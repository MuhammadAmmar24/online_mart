from sqlmodel import create_engine
from app import settings




# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)



engine = create_engine(
    connection_string, connect_args={}, pool_recycle=300, pool_size=10
)