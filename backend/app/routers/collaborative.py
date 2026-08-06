from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.auth import AuthenticatedUser, BusinessEditorUser
from app.core.db import response_single
from app.core.errors import bad_request, forbidden, not_found
from app.supabase_client import supabase

router = APIRouter(prefix="/boards", tags=["collaborative boards"])

BOARD_TABLES: dict[str, tuple[str, ...]] = {
    "drink-refill": ("dtable_rows", "dtable_locks"),
    "meal-drink": ("mdtable_rows", "mdtable_columns", "mdtable_cells", "mdtable_locks"),
    "meal-food": ("mftable_sections", "mftable_rows", "mftable_containers"),
    "inventory": ("mtable_rows",),
}

RESOURCE_TABLES = {
    "d-rows": "dtable_rows",
    "md-rows": "mdtable_rows",
    "md-columns": "mdtable_columns",
    "md-cells": "mdtable_cells",
    "mf-sections": "mftable_sections",
    "mf-rows": "mftable_rows",
    "mf-containers": "mftable_containers",
    "m-rows": "mtable_rows",
}

RESOURCE_BOARDS = {
    "d-rows": "drink-refill",
    "md-rows": "meal-drink",
    "md-columns": "meal-drink",
    "md-cells": "meal-drink",
    "mf-sections": "meal-food",
    "mf-rows": "meal-food",
    "mf-containers": "meal-food",
    "m-rows": "inventory",
}

WRITE_FIELDS: dict[str, set[str]] = {
    "d-rows": {"store_id", "scope", "item_name", "max_quantity", "requested_quantity", "note", "status", "sort_order"},
    "md-rows": {"floor_group", "booth_type", "booth", "custom_booth", "sort_order"},
    "md-columns": {"floor_group", "title", "sort_order"},
    "md-cells": {"row_id", "column_id", "value"},
    "mf-sections": {"store_id", "store_name", "sort_order"},
    "mf-rows": {"section_id", "icon", "item_name", "subtext", "note", "sort_order"},
    "mf-containers": {"row_id", "name", "container_type", "quantity", "sort_order"},
    "m-rows": {"store_id", "product_id", "expected_quantity", "actual_quantity", "note", "is_confirmed", "sort_order"},
}

SOFT_DELETE_RESOURCES = {"d-rows", "md-rows", "md-columns", "mf-sections", "mf-rows", "mf-containers", "m-rows"}
IMMUTABLE_FIELDS = {
    "d-rows": {"store_id", "scope"},
    "md-rows": {"floor_group"},
    "md-columns": {"floor_group"},
    "md-cells": {"row_id", "column_id"},
    "mf-sections": set(),
    "mf-rows": {"section_id"},
    "mf-containers": {"row_id"},
    "m-rows": set(),
}


class ResourcePayload(BaseModel):
    values: dict[str, Any]


class ReorderItem(BaseModel):
    id: int
    sort_order: int = Field(ge=0)


class ReorderPayload(BaseModel):
    items: list[ReorderItem]


class LockPayload(BaseModel):
    store_id: int | None = None
    scope: Literal["drink", "consumable"] | None = None
    floor_group: Literal["first", "second", "third"] | None = None
    column_key: str
    is_locked: bool


class ClearPayload(BaseModel):
    store_id: int | None = None
    scope: Literal["drink", "consumable"] | None = None
    floor_group: Literal["first", "second", "third"] | None = None


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _board(key: str) -> dict:
    if key not in BOARD_TABLES:
        raise not_found("Board not found")
    response = supabase.table("shared_boards").select("id,key,revision,updated_at").eq("key", key).maybe_single().execute()
    data = getattr(response, "data", None)
    if not data:
        raise not_found("Board not found")
    return data


def _resource(resource: str, key: str | None = None) -> tuple[str, str]:
    table = RESOURCE_TABLES.get(resource)
    board_key = RESOURCE_BOARDS.get(resource)
    if not table or not board_key or (key is not None and board_key != key):
        raise not_found("Board resource not found")
    return table, board_key


def _row(table: str, row_id: int) -> dict:
    response = supabase.table(table).select("*").eq("id", row_id).maybe_single().execute()
    data = getattr(response, "data", None)
    if not data:
        raise not_found("Row not found")
    return data


def _active_rows(table: str, board_id: int) -> list[dict]:
    query = supabase.table(table).select("*").eq("board_id", board_id)
    if table != "mdtable_cells" and table not in {"dtable_locks", "mdtable_locks"}:
        query = query.is_("deleted_at", "null")
    response = query.order("sort_order" if table not in {"mdtable_cells", "dtable_locks", "mdtable_locks"} else "id").execute()
    return getattr(response, "data", None) or []


