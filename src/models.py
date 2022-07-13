from sqlalchemy import Column, Integer, String

from src.utils.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    title = Column(String)
    body = Column(String)
