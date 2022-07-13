from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession as DBAsyncSession

from src import crud, models, schemas
from src.constants import Connection

router = APIRouter(tags=["User posts endpoints"])


async def ensure_valid_user_id(httpx_client: httpx.AsyncClient, user_id: int) -> None:
    """
    Custom validation logic for user_id using external API.

    We do this here instead of in the Post model schema because we're making an asynchronous
    request and pydantic doesn't support async validators.
    """
    response = await httpx_client.get(f"{Connection.API_BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        return
    if response.status_code != 404:
        # Make sure we exit loudly with HTTPError from httpx in case the API fails
        # this should produce HTTP code 500 when unhandled within route
        response.raise_for_status()

    # Use the same convention as default FastAPI 422 on pydantic validation error
    err_details = {
        "detail": [
            {
                "loc": ["body", "user_id"],
                "msg": f"There is no user with ID {user_id}",
                "type": "value_error",
            }
        ]
    }
    raise HTTPException(422, err_details)


async def lookup_post(
    db_session: DBAsyncSession,
    httpx_client: httpx.AsyncClient,
    post_id: int,
) -> Optional[models.Post]:
    """
    Find post of given id in our database, or if it's not present, look it up from API.

    If the post isn't present, the lookup will also store the post into our database for faster future lookups.
    If the post lookup fails (both from database and API), return None.
    """
    db_post = await crud.get_post(db_session, post_id)
    if db_post is not None:
        return db_post

    response = await httpx_client.get(f"{Connection.API_BASE_URL}/posts/{post_id}")
    if response.status_code == 404:
        return None
    # Make sure we exit loudly with HTTPError from httpx in case the API fails
    # this should produce HTTP code 500 when unhandled within route
    response.raise_for_status()

    post_data = response.json()
    post_schema = schemas.Post(
        id=post_data["id"],
        user_id=post_data["userId"],
        title=post_data["title"],
        body=post_data["body"],
    )
    db_post = await crud.add_post(db_session, post_schema)
    return db_post


@router.post("/post", response_model=schemas.Post)
async def create_post(request: Request, data: schemas.PostCreate) -> models.Post:
    db_session = request.state.db_session
    httpx_client = request.state.httpx_client

    await ensure_valid_user_id(httpx_client, data.user_id)
    db_post = await crud.add_post(db_session, data)
    return db_post


@router.get("/post/{post_id}", response_model=schemas.Post)
async def get_post(request: Request, post_id: int) -> models.Post:
    db_session = request.state.db_session
    httpx_client = request.state.httpx_client

    db_post = await lookup_post(db_session, httpx_client, post_id)
    if db_post is None:
        raise HTTPException(404, "No such post")
    return db_post


@router.patch("/post/{post_id}", response_model=schemas.Post)
async def update_post(request: Request, post_id: int, data: schemas.PostUpdate) -> models.Post:
    db_session = request.state.db_session

    db_post = await crud.update_post(db_session, post_id, data)
    if not db_post:
        raise HTTPException(404, "No such post")
    return db_post


@router.delete("/post/{post_id}")
async def delete_post(request: Request, post_id: int) -> Response:
    db_session = request.state.db_session

    status = await crud.delete_post(db_session, post_id)
    if status is False:
        raise HTTPException(404, "No such post")
    return Response(status_code=200)