def _allowed_store_ids(current_user: AuthenticatedUser) -> list[int] | None:
    if current_user.role_code in {"admin", "leader"}:
        return None
    response = (
        supabase.table("user_store_assignments")
        .select("store_id")
        .eq("user_id", current_user.auth_user_id)
        .eq("can_edit", True)
        .execute()
    )
    return [int(item["store_id"]) for item in (getattr(response, "data", None) or [])]


def _require_store_edit(current_user: AuthenticatedUser, store_id: int | None) -> None:
    if current_user.role_code in {"admin", "leader"}:
        return
    allowed = _allowed_store_ids(current_user)
    if store_id is None or allowed is None or store_id not in allowed:
        raise forbidden("Assigned store edit permission is required")


def _section_store(section_id: int) -> int | None:
    section = _row("mftable_sections", section_id)
    return int(section["store_id"]) if section.get("store_id") is not None else None


def _resource_store(resource: str, values: dict, existing: dict | None = None) -> int | None:
    source = {**(existing or {}), **values}
    if resource in {"d-rows", "mf-sections", "m-rows"}:
        value = source.get("store_id")
        return int(value) if value is not None else None
    if resource == "mf-rows":
        return _section_store(int(source["section_id"]))
    if resource == "mf-containers":
        row = _row("mftable_rows", int(source["row_id"]))
        return _section_store(int(row["section_id"]))
    if resource in {"md-rows", "md-cells"}:
        if resource == "md-cells":
            row = _row("mdtable_rows", int(source["row_id"]))
        else:
            row = source
        booth = "その他" if row.get("booth") == "その他" else row.get("booth")
        store = supabase.table("stores").select("id").eq("name", booth).maybe_single().execute()
        data = getattr(store, "data", None)
        return int(data["id"]) if data else None
    return None


def _validate_values(resource: str, values: dict[str, Any], *, create: bool) -> dict[str, Any]:
    unknown = set(values) - WRITE_FIELDS[resource]
    if unknown:
        raise bad_request(f"Unsupported fields: {', '.join(sorted(unknown))}")
    if not values:
        raise bad_request("No values were supplied")
    if not create and any(key in values for key in IMMUTABLE_FIELDS[resource]):
        raise bad_request("Relationship fields cannot be changed")
    if "status" in values and values["status"] not in {"pending", "out_of_stock", "completed"}:
        raise bad_request("Invalid restock status")
    if "container_type" in values and values["container_type"] not in {"insulated_box", "food_warmer", "register"}:
        raise bad_request("Invalid container type")
    for field in {"max_quantity", "requested_quantity", "quantity", "expected_quantity", "actual_quantity", "sort_order"} & set(values):
        if isinstance(values[field], bool) or not isinstance(values[field], int) or values[field] < 0:
            raise bad_request(f"{field} must be a non-negative integer")
    return values


def _require_write(current_user: AuthenticatedUser, resource: str, values: dict, existing: dict | None = None) -> None:
    if current_user.role_code == "viewer":
        raise forbidden()
    if resource == "md-columns" and current_user.role_code == "sub_leader":
        raise forbidden("Only admin or leader can change table structure")
    _require_store_edit(current_user, _resource_store(resource, values, existing))
    if current_user.role_code == "sub_leader" and existing:
        if resource == "d-rows":
            field_to_column = {"item_name": "name", "max_quantity": "max_quantity", "requested_quantity": "requested_quantity", "note": "note", "status": "status"}
            columns = [field_to_column[field] for field in values if field in field_to_column]
            if columns:
                response = (
                    supabase.table("dtable_locks").select("column_key")
                    .eq("board_id", existing["board_id"]).eq("store_id", existing["store_id"])
                    .eq("scope", existing["scope"]).eq("is_locked", True).in_("column_key", columns).execute()
                )
                if getattr(response, "data", None):
                    raise forbidden("The edited column is locked")
        if resource == "md-rows" and ({"booth", "custom_booth"} & set(values)):
            response = (
                supabase.table("mdtable_locks").select("id")
                .eq("board_id", existing["board_id"]).eq("floor_group", existing["floor_group"])
                .eq("column_key", "booth").eq("is_locked", True).maybe_single().execute()
            )
            if getattr(response, "data", None):
                raise forbidden("The booth column is locked")
        if resource == "m-rows" and existing.get("is_confirmed"):
            raise forbidden("Confirmed inventory rows cannot be edited")
    if resource == "m-rows" and "is_confirmed" in values and values["is_confirmed"] != (existing or {}).get("is_confirmed"):
        if current_user.role_code not in {"admin", "leader"}:
            raise forbidden("Only admin or leader can confirm inventory")


