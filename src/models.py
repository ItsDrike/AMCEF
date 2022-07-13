from sqlalchemy import Boolean, Column, Integer, String

from src.utils.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    title = Column(String)
    body = Column(String)


class Member(Base):
    __tablename__ = "members"

    member_id = Column(Integer, primary_key=True, index=True)
    key_salt = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
