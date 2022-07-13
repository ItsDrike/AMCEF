# type: ignore  # SQLAlchemy models specify Columns, model instances will not be of Column type
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String

from src.utils.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer)
    title: str = Column(String)
    body: str = Column(String)


class Member(Base):
    __tablename__ = "members"

    member_id: int = Column(Integer, primary_key=True, index=True)
    key_salt: Optional[str] = Column(String, nullable=True)
    is_admin: bool = Column(Boolean, default=False)
