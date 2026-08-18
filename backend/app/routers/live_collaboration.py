from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass, field as dataclass_field
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.auth import AuthenticatedUser, CurrentUser
from app.core.db import get_user_profile
from app.core.errors import bad_request, forbidden, not_found
from app.routers.collaborative import (
    POSTGRES_INTEGER_MAX,
    RESOURCE_TABLES,
    ResourcePayload,
    _board,
    _require_write,
    _resource,
    _row,
    _validate_values,
    create_resource,
    update_resource,
)
from app.supabase_client import supabase

router = APIRouter(tags=["live collaboration"])
logger = logging.getLogger(__name__)

TICKET_TTL_SECONDS = 60
AUTH_RECHECK_SECONDS = 60
LIVE_PERSIST_DELAY_SECONDS = 0.05
CANONICAL_DELAY_SECONDS = 0.25
CANONICAL_MAX_WAIT_SECONDS = 1.0
# Locks/confirmation changes invalidate this cache immediately. A short cache
# keeps permission lookups out of the character hot path while still detecting
# out-of-band store-assignment changes well inside the 60-second recheck window.
AUTHORIZATION_CACHE_SECONDS = 10.0
# Keep live revisions above the durable board revision so a FastAPI restart after
# clear/restore cannot make newly accepted events look older to connected clients.
REVISION_EPOCH_SIZE = 1_000_000_000
_ticket_secret = secrets.token_bytes(32)

