from sqlmodel import SQLModel, Field  
import datetime

class Order(SQLModel, table=True):
    order_id : int | None = Field(default=None, primary_key=True)
    customer_name : str
    customer_email: str
    product_id: int
    quantity: float
    total_amount: float
    # order_date: datetime
    order_status: str
    

# Update Order
class OrderUpdate(SQLModel):
    order_id : int | None = None 
    customer_name : str | None = None 
    customer_email : str | None = None 
    product_id : int | None = None 
    quantity : float | None = None 
    total_amount : float | None = None 
    # order_date : datetime | None = None 
    order_status : str | None = None 
