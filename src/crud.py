"""
This file contains CRUD database interactions, standing for
C: Create
R: Read
U: Update
D: Delete
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src import models, schemas

# region: Post


async def get_post(session: AsyncSession, id: int) -> Optional[models.Post]:
    stmt = select(models.Post).filter(models.Post.id == id)
    r = await session.execute(stmt)
    db_model = r.scalars().first()
    return db_model


async def add_post(session: AsyncSession, schema: schemas.PostCreate) -> models.Post:
    db_model = models.Post(**schema.dict())
    session.add(db_model)
    await session.commit()
    await session.refresh(db_model)
    return db_model


async def delete_post(session: AsyncSession, post_id: int) -> bool:
    db_model = await get_post(session, post_id)
    if db_model is None:
        return False
    await session.delete(db_model)
    await session.commit()
    return True


async def update_post(session: AsyncSession, post_id: int, schema: schemas.PostUpdate) -> Optional[models.Post]:
    db_model = await get_post(session, post_id)
    if db_model is None:
        return None

    for var, value in vars(schema).items():
        setattr(db_model, var, value) if value else None

    session.add(db_model)
    await session.commit()
    await session.refresh(db_model)
    return db_model


async def get_user_posts(session: AsyncSession, user_id: int) -> list[models.Post]:
    stmt = select(models.Post).filter(models.Post.user_id == user_id)
    r = await session.execute(stmt)
    db_models = r.scalars().fetchall()
    return db_models


# endregion
# region: Member


async def make_blank_member(session: AsyncSession) -> models.Member:
    db_model = models.Member()
    session.add(db_model)
    await session.commit()
    await session.refresh(db_model)
    return db_model


async def get_member(session: AsyncSession, member_id: int) -> models.Member:
    stmt = select(models.Member).filter(models.Member.member_id == member_id)
    r = await session.execute(stmt)
    db_model = r.scalars().first()
    return db_model


async def delete_member(session: AsyncSession, member_id: int) -> bool:
    db_model = await get_member(session, member_id)
    if db_model is None:
        return False
    await session.delete(db_model)
    await session.commit()
    return True


async def update_member(
    session: AsyncSession,
    member_id: int,
    *,
    is_admin: Optional[bool] = None,
    key_salt: Optional[str] = None,
) -> Optional[models.Member]:
    db_model = await get_member(session, member_id)
    if db_model is None:
        return None

    if is_admin is not None:
        db_model.is_admin = is_admin
    if key_salt is not None:
        db_model.key_salt = key_salt

    session.add(db_model)
    await session.commit()
    await session.refresh(db_model)
    return db_model


# endregion