LIVE_FIELDS: dict[str, set[str]] = {
    "d-rows": {"item_name", "max_quantity", "requested_quantity", "note"},
    "md-rows": {"custom_booth"},
    "md-columns": {"title"},
    "md-cells": {"value"},
    "mf-rows": {"icon", "item_name", "subtext", "note"},
    "mf-containers": {"name", "quantity"},
    "m-rows": {"expected_quantity", "actual_quantity", "note"},
}
NUMERIC_FIELDS = {"max_quantity", "requested_quantity", "quantity", "expected_quantity", "actual_quantity"}
MAX_FIELD_LENGTH = 10_000


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _issue_ticket(user_id: str, board: str) -> str:
    payload = _b64encode(json.dumps({
        "sub": user_id,
        "board": board,
        "exp": int(time.time()) + TICKET_TTL_SECONDS,
        "nonce": secrets.token_urlsafe(12),
    }, separators=(",", ":")).encode())
    signature = _b64encode(hmac.new(_ticket_secret, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def _verify_ticket(ticket: str, board: str) -> str:
    try:
        payload_part, signature_part = ticket.split(".", 1)
        expected = hmac.new(_ticket_secret, payload_part.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature_part)):
            raise ValueError
        payload = json.loads(_b64decode(payload_part))
        if payload.get("board") != board or int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError
        return str(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise forbidden("Invalid or expired collaboration ticket") from exc


def _current_user(user_id: str) -> CurrentUser:
    profile = get_user_profile(user_id)
    if not profile or profile.get("is_active") is False:
        raise forbidden("Inactive or unregistered user")
    role = profile.get("role") or {}
    if not role.get("code"):
        raise forbidden("User role is not configured")
    return CurrentUser(auth_user_id=user_id, profile=profile, role=role)


def _canonical_value(field: str, value: Any) -> Any:
    if field not in NUMERIC_FIELDS:
        if not isinstance(value, str):
            raise bad_request(f"{field} must be text")
        if len(value) > MAX_FIELD_LENGTH:
            raise bad_request("Input is too long")
        return value
    if value == "" or value is None:
        return 0
    if isinstance(value, bool):
        raise bad_request(f"{field} must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise bad_request(f"{field} must be an integer") from exc
    if str(value).strip() not in {str(number), f"+{number}"} and not isinstance(value, int):
        raise bad_request(f"{field} must be an integer")
    if not 0 <= number <= POSTGRES_INTEGER_MAX:
        raise bad_request(f"{field} must be between 0 and {POSTGRES_INTEGER_MAX}")
    return number


def _resolve_edit(
    board_key: str,
    user: CurrentUser,
    resource: str,
    record_id: int,
    field: str,
    value: Any,
    relations: dict[str, Any],
) -> tuple[dict, dict, int, Any]:
    table, _ = _resource(resource, board_key)
    if field not in LIVE_FIELDS.get(resource, set()):
        raise bad_request("This field does not support live editing")
    canonical = _canonical_value(field, value)
    board = _board(board_key)

    if resource == "md-cells" and record_id <= 0:
        row_id = relations.get("row_id")
        column_id = relations.get("column_id")
        if (
            not isinstance(row_id, int) or isinstance(row_id, bool)
            or not isinstance(column_id, int) or isinstance(column_id, bool)
        ):
            raise bad_request("Meal drink cell coordinates are required")
        response = (
            supabase.table("mdtable_cells").select("*")
            .eq("board_id", board["id"]).eq("row_id", row_id).eq("column_id", column_id)
            .maybe_single().execute()
        )
        existing = getattr(response, "data", None)
        if not existing:
            try:
                existing = create_resource(
                    board_key,
                    resource,
                    ResourcePayload(values={"row_id": row_id, "column_id": column_id, "value": canonical}),
                    user,
                )
            except Exception:
                response = (
                    supabase.table("mdtable_cells").select("*")
                    .eq("board_id", board["id"]).eq("row_id", row_id).eq("column_id", column_id)
                    .maybe_single().execute()
                )
                existing = getattr(response, "data", None)
                if not existing:
                    raise
        record_id = int(existing["id"])
    else:
        existing = _row(table, record_id)

    if int(existing["board_id"]) != int(board["id"]) or existing.get("deleted_at"):
        raise not_found("Row not found")
    values = _validate_values(resource, {field: canonical}, create=False)
    _require_write(user, resource, values, existing)
    return board, existing, record_id, canonical


@dataclass
class LiveValue:
    board_id: int
    resource: str
    record_id: int
    field: str
    value: Any
    revision: int
    updated_by: str

    @property
    def key(self) -> tuple[int, str, int, str]:
        return (self.board_id, self.resource, self.record_id, self.field)

    def message(self, *, client_id: str | None = None, client_seq: int | None = None) -> dict[str, Any]:
        return {
            "type": "field_changed",
            "resource": self.resource,
            "recordId": self.record_id,
            "field": self.field,
            "value": self.value,
            "revision": self.revision,
            "actorId": self.updated_by,
            "clientId": client_id,
            "clientSeq": client_seq,
        }


@dataclass(eq=False)
class Connection:
    websocket: WebSocket
    user: CurrentUser
    send_lock: asyncio.Lock = dataclass_field(default_factory=asyncio.Lock)


class LiveCollaborationManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[Connection]] = {}
        self._values: dict[tuple[int, str, int, str], LiveValue] = {}
        self._board_ids: dict[str, int] = {}
        self._board_keys: dict[int, str] = {}
        self._next_revision: dict[int, int] = {}
        self._loaded_boards: set[int] = set()
        self._receive_locks: dict[tuple[Any, ...], asyncio.Lock] = {}
        self._live_tasks: dict[tuple[int, str, int, str], asyncio.Task[None]] = {}
        self._canonical_tasks: dict[tuple[int, str, int, str], asyncio.Task[None]] = {}
        self._canonical_started: dict[tuple[int, str, int, str], float] = {}
        self._canonical_due: dict[tuple[int, str, int, str], float] = {}
        self._authorization_cache: dict[tuple[Any, ...], tuple[float, int, int]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    async def _load_board(self, board_key: str) -> int:
        if board_key in self._board_ids:
            return self._board_ids[board_key]
        board = await asyncio.to_thread(_board, board_key)
        board_id = int(board["id"])
        self._board_ids[board_key] = board_id
        self._board_keys[board_id] = board_key
        if board_id in self._loaded_boards:
            return board_id
        response = await asyncio.to_thread(
            lambda: supabase.table("board_live_fields").select("*").eq("board_id", board_id).execute()
        )
        maximum = 0
        loaded: list[LiveValue] = []
        for item in getattr(response, "data", None) or []:
            live = LiveValue(
                board_id=board_id,
                resource=item["resource"],
                record_id=int(item["record_id"]),
                field=item["field"],
                value=item["value"],
                revision=int(item["revision"]),
                updated_by=str(item["updated_by"]),
            )
            self._values[live.key] = live
            loaded.append(live)
            maximum = max(maximum, live.revision)
        durable_floor = int(board.get("revision") or 0) * REVISION_EPOCH_SIZE
        self._next_revision[board_id] = max(maximum, durable_floor)
        self._loaded_boards.add(board_id)
        for live in loaded:
            self._schedule_canonical(board_key, live)
        return board_id

    async def connect(self, board_key: str, connection: Connection) -> None:
        self._loop = asyncio.get_running_loop()
        board_id = await self._load_board(board_key)
        self._connections.setdefault(board_key, set()).add(connection)
        values = [item.message() for item in self._values.values() if item.board_id == board_id]
        await connection.websocket.send_json({"type": "sync", "values": values})

    def disconnect(self, board_key: str, connection: Connection) -> None:
        connections = self._connections.get(board_key)
        if connections:
            connections.discard(connection)
            if not connections:
                self._connections.pop(board_key, None)

    async def _broadcast(self, board_key: str, message: dict[str, Any]) -> None:
        connections = list(self._connections.get(board_key, set()))
        if not connections:
            return

        async def send(connection: Connection) -> Connection | None:
            try:
                async with connection.send_lock:
                    await asyncio.wait_for(connection.websocket.send_json(message), timeout=1.0)
                return None
            except Exception:
                return connection

        for stale in await asyncio.gather(*(send(connection) for connection in connections)):
            if stale:
                self.disconnect(board_key, stale)

    def _schedule_live_persist(self, live: LiveValue) -> None:
        current = self._live_tasks.get(live.key)
        if current and not current.done():
            return
        self._live_tasks[live.key] = asyncio.create_task(self._persist_live(live.key))

    async def _persist_live(self, key: tuple[int, str, int, str]) -> None:
        await asyncio.sleep(LIVE_PERSIST_DELAY_SECONDS)
        retry = 0
        while True:
            live = self._values.get(key)
            if not live:
                return
            revision = live.revision
            payload = {
                "board_id": live.board_id,
                "resource": live.resource,
                "record_id": live.record_id,
                "field": live.field,
                "value": live.value,
                "revision": revision,
                "updated_by": live.updated_by,
                "updated_at": datetime.now(UTC).isoformat(),
            }
            try:
                await asyncio.to_thread(
                    lambda: supabase.table("board_live_fields").upsert(
                        payload, on_conflict="board_id,resource,record_id,field"
                    ).execute()
                )
                board_key = self._board_keys.get(live.board_id)
                if board_key:
                    await self._broadcast(board_key, {
                        "type": "field_persisted",
                        "resource": live.resource,
                        "recordId": live.record_id,
                        "field": live.field,
                        "revision": revision,
                    })
                retry = 0
                current = self._values.get(key)
                if current and current.revision == revision:
                    return
                await asyncio.sleep(LIVE_PERSIST_DELAY_SECONDS)
            except Exception:
                retry += 1
                if retry == 1 or retry & (retry - 1) == 0:
                    logger.exception(
                        "Live-field persistence failed; retrying board_id=%s resource=%s record_id=%s field=%s retry=%s",
                        key[0], key[1], key[2], key[3], retry,
                    )
                await asyncio.sleep(min(8.0, 2 ** min(retry, 3)))

    def _schedule_canonical(self, board_key: str, live: LiveValue) -> None:
        now = time.monotonic()
        started = self._canonical_started.setdefault(live.key, now)
        due = min(now + CANONICAL_DELAY_SECONDS, started + CANONICAL_MAX_WAIT_SECONDS)
        self._canonical_due[live.key] = due
        current = self._canonical_tasks.get(live.key)
        if current and not current.done():
            return
        self._canonical_tasks[live.key] = asyncio.create_task(self._persist_canonical(board_key, live.key))

    async def _persist_canonical(self, board_key: str, key: tuple[int, str, int, str]) -> None:
        retry = 0
        while True:
            due = self._canonical_due.get(key)
            if due is None:
                return
            await asyncio.sleep(max(0.0, due - time.monotonic()))
            if self._canonical_due.get(key, 0) > time.monotonic():
                continue
            live = self._values.get(key)
            if not live:
                return
            source_revision = live.revision
            try:
                canonical = _canonical_value(live.field, live.value)
                if canonical != live.value:
                    self._next_revision[live.board_id] += 1
                    live = LiveValue(
                        board_id=live.board_id,
                        resource=live.resource,
                        record_id=live.record_id,
                        field=live.field,
                        value=canonical,
                        revision=self._next_revision[live.board_id],
                        updated_by=live.updated_by,
                    )
                    self._values[key] = live
                    self._schedule_live_persist(live)
                    await self._broadcast(board_key, live.message())
                    source_revision = live.revision
                user = await asyncio.to_thread(_current_user, live.updated_by)
                await asyncio.to_thread(
                    update_resource,
                    board_key,
                    live.resource,
                    live.record_id,
                    ResourcePayload(values={live.field: canonical}),
                    user,
                )
                if self._values.get(key) and self._values[key].revision == source_revision:
                    self._canonical_started.pop(key, None)
                    self._canonical_due.pop(key, None)
                    self._canonical_tasks.pop(key, None)
                    return
                else:
                    self._canonical_started[key] = time.monotonic()
                    self._canonical_due[key] = time.monotonic() + CANONICAL_DELAY_SECONDS
                    retry = 0
                    continue
            except Exception:
                retry += 1
                if retry == 1 or retry & (retry - 1) == 0:
                    logger.exception(
                        "Canonical-field persistence failed; retrying board=%s resource=%s record_id=%s field=%s retry=%s",
                        board_key, key[1], key[2], key[3], retry,
                    )
                await asyncio.sleep(min(8.0, 2 ** min(retry, 3)))

    async def edit(self, board_key: str, connection: Connection, message: dict[str, Any]) -> None:
        if message.get("board") != board_key:
            raise bad_request("Live edit board does not match the connection")
        resource = message.get("resource")
        field = message.get("field")
        record_id = message.get("recordId")
        client_id = message.get("clientId")
        client_seq = message.get("clientSeq")
        if (
            not isinstance(resource, str)
            or not isinstance(field, str)
            or not isinstance(record_id, int)
            or isinstance(record_id, bool)
        ):
            raise bad_request("Invalid live edit message")
        if (
            not isinstance(client_id, str)
            or len(client_id) > 100
            or not isinstance(client_seq, int)
            or isinstance(client_seq, bool)
            or not 1 <= client_seq <= POSTGRES_INTEGER_MAX
        ):
            raise bad_request("Invalid client sequence")
        relations = message.get("relations") if isinstance(message.get("relations"), dict) else {}
        _canonical_value(field, message.get("value"))
        logical_record = (
            (relations.get("row_id"), relations.get("column_id"))
            if resource == "md-cells" and relations.get("row_id") and relations.get("column_id")
            else record_id
        )
        receive_key = (board_key, resource, logical_record, field)
        receive_lock = self._receive_locks.setdefault(receive_key, asyncio.Lock())
        async with receive_lock:
            cache_key = (
                connection.user.auth_user_id,
                board_key,
                resource,
                record_id,
                field,
                relations.get("row_id"),
                relations.get("column_id"),
            )
            cached = self._authorization_cache.get(cache_key)
            if cached and cached[0] > time.monotonic():
                board_id, record_id = cached[1], cached[2]
            else:
                board, _, record_id, _ = await asyncio.to_thread(
                    _resolve_edit,
                    board_key,
                    connection.user,
                    resource,
                    record_id,
                    field,
                    message.get("value"),
                    relations,
                )
                board_id = int(board["id"])
                self._authorization_cache[cache_key] = (
                    time.monotonic() + AUTHORIZATION_CACHE_SECONDS,
                    board_id,
                    record_id,
                )
            key = (board_id, resource, record_id, field)
            self._next_revision[board_id] = self._next_revision.get(board_id, 0) + 1
            live = LiveValue(
                board_id=board_id,
                resource=resource,
                record_id=record_id,
                field=field,
                value=message.get("value"),
                revision=self._next_revision[board_id],
                updated_by=connection.user.auth_user_id,
            )
            self._values[key] = live
            self._schedule_live_persist(live)
            self._schedule_canonical(board_key, live)
            event = live.message(client_id=client_id, client_seq=client_seq)
            if relations:
                event["relations"] = relations
            await self._broadcast(board_key, event)

    async def correction(self, board_key: str, message: dict[str, Any]) -> dict[str, Any] | None:
        resource = message.get("resource")
        field = message.get("field")
        record_id = message.get("recordId")
        if (
            not isinstance(resource, str)
            or field not in LIVE_FIELDS.get(resource, set())
            or not isinstance(record_id, int)
            or isinstance(record_id, bool)
        ):
            return None
        board_id = await self._load_board(board_key)
        relations = message.get("relations") if isinstance(message.get("relations"), dict) else {}
        if resource == "md-cells" and record_id <= 0:
            row_id = relations.get("row_id")
            column_id = relations.get("column_id")
            if (
                not isinstance(row_id, int) or isinstance(row_id, bool)
                or not isinstance(column_id, int) or isinstance(column_id, bool)
            ):
                return None
            response = await asyncio.to_thread(
                lambda: supabase.table("mdtable_cells").select("id")
                .eq("board_id", board_id).eq("row_id", row_id).eq("column_id", column_id)
                .maybe_single().execute()
            )
            cell = getattr(response, "data", None)
            if not cell:
                return None
            record_id = int(cell["id"])
        key = (board_id, resource, record_id, field)
        live = self._values.get(key)
        if live:
            correction = live.message()
        else:
            table = RESOURCE_TABLES[resource]
            existing = await asyncio.to_thread(_row, table, record_id)
            if int(existing["board_id"]) != board_id or existing.get("deleted_at"):
                return None
            correction = {
                "type": "field_changed",
                "resource": resource,
                "recordId": record_id,
                "field": field,
                "value": existing.get(field),
                "revision": self._next_revision.get(board_id, 0),
            }
        if relations:
            correction["relations"] = relations
        return correction

    async def reset_board(self, board_key: str, event_type: str = "board_reset") -> None:
        board_id = await self._load_board(board_key)
        for key in [key for key in self._values if key[0] == board_id]:
            self._values.pop(key, None)
            live_task = self._live_tasks.pop(key, None)
            if live_task:
                live_task.cancel()
            task = self._canonical_tasks.pop(key, None)
            if task:
                task.cancel()
            self._canonical_started.pop(key, None)
            self._canonical_due.pop(key, None)
        await self._broadcast(board_key, {"type": event_type})

    async def remove_resources(
        self,
        board_key: str,
        targets: set[tuple[str, int]],
        resource: str,
        record_id: int,
        event_type: str = "structure_changed",
        message_targets: list[dict[str, Any]] | None = None,
    ) -> None:
        board_id = await self._load_board(board_key)
        for key in [
            key for key in self._values
            if key[0] == board_id and (key[1], key[2]) in targets
        ]:
            self._values.pop(key, None)
            live_task = self._live_tasks.pop(key, None)
            if live_task:
                live_task.cancel()
            task = self._canonical_tasks.pop(key, None)
            if task:
                task.cancel()
            self._canonical_started.pop(key, None)
            self._canonical_due.pop(key, None)
        await self._broadcast(board_key, {
            "type": event_type,
            "resource": resource,
            "recordId": record_id,
            "targets": message_targets or [
                {"resource": target_resource, "recordId": target_id}
                for target_resource, target_id in sorted(targets)
            ],
        })

    def notify_reset(self, board_key: str, event_type: str = "board_reset") -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.reset_board(board_key, event_type))
            )

    def notify_resources_deleted(
        self,
        board_key: str,
        targets: set[tuple[str, int]],
        resource: str,
        record_id: int,
    ) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(
                    self.remove_resources(board_key, targets, resource, record_id)
                )
            )

    async def reset_fields(
        self,
        board_key: str,
        targets: set[tuple[str, int, str]],
        message_targets: list[dict[str, Any]],
    ) -> None:
        board_id = await self._load_board(board_key)
        for key in [
            key for key in self._values
            if key[0] == board_id and (key[1], key[2], key[3]) in targets
        ]:
            self._values.pop(key, None)
            live_task = self._live_tasks.pop(key, None)
            if live_task:
                live_task.cancel()
            canonical_task = self._canonical_tasks.pop(key, None)
            if canonical_task:
                canonical_task.cancel()
            self._canonical_started.pop(key, None)
            self._canonical_due.pop(key, None)
        await self._broadcast(board_key, {
            "type": "fields_reset",
            "targets": message_targets,
        })

    def notify_fields_reset(
        self,
        board_key: str,
        targets: set[tuple[str, int, str]],
        message_targets: list[dict[str, Any]],
    ) -> None:
        if not targets or not self._loop or not self._loop.is_running():
            return
        self._loop.call_soon_threadsafe(
            lambda: asyncio.create_task(
                self.reset_fields(board_key, targets, message_targets)
            )
        )

    def invalidate_authorization(self, user_id: str | None = None) -> None:
        if user_id is None:
            self._authorization_cache.clear()
            return
        for key in [key for key in self._authorization_cache if key[0] == user_id]:
            self._authorization_cache.pop(key, None)


