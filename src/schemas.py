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
# region: Member


class MemberData(BaseModel):
    member_id: int
    is_admin: bool

    class Config:
        orm_mode = True


class TokenMemberData(MemberData):
    api_token: str


# endregion
