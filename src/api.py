import logging
from collections.abc import Awaitable, Callable
from typing import cast

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Base
from src.utils.database import SessionLocal, engine
from src.utils.log import setup_logging

log = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    """Perform initial setup and establish connections/sessions."""
    setup_logging()

    log.info("API Server starting...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown() -> None:
    """Close the connections/sessions."""
    log.info("API Server stopping...")
    await engine.dispose()


@app.middleware("http")
async def setup_data(request: Request, callnext: Callable[[Request], Awaitable[Response]]) -> Response:
    """Attach references to database session for the request."""
    db = cast(AsyncSession, SessionLocal())
    try:
        request.state.db_session = db
        return await callnext(request)
    finally:
        await db.close()
