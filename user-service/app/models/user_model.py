from sqlmodel import SQLModel, Field

class UserModel(SQLModel, table=True):
    user_id : int | None = Field(default=None, primary_key=True)
    full_name: str | None = None
    email: str 
    password: str
    address : str

# Update User
class UserUpdate(SQLModel):
    email: str | None = None 
    password: str | None = None
    full_name: str | None = None 
    address: str | None = None


class TokenData(SQLModel):
    iss: str
