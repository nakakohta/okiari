import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.auth import CurrentUser
from app.main import app
from app.routers.live_collaboration import (
    Connection,
    LiveCollaborationManager,
    LiveValue,
    _canonical_value,
    _issue_ticket,
    _verify_ticket,
    manager,
)


def user(role: str = "admin") -> CurrentUser:
    return CurrentUser(
        auth_user_id="00000000-0000-0000-0000-000000000001",
        profile={"is_active": True},
        role={"code": role},
    )


class TicketTests(unittest.TestCase):
    def test_ticket_is_limited_to_its_board(self) -> None:
        ticket = _issue_ticket(user().auth_user_id, "drink-refill")
        self.assertEqual(_verify_ticket(ticket, "drink-refill"), user().auth_user_id)
        with self.assertRaises(HTTPException):
            _verify_ticket(ticket, "inventory")

    def test_modified_ticket_is_rejected(self) -> None:
        ticket = _issue_ticket(user().auth_user_id, "drink-refill")
        with self.assertRaises(HTTPException):
            _verify_ticket(f"x{ticket}", "drink-refill")

    def test_ticket_expires_at_sixty_seconds(self) -> None:
        with patch("app.routers.live_collaboration.time.time", return_value=100):
            ticket = _issue_ticket(user().auth_user_id, "drink-refill")
        with (
            patch("app.routers.live_collaboration.time.time", return_value=160),
            self.assertRaises(HTTPException),
        ):
            _verify_ticket(ticket, "drink-refill")

    def test_websocket_rejects_invalid_ticket_without_exposing_it_in_url(self) -> None:
        with TestClient(app).websocket_connect("/ws/boards/drink-refill") as websocket:
            websocket.send_json({"type": "authenticate", "ticket": "redacted.invalid"})
            with self.assertRaises(WebSocketDisconnect) as raised:
                websocket.receive_json()
        self.assertEqual(raised.exception.code, 4403)

    def test_websocket_accepts_a_valid_board_ticket(self) -> None:
        async def send_initial_sync(_board: str, connection: Connection) -> None:
            await connection.websocket.send_json({"type": "sync", "values": []})

        ticket = _issue_ticket(user().auth_user_id, "drink-refill")
        with (
            patch("app.routers.live_collaboration._current_user", return_value=user()),
            patch.object(manager, "connect", side_effect=send_initial_sync),
            patch.object(manager, "disconnect"),
            TestClient(app).websocket_connect("/ws/boards/drink-refill") as websocket,
        ):
            websocket.send_json({"type": "authenticate", "ticket": ticket})
            self.assertEqual(websocket.receive_json(), {"type": "sync", "values": []})


class LiveValueValidationTests(unittest.TestCase):
    def test_empty_numeric_input_normalizes_to_zero(self) -> None:
        self.assertEqual(_canonical_value("actual_quantity", ""), 0)

    def test_negative_numeric_input_is_rejected(self) -> None:
        with self.assertRaises(HTTPException):
            _canonical_value("requested_quantity", -1)

    def test_text_limit_is_enforced(self) -> None:
        with self.assertRaises(HTTPException):
            _canonical_value("note", "x" * 10_001)


