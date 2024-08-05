from sqlmodel import SQLModel, Field

class Product(SQLModel, table=True):
    id : int | None = Field(default=None, primary_key=True)
    title : str
    description: str
    category : str
    price : float
    discount : int | None = None
    quantity : int | None = None
    brand : str | None = None
    weight : float | None 
    expiry : str | None = None
    

# Update Product
class ProductUpdate(SQLModel):
    title : str | None = None 
    description: str | None = None 
    category : str | None = None 
    price : float | None = None
    discount : int | None = None
    quantity : int | None = None
    brand : str | None = None
    weight : float | None 
    expiry : str | None = None
