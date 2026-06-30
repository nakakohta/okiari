from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ProductCategory = Literal["meal", "drink", "inventory"]
RestockStatus = Literal["requested", "working", "completed", "cancelled"]


class StoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    store_type: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    unit: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReportUserRead(BaseModel):
    id: UUID
    display_name: str
    email: str


class MealReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_date: date
    store_id: int
    product_id: int
    quantity: int = Field(ge=0)
    note: str | None = None


class MealReportRead(MealReportCreate):
    id: int
    reported_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    store: StoreRead | None = None
    product: ProductRead | None = None
    reporter: ReportUserRead | None = None


class RestockReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_id: int
    product_id: int
    quantity: int = Field(gt=0)
    note: str | None = None


class RestockStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RestockStatus


class RestockReportRead(RestockReportCreate):
    id: int
    requested_at: datetime
    completed_at: datetime | None = None
    status: RestockStatus
    requested_by: UUID | None = None
    completed_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    store: StoreRead | None = None
    product: ProductRead | None = None
    requested_by_user: ReportUserRead | None = None
    completed_by_user: ReportUserRead | None = None


class InventoryCheckCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check_date: date
    store_id: int
    product_id: int
    expected_quantity: int | None = Field(default=None, ge=0)
    actual_quantity: int = Field(ge=0)
    is_confirmed: bool = False
    note: str | None = None


class InventoryCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    check_date: date
    store_id: int
    product_id: int
    expected_quantity: int
    actual_quantity: int
    difference: int | None = None
    checked_by: UUID | None = None
    is_confirmed: bool
    note: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    store: StoreRead | None = None
    product: ProductRead | None = None
    checker: ReportUserRead | None = None


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: int
    product_id: int
    quantity: int
    updated_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    store: StoreRead | None = None
    product: ProductRead | None = None
