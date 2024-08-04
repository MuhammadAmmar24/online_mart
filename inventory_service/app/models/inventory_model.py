from sqlmodel import SQLModel, Field


class InventoryItem(SQLModel, table=True):
    id : int | None = Field(default=None, primary_key=True)
    id: int
    variant_id: int | None = None
    quantity: int 
    status: str
    
1