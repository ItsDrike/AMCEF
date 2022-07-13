from pydantic import BaseModel

# region: Post


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


# endregion
# region: User


class UserBase(BaseModel):
    user_id: int
    is_admin: bool


class User(UserBase):
    key_salt: str

    class Config:
        orm_mode = True