manager = LiveCollaborationManager()


def clear_live_fields(board_key: str) -> None:
    board = _board(board_key)
    supabase.table("board_live_fields").delete().eq("board_id", board["id"]).execute()
    manager.invalidate_authorization()
    manager.notify_reset(board_key)


def _delete_target_live_fields(board_id: int, targets: set[tuple[str, int]]) -> None:
    for target_resource in {item[0] for item in targets}:
        ids = [item[1] for item in targets if item[0] == target_resource]
        (
            supabase.table("board_live_fields").delete()
            .eq("board_id", board_id).eq("resource", target_resource).in_("record_id", ids).execute()
        )


def _delete_target_live_field_values(
    board_id: int,
    targets: set[tuple[str, int, str]],
) -> None:
    for target_resource, target_field in {(item[0], item[2]) for item in targets}:
        ids = [
            item[1] for item in targets
            if item[0] == target_resource and item[2] == target_field
        ]
        (
            supabase.table("board_live_fields").delete()
            .eq("board_id", board_id).eq("resource", target_resource)
            .eq("field", target_field).in_("record_id", ids).execute()
        )


def clear_action_live_fields(board_key: str, values: dict[str, Any]) -> None:
    board = _board(board_key)
    board_id = int(board["id"])
    targets: set[tuple[str, int, str]] = set()
    message_targets: list[dict[str, Any]] = []
    if board_key == "drink-refill":
        response = (
            supabase.table("dtable_rows").select("id")
            .eq("board_id", board_id).eq("store_id", values["store_id"])
            .eq("scope", values["scope"]).is_("deleted_at", "null").execute()
        )
        for item in getattr(response, "data", None) or []:
            targets.add(("d-rows", int(item["id"]), "requested_quantity"))
            targets.add(("d-rows", int(item["id"]), "note"))
    elif board_key == "meal-drink":
        rows = (
            supabase.table("mdtable_rows").select("id")
            .eq("board_id", board_id).eq("floor_group", values["floor_group"])
            .is_("deleted_at", "null").execute()
        )
        row_ids = [int(item["id"]) for item in (getattr(rows, "data", None) or [])]
        if row_ids:
            cells = (
                supabase.table("mdtable_cells").select("id,row_id,column_id")
                .eq("board_id", board_id).in_("row_id", row_ids).execute()
            )
            cell_rows = getattr(cells, "data", None) or []
            targets.update(("md-cells", int(item["id"]), "value") for item in cell_rows)
            message_targets.extend({
                "resource": "md-cells",
                "recordId": int(item["id"]),
                "field": "value",
                "relations": {"row_id": int(item["row_id"]), "column_id": int(item["column_id"])},
            } for item in cell_rows)
    elif board_key == "meal-food":
        rows = (
            supabase.table("mftable_rows").select("id")
            .eq("board_id", board_id).is_("deleted_at", "null").execute()
        )
        row_ids = [int(item["id"]) for item in (getattr(rows, "data", None) or [])]
        targets.update(("mf-rows", row_id, "note") for row_id in row_ids)
        if row_ids:
            containers = (
                supabase.table("mftable_containers").select("id")
                .eq("board_id", board_id).in_("row_id", row_ids).is_("deleted_at", "null").execute()
            )
            targets.update(
                ("mf-containers", int(item["id"]), "quantity")
                for item in (getattr(containers, "data", None) or [])
            )
    elif board_key == "inventory":
        rows = (
            supabase.table("mtable_rows").select("id")
            .eq("board_id", board_id).is_("deleted_at", "null").execute()
        )
        for item in getattr(rows, "data", None) or []:
            targets.add(("m-rows", int(item["id"]), "actual_quantity"))
            targets.add(("m-rows", int(item["id"]), "note"))

    _delete_target_live_field_values(board_id, targets)
    manager.invalidate_authorization()
    if not message_targets:
        message_targets = [
            {"resource": target_resource, "recordId": target_id, "field": target_field}
            for target_resource, target_id, target_field in sorted(targets)
        ]
    manager.notify_fields_reset(board_key, targets, message_targets)


