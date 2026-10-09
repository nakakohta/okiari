from datetime import UTC, date, datetime

from fastapi import APIRouter

from app.core.auth import AuthenticatedUser, BusinessEditorUser
from app.core.db import response_single
from app.core.errors import bad_request, forbidden, not_found
from app.schemas.business import (
    InventoryCheckCreate,
    InventoryCheckRead,
    InventoryCheckUpdate,
    MealReportCreate,
    MealReportRead,
    MealReportUpdate,
    RestockReportCreate,
    RestockReportRead,
    RestockReportUpdate,
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
    response = (
        supabase.table("products")
        .select("id")
        .eq("id", product_id)
        .eq("category", category)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    product = getattr(response, "data", None)
    if not product:
        raise not_found(f"Active {category} product not found")


def _require_store(store_id: int) -> None:
    response = (
        supabase.table("stores")
        .select("id")
        .eq("id", store_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    store = getattr(response, "data", None)
    if not store:
        raise not_found("Active store not found")


def _allowed_store_ids(current_user: AuthenticatedUser, *, edit: bool = False) -> list[int] | None:
    if current_user.role_code == "admin":
        return None

    permission_column = "can_edit" if edit else "can_view"
    response = (
        supabase.table("user_store_assignments")
        .select("store_id")
        .eq("user_id", current_user.auth_user_id)
        .eq(permission_column, True)
        .execute()
    )
    return [int(item["store_id"]) for item in (getattr(response, "data", None) or [])]


def _require_store_access(current_user: AuthenticatedUser, store_id: int, *, edit: bool = False) -> None:
    allowed_store_ids = _allowed_store_ids(current_user, edit=edit)
    if allowed_store_ids is not None and store_id not in allowed_store_ids:
        permission = "edit" if edit else "view"
        raise forbidden(f"Store {permission} permission is required")


def _require_report_row(table: str, report_id: int) -> dict:
    response = (
        supabase.table(table)
        .select("id,store_id")
        .eq("id", report_id)
        .maybe_single()
        .execute()
    )
    row = getattr(response, "data", None)
    if not row:
        raise not_found("Report not found")
    return row


def _current_inventory_quantity(store_id: int, product_id: int) -> int:
    response = (
        supabase.table("inventories")
        .select("quantity")
        .eq("store_id", store_id)
        .eq("product_id", product_id)
        .maybe_single()
        .execute()
    )
    inventory = getattr(response, "data", None)
    return int(inventory["quantity"]) if inventory else 0


def _replace_inventory(store_id: int, product_id: int, quantity: int, user_id: str) -> None:
    response = (
        supabase.table("inventories")
        .select("id")
        .eq("store_id", store_id)
        .eq("product_id", product_id)
        .maybe_single()
        .execute()
    )
    existing = getattr(response, "data", None)
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
def read_meal_reports(current_user: AuthenticatedUser, report_date: date | None = None) -> list[dict]:
    allowed_store_ids = _allowed_store_ids(current_user)
    if allowed_store_ids == []:
        return []

    query = supabase.table("meal_reports").select(MEAL_SELECT)
    if allowed_store_ids is not None:
        query = query.in_("store_id", allowed_store_ids)
    if report_date is not None:
        query = query.eq("report_date", report_date.isoformat())

    return query.order("report_date", desc=True).order("created_at", desc=True).limit(500).execute().data or []


@router.post("/meal-reports", response_model=MealReportRead, status_code=201)
def create_meal_report(payload: MealReportCreate, current_user: BusinessEditorUser) -> dict:
    _require_store(payload.store_id)
    _require_store_access(current_user, payload.store_id, edit=True)
    _require_product(payload.product_id, "meal")
    created = response_single(
        supabase.table("meal_reports")
        .insert({**payload.model_dump(mode="json"), "reported_by": current_user.auth_user_id})
        .select(MEAL_SELECT)
        .execute(),
        "Meal report was created but could not be read",
    )
    return created


@router.put("/meal-reports/cell", response_model=MealReportRead)
def upsert_meal_report(payload: MealReportCreate, current_user: BusinessEditorUser) -> dict:
    _require_store(payload.store_id)
    _require_store_access(current_user, payload.store_id, edit=True)
    _require_product(payload.product_id, "meal")

    values = {
        **payload.model_dump(mode="json"),
        "reported_by": current_user.auth_user_id,
        "updated_at": _now(),
    }
    response = (
        supabase.table("meal_reports")
        .upsert(values, on_conflict="report_date,store_id,product_id")
        .select(MEAL_SELECT)
        .execute()
    )

    return response_single(response, "Meal report could not be saved")


@router.patch("/meal-reports/{report_id}", response_model=MealReportRead)
def update_meal_report(
    report_id: int,
    payload: MealReportUpdate,
    current_user: BusinessEditorUser,
) -> dict:
    row = _require_report_row("meal_reports", report_id)
    _require_store_access(current_user, int(row["store_id"]), edit=True)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise bad_request("No update fields were supplied")
    if updates.get("quantity", 0) is None:
        raise bad_request("Quantity cannot be null")
    updates["reported_by"] = current_user.auth_user_id
    updates["updated_at"] = _now()
    return response_single(
        supabase.table("meal_reports")
        .update(updates)
        .eq("id", report_id)
        .select(MEAL_SELECT)
        .execute(),
        "Meal report could not be updated",
    )


@router.get("/drink-refills", response_model=list[RestockReportRead])
def read_drink_refills(current_user: AuthenticatedUser) -> list[dict]:
    allowed_store_ids = _allowed_store_ids(current_user)
    if allowed_store_ids == []:
        return []
    query = supabase.table("restock_reports").select(RESTOCK_SELECT)
    if allowed_store_ids is not None:
        query = query.in_("store_id", allowed_store_ids)
    return query.order("requested_at", desc=True).limit(500).execute().data or []


@router.post("/drink-refills", response_model=RestockReportRead, status_code=201)
def create_drink_refill(payload: RestockReportCreate, current_user: BusinessEditorUser) -> dict:
    _require_store(payload.store_id)
    _require_store_access(current_user, payload.store_id, edit=True)
    _require_product(payload.product_id, "drink")
    created = response_single(
        supabase.table("restock_reports")
        .insert({**payload.model_dump(mode="json"), "requested_by": current_user.auth_user_id})
        .select(RESTOCK_SELECT)
        .execute(),
        "Restock report was created but could not be read",
    )
    return created


@router.patch("/drink-refills/{report_id}/status", response_model=RestockReportRead)
def update_drink_refill_status(report_id: int, payload: RestockStatusUpdate, current_user: BusinessEditorUser) -> dict:
    row = _require_report_row("restock_reports", report_id)
    _require_store_access(current_user, int(row["store_id"]), edit=True)
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
        .execute(),
        "Restock report was updated but could not be read",
    )
    return updated


@router.patch("/drink-refills/{report_id}", response_model=RestockReportRead)
def update_drink_refill(
    report_id: int,
    payload: RestockReportUpdate,
    current_user: BusinessEditorUser,
) -> dict:
    row = _require_report_row("restock_reports", report_id)
    _require_store_access(current_user, int(row["store_id"]), edit=True)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise bad_request("No update fields were supplied")
    if updates.get("quantity", 1) is None or updates.get("status", "requested") is None:
        raise bad_request("Quantity and status cannot be null")

    status = updates.get("status")
    if status == "completed":
        updates["completed_at"] = _now()
        updates["completed_by"] = current_user.auth_user_id
    elif status in {"requested", "working", "cancelled"}:
        updates["completed_at"] = None
        updates["completed_by"] = None
    updates["updated_at"] = _now()

    return response_single(
        supabase.table("restock_reports")
        .update(updates)
        .eq("id", report_id)
        .select(RESTOCK_SELECT)
        .execute(),
        "Restock report could not be updated",
    )


@router.get("/inventory-checks", response_model=list[InventoryCheckRead])
def read_inventory_checks(current_user: AuthenticatedUser) -> list[dict]:
    allowed_store_ids = _allowed_store_ids(current_user)
    if allowed_store_ids == []:
        return []
    query = supabase.table("inventory_checks").select(INVENTORY_CHECK_SELECT)
    if allowed_store_ids is not None:
        query = query.in_("store_id", allowed_store_ids)
    return query.order("check_date", desc=True).order("created_at", desc=True).limit(500).execute().data or []


@router.post("/inventory-checks", response_model=InventoryCheckRead, status_code=201)
def create_inventory_check(payload: InventoryCheckCreate, current_user: BusinessEditorUser) -> dict:
    _require_store(payload.store_id)
    _require_store_access(current_user, payload.store_id, edit=True)
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
        .execute(),
        "Inventory check was created but could not be read",
    )
    if payload.is_confirmed:
        _replace_inventory(payload.store_id, payload.product_id, payload.actual_quantity, current_user.auth_user_id)
    return created


@router.patch("/inventory-checks/{report_id}", response_model=InventoryCheckRead)
def update_inventory_check(
    report_id: int,
    payload: InventoryCheckUpdate,
    current_user: BusinessEditorUser,
) -> dict:
    row = _require_report_row("inventory_checks", report_id)
    _require_store_access(current_user, int(row["store_id"]), edit=True)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise bad_request("No update fields were supplied")
    non_nullable_fields = {"expected_quantity", "actual_quantity", "is_confirmed"}
    if any(field in updates and updates[field] is None for field in non_nullable_fields):
        raise bad_request("Inventory quantities and confirmation cannot be null")
    updates["checked_by"] = current_user.auth_user_id
    updates["updated_at"] = _now()

    updated = response_single(
        supabase.table("inventory_checks")
        .update(updates)
        .eq("id", report_id)
        .select(INVENTORY_CHECK_SELECT)
        .execute(),
        "Inventory check could not be updated",
    )
    if updated["is_confirmed"]:
        _replace_inventory(
            int(updated["store_id"]),
            int(updated["product_id"]),
            int(updated["actual_quantity"]),
            current_user.auth_user_id,
        )
    return updated


@router.get("/inventories", response_model=list[dict])
def read_inventories(current_user: AuthenticatedUser) -> list[dict]:
    allowed_store_ids = _allowed_store_ids(current_user)
    if allowed_store_ids == []:
        return []
    query = supabase.table("inventories").select(INVENTORY_SELECT)
    if allowed_store_ids is not None:
        query = query.in_("store_id", allowed_store_ids)
    return query.order("updated_at", desc=True).limit(500).execute().data or []
