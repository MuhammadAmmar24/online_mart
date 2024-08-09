from sqlmodel import SQLModel, Field

class OrderModel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    product_id: int
    quantity: int
    total_amount: float
    status : str = Field(default="Processing")
    # created_at: str | None = None
    # updated_at: str | None = None

class OrderCreate(SQLModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    status : str = Field(default="Processing")

class OrderUpdate(SQLModel):
    # user_id: int | None = None
    quantity: int | None = None
    total_amount: float | None = None
    status : str | None = Field(default="Processing")
    # status: OrderStatus | None = None
