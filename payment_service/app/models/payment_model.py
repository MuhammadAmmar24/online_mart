from sqlmodel import SQLModel, Field

class Payment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    order_id: int
    user_id: int
    amount: float
    status: str  # Could be 'pending', 'completed', 'failed', 'canceled' etc.