def _snapshot(board: dict, user_id: str, reason: str) -> dict:
    state = {table: _active_rows(table, int(board["id"])) for table in BOARD_TABLES[board["key"]]}
    return response_single(
        supabase.table("board_snapshots").insert({
            "board_id": board["id"], "revision": board["revision"], "reason": reason, "snapshot": state, "created_by": user_id,
        }).select("*").execute(),
        "Snapshot could not be created",
    )


def _inventory_replace(row: dict, user_id: str) -> None:
    if not row.get("is_confirmed"):
        return
    payload = {"quantity": row["actual_quantity"], "updated_by": user_id, "updated_at": _now()}
    existing = (
        supabase.table("inventories").select("id")
        .eq("store_id", row["store_id"]).eq("product_id", row["product_id"])
        .maybe_single().execute()
    )
    data = getattr(existing, "data", None)
    if data:
        supabase.table("inventories").update(payload).eq("id", data["id"]).execute()
    else:
        supabase.table("inventories").insert({"store_id": row["store_id"], "product_id": row["product_id"], **payload}).execute()


@router.get("/{key}")
def read_board(key: str, _: AuthenticatedUser) -> dict:
    board = _board(key)
    return {
        "board": board,
        **{table: _active_rows(table, int(board["id"])) for table in BOARD_TABLES[key]},
    }


@router.post("/{key}/{resource}", status_code=201)
def create_resource(key: str, resource: str, payload: ResourcePayload, current_user: BusinessEditorUser) -> dict:
    table, _ = _resource(resource, key)
    board = _board(key)
    values = _validate_values(resource, payload.values, create=True)
    if resource in {"md-rows", "md-columns"} and current_user.role_code == "sub_leader":
        raise forbidden("Only admin or leader can change table structure")
    _require_write(current_user, resource, values)
    values.update({"board_id": board["id"], "created_by": current_user.auth_user_id, "updated_by": current_user.auth_user_id})
    created = response_single(supabase.table(table).insert(values).select("*").execute(), "Row could not be created")
    if resource == "m-rows":
        _inventory_replace(created, current_user.auth_user_id)
    return created


@router.patch("/{key}/{resource}/{row_id}")
def update_resource(key: str, resource: str, row_id: int, payload: ResourcePayload, current_user: BusinessEditorUser) -> dict:
    table, _ = _resource(resource, key)
    board = _board(key)
    existing = _row(table, row_id)
    if int(existing["board_id"]) != int(board["id"]) or existing.get("deleted_at"):
        raise not_found("Row not found")
    values = _validate_values(resource, payload.values, create=False)
    _require_write(current_user, resource, values, existing)
    values.update({"updated_by": current_user.auth_user_id, "updated_at": _now()})
    updated = response_single(supabase.table(table).update(values).eq("id", row_id).select("*").execute(), "Row could not be updated")
    if resource == "m-rows":
        _inventory_replace(updated, current_user.auth_user_id)
    return updated


@router.delete("/{key}/{resource}/{row_id}")
def delete_resource(key: str, resource: str, row_id: int, current_user: AuthenticatedUser) -> dict:
    if current_user.role_code != "admin":
        raise forbidden("Only admin can delete rows")
    table, _ = _resource(resource, key)
    if resource not in SOFT_DELETE_RESOURCES:
        raise bad_request("This resource cannot be deleted")
    board = _board(key)
    existing = _row(table, row_id)
    if int(existing["board_id"]) != int(board["id"]):
        raise not_found("Row not found")
    result = response_single(
        supabase.table(table).update({"deleted_at": _now(), "deleted_by": current_user.auth_user_id, "updated_by": current_user.auth_user_id, "updated_at": _now()})
        .eq("id", row_id).select("*").execute(), "Row could not be deleted",
    )
    return result


@router.put("/{key}/{resource}/order")
def reorder_resource(key: str, resource: str, payload: ReorderPayload, current_user: BusinessEditorUser) -> dict:
    table, _ = _resource(resource, key)
    board = _board(key)
    for item in payload.items:
        existing = _row(table, item.id)
        if int(existing["board_id"]) != int(board["id"]):
            raise not_found("Row not found")
        _require_write(current_user, resource, {}, existing)
    for item in payload.items:
        supabase.table(table).update({"sort_order": item.sort_order, "updated_by": current_user.auth_user_id, "updated_at": _now()}).eq("id", item.id).execute()
    return {"ok": True}


