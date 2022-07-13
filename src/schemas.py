from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    body: str


class PostUpdate(PostBase):
    ...


class PostCreate(PostUpdate):
    user_id: int


class Post(PostCreate):
    id: int

    class Config:
        orm_mode = True
