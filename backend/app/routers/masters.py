from fastapi import APIRouter

from app.core.auth import AuthenticatedUser
from app.schemas.business import ProductCategory, ProductRead, StoreRead
from app.supabase_client import supabase

router = APIRouter(tags=["masters"])

STORE_SELECT = "id,name,store_type,is_active,created_at,updated_at"
PRODUCT_SELECT = "id,name,category,unit,is_active,created_at,updated_at"


@router.get("/stores", response_model=list[StoreRead])
def read_stores(_: AuthenticatedUser) -> list[dict]:
    return (
        supabase.table("stores")
        .select(STORE_SELECT)
        .eq("is_active", True)
        .order("name")
        .execute()
        .data
        or []
    )


@router.get("/products", response_model=list[ProductRead])
def read_products(_: AuthenticatedUser, category: ProductCategory | None = None) -> list[dict]:
    query = supabase.table("products").select(PRODUCT_SELECT).eq("is_active", True)
    if category:
        query = query.eq("category", category)
    return query.order("category").order("name").execute().data or []