def delete_live_fields(board_key: str, resource: str, record_id: int) -> None:
    board = _board(board_key)
    targets: set[tuple[str, int]] = {(resource, record_id)}

    if resource in {"md-rows", "md-columns"}:
        foreign_key = "row_id" if resource == "md-rows" else "column_id"
        response = (
            supabase.table("mdtable_cells").select("id")
            .eq("board_id", board["id"]).eq(foreign_key, record_id).execute()
        )
        targets.update(("md-cells", int(item["id"])) for item in (getattr(response, "data", None) or []))
    elif resource in {"mf-sections", "mf-rows"}:
        if resource == "mf-sections":
            response = (
                supabase.table("mftable_rows").select("id")
                .eq("board_id", board["id"]).eq("section_id", record_id).execute()
            )
            row_ids = [int(item["id"]) for item in (getattr(response, "data", None) or [])]
            targets.update(("mf-rows", row_id) for row_id in row_ids)
        else:
            row_ids = [record_id]
        if row_ids:
            response = (
                supabase.table("mftable_containers").select("id")
                .eq("board_id", board["id"]).in_("row_id", row_ids).execute()
            )
            targets.update(
                ("mf-containers", int(item["id"]))
                for item in (getattr(response, "data", None) or [])
            )

    _delete_target_live_fields(int(board["id"]), targets)
    manager.invalidate_authorization()
    manager.notify_resources_deleted(board_key, targets, resource, record_id)


