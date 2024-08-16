from sqlmodel import SQLModel, Field

class Notification(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    subject: str | None = None
    message: str
    status: str | None = None
