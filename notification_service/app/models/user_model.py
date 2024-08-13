from sqlmodel import SQLModel, Field

class UserModel(SQLModel):
    email: str | None = None
    full_name: str | None = None

