from sqlmodel import SQLModel, Field

class UserModel(SQLModel, table=True):
    user_id : int | None = Field(default=None, primary_key=True)
    username: str
    email: str
    full_name: str | None = None
    password: str

# Update User
class UserUpdate(SQLModel):
    username: str | None = None 
    email: str | None = None 
    full_name: str | None = None 
    password: str | None = None