class RevisionOrderingTests(unittest.IsolatedAsyncioTestCase):
    async def test_scoped_clear_keeps_unrelated_live_fields(self) -> None:
        manager = LiveCollaborationManager()
        name = LiveValue(1, "d-rows", 10, "item_name", "Cola", 1, user().auth_user_id)
        requested = LiveValue(1, "d-rows", 10, "requested_quantity", 4, 2, user().auth_user_id)
        manager._values[name.key] = name
        manager._values[requested.key] = requested
        manager._load_board = AsyncMock(return_value=1)
        manager._broadcast = AsyncMock()

        await manager.reset_fields(
            "drink-refill",
            {("d-rows", 10, "requested_quantity")},
            [{"resource": "d-rows", "recordId": 10, "field": "requested_quantity"}],
        )

        self.assertIn(name.key, manager._values)
        self.assertNotIn(requested.key, manager._values)
        manager._broadcast.assert_awaited_once()

    async def test_live_persistence_confirms_the_durable_revision(self) -> None:
        manager = LiveCollaborationManager()
        live = LiveValue(1, "d-rows", 10, "item_name", "Cola", 8, user().auth_user_id)
        manager._values[live.key] = live
        manager._board_keys[1] = "drink-refill"
        manager._broadcast = AsyncMock()
        query = MagicMock()
        query.upsert.return_value.execute.return_value = SimpleNamespace(data=[])
        fake_supabase = MagicMock()
        fake_supabase.table.return_value = query

        with (
            patch("app.routers.live_collaboration.supabase", fake_supabase),
            patch("app.routers.live_collaboration.LIVE_PERSIST_DELAY_SECONDS", 0),
        ):
            await manager._persist_live(live.key)

        persisted = manager._broadcast.await_args.args[1]
        self.assertEqual(persisted["type"], "field_persisted")
        self.assertEqual(persisted["revision"], 8)

    async def test_durable_board_revision_sets_restart_floor(self) -> None:
        manager = LiveCollaborationManager()
        query = MagicMock()
        query.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])
        fake_supabase = MagicMock()
        fake_supabase.table.return_value = query
        with (
            patch("app.routers.live_collaboration._board", return_value={"id": 1, "revision": 7}),
            patch("app.routers.live_collaboration.supabase", fake_supabase),
        ):
            await manager._load_board("drink-refill")
        self.assertEqual(manager._next_revision[1], 7_000_000_000)

    async def test_latest_server_received_value_gets_highest_revision(self) -> None:
        manager = LiveCollaborationManager()
        manager._next_revision[1] = 0
        manager._schedule_live_persist = lambda _: None
        manager._schedule_canonical = lambda _board, _live: None
        manager._broadcast = AsyncMock()
        connection = Connection(websocket=AsyncMock(), user=user())

        with patch(
            "app.routers.live_collaboration._resolve_edit",
            return_value=({"id": 1}, {"id": 10, "board_id": 1}, 10, "a"),
        ):
            await manager.edit("drink-refill", connection, {
                "type": "field_edit",
                "board": "drink-refill",
                "resource": "d-rows",
                "recordId": 10,
                "field": "item_name",
                "value": "a",
                "clientId": "client-a",
                "clientSeq": 1,
            })
            await manager.edit("drink-refill", connection, {
                "type": "field_edit",
                "board": "drink-refill",
                "resource": "d-rows",
                "recordId": 10,
                "field": "item_name",
                "value": "ab",
                "clientId": "client-a",
                "clientSeq": 2,
            })

        calls = manager._broadcast.await_args_list
        self.assertEqual(calls[0].args[1]["revision"], 1)
        self.assertEqual(calls[1].args[1]["revision"], 2)
        self.assertEqual(calls[1].args[1]["value"], "ab")

    async def test_five_concurrent_editors_converge_to_the_last_server_revision(self) -> None:
        manager = LiveCollaborationManager()
        manager._next_revision[1] = 0
        manager._schedule_live_persist = lambda _: None
        manager._schedule_canonical = lambda _board, _live: None
        manager._broadcast = AsyncMock()
        connection = Connection(websocket=AsyncMock(), user=user())

        with patch(
            "app.routers.live_collaboration._resolve_edit",
            return_value=({"id": 1}, {"id": 10, "board_id": 1}, 10, "ignored"),
        ):
            await asyncio.gather(*(
                manager.edit("drink-refill", connection, {
                    "type": "field_edit",
                    "board": "drink-refill",
                    "resource": "d-rows",
                    "recordId": 10,
                    "field": "item_name",
                    "value": value,
                    "clientId": f"client-{index}",
                    "clientSeq": 1,
                })
                for index, value in enumerate(["a", "ab", "abc", "abcd", "abcde"])
            ))

        calls = manager._broadcast.await_args_list
        self.assertEqual([call.args[1]["revision"] for call in calls], [1, 2, 3, 4, 5])
        self.assertEqual(calls[-1].args[1]["value"], "abcde")

    async def test_twenty_client_broadcast_fanout_is_concurrent(self) -> None:
        active = 0
        maximum_active = 0

        class SlowWebSocket:
            async def send_json(self, _message: dict) -> None:
                nonlocal active, maximum_active
                active += 1
                maximum_active = max(maximum_active, active)
                await asyncio.sleep(0)
                active -= 1

        manager = LiveCollaborationManager()
        manager._connections["drink-refill"] = {
            Connection(websocket=SlowWebSocket(), user=user()) for _ in range(20)
        }
        await manager._broadcast("drink-refill", {"type": "field_changed"})
        self.assertEqual(maximum_active, 20)


if __name__ == "__main__":
    unittest.main()
