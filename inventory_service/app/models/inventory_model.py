from enum import Enum
from sqlmodel import SQLModel, Field

class InventoryStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"

class InventoryItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    product_id: int
    quantity: int
    status: InventoryStatus

class InventoryItemUpdate(SQLModel):
    id: int | None = None
    quantity: int | None = None
    status: InventoryStatus | None = None