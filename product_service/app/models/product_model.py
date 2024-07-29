from sqlmodel import SQLModel, Field


class Product(SQLModel, table=True):
    # id : int | None = Field(default=None, primary_key=True)
    # title : str
    # description: str
    # category : str
    # price : float
    # discount : int | None = None
    # quantity : float 
    # brand : str | None = None
    # weight : float | None 
    # expiry : str | None = None
    # sku : str | None = None
    
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)
    

# Update Product
class ProductUpdate(SQLModel):
    title : str | None = None 
    description: str | None = None 
    category : str | None = None 
    price : float | None = None
    discount : int | None = None
    quantity : float | None = None
    brand : str | None = None
    weight : float | None 
    expiry : str | None = None
    sku : str | None = None
