from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.constants import Connection

# Disable JIT for PostgreSQL database, to improve ENUM datatype handling, for more info, see:
# https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#disabling-the-postgresql-jit-to-improve-enum-datatype-handling
engine = create_async_engine(
    f"postgresql+asyncpg://{Connection.DATABASE_URL}",
    connect_args={"server_settings": {"jit": "off"}},
)

Base = declarative_base()
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