@router.post("/boards/{board_key}/collaboration-ticket")
def collaboration_ticket(board_key: str, current_user: AuthenticatedUser) -> dict[str, Any]:
    _board(board_key)
    return {
        "ticket": _issue_ticket(current_user.auth_user_id, board_key),
        "expires_in": TICKET_TTL_SECONDS,
    }


@router.websocket("/ws/boards/{board_key}")
async def collaboration_websocket(websocket: WebSocket, board_key: str) -> None:
    await websocket.accept()
    connection: Connection | None = None
    receive_task: asyncio.Task[dict[str, Any]] | None = None
    try:
        first = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        if first.get("type") != "authenticate" or not isinstance(first.get("ticket"), str):
            await websocket.close(code=4401)
            return
        user_id = _verify_ticket(first["ticket"], board_key)
        user = await asyncio.to_thread(_current_user, user_id)
        connection = Connection(websocket=websocket, user=user)
        await manager.connect(board_key, connection)

        receive_task = asyncio.create_task(websocket.receive_json())
        while True:
            done, _ = await asyncio.wait({receive_task}, timeout=AUTH_RECHECK_SECONDS)
            if not done:
                connection.user = await asyncio.to_thread(_current_user, user_id)
                manager.invalidate_authorization(user_id)
                continue
            message = receive_task.result()
            receive_task = asyncio.create_task(websocket.receive_json())
            if message.get("type") != "field_edit":
                continue
            try:
                await manager.edit(board_key, connection, message)
            except HTTPException as exc:
                try:
                    current = await manager.correction(board_key, message)
                except Exception:
                    logger.exception("Failed to prepare live-field correction board=%s", board_key)
                    current = None
                await websocket.send_json({
                    "type": "field_error",
                    "resource": message.get("resource"),
                    "recordId": message.get("recordId"),
                    "field": message.get("field"),
                    "relations": message.get("relations"),
                    "clientId": message.get("clientId"),
                    "clientSeq": message.get("clientSeq"),
                    "current": current,
                    "detail": exc.detail,
                })
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except HTTPException:
        await websocket.close(code=4403)
    except Exception:
        logger.exception("Unexpected collaboration WebSocket failure board=%s", board_key)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        if receive_task:
            receive_task.cancel()
        if connection:
            manager.disconnect(board_key, connection)
