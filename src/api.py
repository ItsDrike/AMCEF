import logging
from collections.abc import Awaitable, Callable

import httpx
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from src.constants import Server
from src.endpoints import admin, user_posts
from src.models import Base
from src.utils.database import SessionLocal, engine
from src.utils.log import setup_logging

log = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.include_router(user_posts.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup() -> None:
    """Perform initial setup and establish connections/sessions."""
    setup_logging()

    log.info("API Server starting...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.httpx_client = httpx.AsyncClient()
    app.state.db_session = SessionLocal()


@app.on_event("shutdown")
async def shutdown() -> None:
    """Close the connections/sessions."""
    log.info("API Server stopping...")
    await engine.dispose()
    await app.state.httpx_client.aclose()
    await app.state.db_session.close()


@app.middleware("http")
async def setup_data(request: Request, callnext: Callable[[Request], Awaitable[Response]]) -> Response:
    """Attach references to database session for the request."""
    request.state.httpx_client = app.state.httpx_client
    request.state.db_session = app.state.db_session
    return await callnext(request)


@app.get("/", include_in_schema=False)
async def info(request: Request) -> Response:
    # Use 302 (Temporary redirect) to avoid browsers to cache this
    # since the API may at some point actually have some index page
    # rather than just always redirecting to docs page
    return RedirectResponse(url="/docs", status_code=302)


@app.get("/docs", include_in_schema=False)
async def docs(request: Request) -> Response:
    """Return rendered API docs page."""
    return Server.TEMPLATES.TemplateResponse("docs.html", {"request": request})