@router.put("/{key}/lock")
def update_lock(key: str, payload: LockPayload, current_user: AuthenticatedUser) -> dict:
    if current_user.role_code not in {"admin", "leader"}:
        raise forbidden("Only admin or leader can change locks")
    board = _board(key)
    if key == "drink-refill":
        if payload.store_id is None or payload.scope is None or payload.column_key not in {"status", "name", "max_quantity", "requested_quantity", "note"}:
            raise bad_request("Invalid drink table lock")
        values = {"board_id": board["id"], "store_id": payload.store_id, "scope": payload.scope, "column_key": payload.column_key}
        table = "dtable_locks"
        conflict = "board_id,store_id,scope,column_key"
    elif key == "meal-drink":
        if payload.floor_group is None or payload.column_key != "booth":
            raise bad_request("Invalid meal drink lock")
        values = {"board_id": board["id"], "floor_group": payload.floor_group, "column_key": payload.column_key}
        table = "mdtable_locks"
        conflict = "board_id,floor_group,column_key"
    else:
        raise bad_request("This board has no shared locks")
    values.update({"is_locked": payload.is_locked, "updated_by": current_user.auth_user_id, "updated_at": _now()})
    return response_single(supabase.table(table).upsert(values, on_conflict=conflict).select("*").execute(), "Lock could not be saved")


@router.post("/{key}/actions/clear")
def clear_board(key: str, payload: ClearPayload, current_user: AuthenticatedUser) -> dict:
    if current_user.role_code != "admin":
        raise forbidden("Only admin can clear a board")
    board = _board(key)
    snapshot = _snapshot(board, current_user.auth_user_id, "clear")
    common = {"updated_by": current_user.auth_user_id, "updated_at": _now()}
    if key == "drink-refill":
        if payload.store_id is None or payload.scope is None:
            raise bad_request("Store and scope are required")
        supabase.table("dtable_rows").update({**common, "status": "pending", "requested_quantity": 0, "note": ""}).eq("board_id", board["id"]).eq("store_id", payload.store_id).eq("scope", payload.scope).is_("deleted_at", "null").execute()
    elif key == "meal-drink":
        if payload.floor_group is None:
            raise bad_request("Floor group is required")
        row_ids = [row["id"] for row in _active_rows("mdtable_rows", int(board["id"])) if row["floor_group"] == payload.floor_group]
        if row_ids:
            supabase.table("mdtable_cells").update({**common, "value": ""}).eq("board_id", board["id"]).in_("row_id", row_ids).execute()
    elif key == "inventory":
        supabase.table("mtable_rows").update({**common, "actual_quantity": 0, "note": "", "is_confirmed": False}).eq("board_id", board["id"]).is_("deleted_at", "null").execute()
    elif key == "meal-food":
        supabase.table("mftable_rows").update({**common, "note": ""}).eq("board_id", board["id"]).is_("deleted_at", "null").execute()
        supabase.table("mftable_containers").update({**common, "quantity": 0}).eq("board_id", board["id"]).is_("deleted_at", "null").execute()
    else:
        raise bad_request("Unsupported board")
    return {"ok": True, "snapshot_id": snapshot["id"]}


@router.get("/{key}/snapshots")
def list_snapshots(key: str, current_user: AuthenticatedUser) -> list[dict]:
    if current_user.role_code != "admin":
        raise forbidden("Only admin can view snapshots")
    board = _board(key)
    response = supabase.table("board_snapshots").select("id,reason,created_at,created_by").eq("board_id", board["id"]).order("created_at", desc=True).limit(50).execute()
    return getattr(response, "data", None) or []


@router.post("/{key}/snapshots/{snapshot_id}/restore")
def restore_snapshot(key: str, snapshot_id: int, current_user: AuthenticatedUser) -> dict:
    if current_user.role_code != "admin":
        raise forbidden("Only admin can restore snapshots")
    board = _board(key)
    response = supabase.table("board_snapshots").select("snapshot").eq("id", snapshot_id).eq("board_id", board["id"]).maybe_single().execute()
    data = getattr(response, "data", None)
    if not data:
        raise not_found("Snapshot not found")
    _snapshot(board, current_user.auth_user_id, "before_restore")
    for table, rows in data["snapshot"].items():
        if table not in BOARD_TABLES[key]:
            continue
        snapshot_ids = {int(row["id"]) for row in rows}
        if table not in {"mdtable_cells", "dtable_locks", "mdtable_locks"}:
            for current in _active_rows(table, int(board["id"])):
                if int(current["id"]) not in snapshot_ids:
                    supabase.table(table).update({"deleted_at": _now(), "deleted_by": current_user.auth_user_id, "updated_by": current_user.auth_user_id, "updated_at": _now()}).eq("id", current["id"]).execute()
        for row in rows:
            row_id = row.pop("id")
            row.pop("created_at", None)
            row.pop("difference", None)
            row.update({"updated_by": current_user.auth_user_id, "updated_at": _now()})
            if table not in {"mdtable_cells", "dtable_locks", "mdtable_locks"}:
                row.update({"deleted_at": None, "deleted_by": None})
            supabase.table(table).update(row).eq("id", row_id).eq("board_id", board["id"]).execute()
    return {"ok": True}
