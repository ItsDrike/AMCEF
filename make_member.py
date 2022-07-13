#!/usr/bin/env python
import asyncio

from src import models
from src.utils.auth import generate_member
from src.utils.database import SessionLocal, engine


async def main() -> tuple[str, int]:
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with SessionLocal() as db_session:
        member = await generate_member(db_session, is_admin=True)

    return member.api_token, member.member_id


if __name__ == "__main__":
    api_token, user_id = asyncio.run(main())
    print(api_token, user_id)
