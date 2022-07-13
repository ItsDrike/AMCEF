#!/usr/bin/env python
import asyncio

from src import models
from src.utils.auth import generate_user_token
from src.utils.database import SessionLocal, engine


async def main(user_id: int) -> str:
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with SessionLocal() as db_session:
        token = await generate_user_token(db_session, user_id, is_admin=True)

    return token


if __name__ == "__main__":
    user_id = 1
    token = asyncio.run(main(user_id))
    print(token)
