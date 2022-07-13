import logging

from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response

from src import crud, models, schemas
from src.utils.external_api import ensure_valid_user_id, lookup_post

log = logging.getLogger(__name__)

router = APIRouter(tags=["User posts endpoints"])


@router.post("/post", response_model=schemas.Post)
async def create_post(request: Request, data: schemas.PostCreate) -> models.Post:
    db_session = request.state.db_session
    httpx_client = request.state.httpx_client

    try:
        await ensure_valid_user_id(httpx_client, data.user_id)
    except ValueError as exc:
        # Use the same convention as default FastAPI 422 on pydantic validation error
        err_details = {
            "detail": [
                {
                    "loc": ["body", "user_id"],
                    "msg": str(exc),
                    "type": "value_error",
                }
            ]
        }
        raise HTTPException(422, err_details)

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


@router.get("/posts/{user_id}", response_model=list[schemas.Post])
async def get_posts(request: Request, user_id: int) -> list[models.Post]:
    db_session = request.state.db_session

    db_posts = await crud.get_user_posts(db_session, user_id)
    return db_posts
