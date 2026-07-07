from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.auth import AuthenticatedUser, BusinessEditorUser
from app.core.db import response_single
from app.core.errors import conflict, not_found
from app.schemas.business import (
    InventoryCheckCreate,
    InventoryCheckRead,
    MealReportCreate,
    MealReportRead,
    RestockReportCreate,
    RestockReportRead,
    RestockStatusUpdate,
)
from app.supabase_client import supabase

router = APIRouter(tags=["reports"])

STORE_SELECT = "id,name,store_type,is_active,created_at,updated_at"
PRODUCT_SELECT = "id,name,category,unit,is_active,created_at,updated_at"
USER_SELECT = "id,display_name,email"
MEAL_SELECT = (
    "id,report_date,store_id,product_id,quantity,reported_by,note,created_at,updated_at,"
    f"store:stores({STORE_SELECT}),product:products({PRODUCT_SELECT}),"
    f"reporter:app_users!meal_reports_reported_by_fkey({USER_SELECT})"
)
RESTOCK_SELECT = (
    "id,requested_at,completed_at,store_id,product_id,quantity,status,requested_by,completed_by,note,created_at,updated_at,"
    f"store:stores({STORE_SELECT}),product:products({PRODUCT_SELECT}),"
    f"requested_by_user:app_users!restock_reports_requested_by_fkey({USER_SELECT}),"
    f"completed_by_user:app_users!restock_reports_completed_by_fkey({USER_SELECT})"
)
INVENTORY_CHECK_SELECT = (
    "id,check_date,store_id,product_id,expected_quantity,actual_quantity,difference,checked_by,is_confirmed,note,created_at,updated_at,"
    f"store:stores({STORE_SELECT}),product:products({PRODUCT_SELECT}),"
    f"checker:app_users!inventory_checks_checked_by_fkey({USER_SELECT})"
)
INVENTORY_SELECT = (
    "id,store_id,product_id,quantity,updated_by,created_at,updated_at,"
    f"store:stores({STORE_SELECT}),product:products({PRODUCT_SELECT})"
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _require_product(product_id: int, category: str) -> None:
    product = (
        supabase.table("products")
        .select("id")
        .eq("id", product_id)
        .eq("category", category)
        .eq("is_active", True)
        .maybe_single()
        .execute()
        .data
    )
    if not product:
        raise not_found(f"Active {category} product not found")


def _require_store(store_id: int) -> None:
    store = (
        supabase.table("stores")
        .select("id")
        .eq("id", store_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
        .data
    )
    if not store:
        raise not_found("Active store not found")


def _current_inventory_quantity(store_id: int, product_id: int) -> int:
    inventory = (
        supabase.table("inventories")
        .select("quantity")
        .eq("store_id", store_id)
        .eq("product_id", product_id)
        .maybe_single()
        .execute()
        .data
    )
    return int(inventory["quantity"]) if inventory else 0


def _replace_inventory(store_id: int, product_id: int, quantity: int, user_id: str) -> None:
    existing = (
        supabase.table("inventories")
        .select("id")
        .eq("store_id", store_id)
        .eq("product_id", product_id)
        .maybe_single()
        .execute()
        .data
    )
    payload = {"quantity": quantity, "updated_by": user_id, "updated_at": _now()}
    if existing:
        supabase.table("inventories").update(payload).eq("id", existing["id"]).execute()
    else:
        supabase.table("inventories").insert(
            {
                "store_id": store_id,
                "product_id": product_id,
                **payload,
            }
        ).execute()


@router.get("/meal-reports", response_model=list[MealReportRead])
def read_meal_reports(_: AuthenticatedUser) -> list[dict]:
    return (
        supabase.table("meal_reports")
        .select(MEAL_SELECT)
        .order("report_date", desc=True)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
        .data
        or []
    )


@router.post("/meal-reports", response_model=MealReportRead, status_code=201)
def create_meal_report(payload: MealReportCreate, current_user: BusinessEditorUser) -> dict:
    _require_store(payload.store_id)
    _require_product(payload.product_id, "meal")
    created = response_single(
        supabase.table("meal_reports")
        .insert({**payload.model_dump(mode="json"), "reported_by": current_user.auth_user_id})
        .select(MEAL_SELECT)
        .single()
        .execute(),
        "Meal report was created but could not be read",
    )
    return created


@router.get("/drink-refills", response_model=list[RestockReportRead])
def read_drink_refills(_: AuthenticatedUser) -> list[dict]:
    return (
        supabase.table("restock_reports")
        .select(RESTOCK_SELECT)
        .order("requested_at", desc=True)
        .limit(100)
        .execute()
        .data
        or []
    )


@router.post("/drink-refills", response_model=RestockReportRead, status_code=201)
def create_drink_refill(payload: RestockReportCreate, current_user: BusinessEditorUser) -> dict:
    _require_store(payload.store_id)
    _require_product(payload.product_id, "drink")
    created = response_single(
        supabase.table("restock_reports")
        .insert({**payload.model_dump(mode="json"), "requested_by": current_user.auth_user_id})
        .select(RESTOCK_SELECT)
        .single()
        .execute(),
        "Restock report was created but could not be read",
    )
    return created


@router.patch("/drink-refills/{report_id}/status", response_model=RestockReportRead)
def update_drink_refill_status(report_id: int, payload: RestockStatusUpdate, current_user: BusinessEditorUser) -> dict:
    updates: dict[str, str | None] = {"status": payload.status, "updated_at": _now()}
    if payload.status == "completed":
        updates["completed_at"] = _now()
        updates["completed_by"] = current_user.auth_user_id
    elif payload.status in {"requested", "working", "cancelled"}:
        updates["completed_at"] = None
        updates["completed_by"] = None

    updated = response_single(
        supabase.table("restock_reports")
        .update(updates)
        .eq("id", report_id)
        .select(RESTOCK_SELECT)
        .single()
        .execute(),
        "Restock report was updated but could not be read",
    )
    return updated


@router.get("/inventory-checks", response_model=list[InventoryCheckRead])
def read_inventory_checks(_: AuthenticatedUser) -> list[dict]:
    return (
        supabase.table("inventory_checks")
        .select(INVENTORY_CHECK_SELECT)
        .order("check_date", desc=True)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
        .data
        or []
    )


@router.post("/inventory-checks", response_model=InventoryCheckRead, status_code=201)
def create_inventory_check(payload: InventoryCheckCreate, current_user: BusinessEditorUser) -> dict:
    _require_store(payload.store_id)
    _require_product(payload.product_id, "inventory")
    expected_quantity = (
        payload.expected_quantity
        if payload.expected_quantity is not None
        else _current_inventory_quantity(payload.store_id, payload.product_id)
    )
    insert_payload = payload.model_dump(mode="json", exclude={"expected_quantity"})
    insert_payload["expected_quantity"] = expected_quantity
    insert_payload["checked_by"] = current_user.auth_user_id
    created = response_single(
        supabase.table("inventory_checks")
        .insert(insert_payload)
        .select(INVENTORY_CHECK_SELECT)
        .single()
        .execute(),
        "Inventory check was created but could not be read",
    )
    if payload.is_confirmed:
        _replace_inventory(payload.store_id, payload.product_id, payload.actual_quantity, current_user.auth_user_id)
    return created


@router.get("/inventories", response_model=list[dict])
def read_inventories(_: AuthenticatedUser) -> list[dict]:
    return (
        supabase.table("inventories")
        .select(INVENTORY_SELECT)
        .order("updated_at", desc=True)
        .limit(100)
        .execute()
        .data
        or []
    )
