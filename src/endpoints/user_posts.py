import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response

from src import crud, models, schemas
from src.constants import Ratelimits
from src.utils.auth import JWTBearer
from src.utils.external_api import ensure_valid_user_id, lookup_post
from src.utils.ratelimits.ip_bucket import IPRedisBucket
from src.utils.ratelimits.member_bucket import MemberRedisBucket

log = logging.getLogger(__name__)

router = APIRouter(tags=["User posts endpoints"])
member_router = APIRouter(dependencies=[Depends(JWTBearer())])
member_ratelimit_bucket = MemberRedisBucket(
    requests=Ratelimits.REQUESTS_PER_PERIOD,
    time_period=Ratelimits.TIME_PERIOD,
    cooldown=Ratelimits.COOLDOWN_PERIOD,
)


@member_ratelimit_bucket
@member_router.post("/post", response_model=schemas.Post)
async def create_post(request: Request, data: schemas.PostCreate) -> models.Post:
    """Create a new user post and return the created post."""
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


@IPRedisBucket(requests=20, time_period=20, cooldown=50)
@router.get("/post/{post_id}", response_model=schemas.Post)
async def get_post(request: Request, post_id: int) -> models.Post:
    """Obtain a post with given `post_id`.

    Note: If post with this id is not found in the cache database, this will perform an API lookup.
    """
    db_session = request.state.db_session
    httpx_client = request.state.httpx_client

    db_post = await lookup_post(db_session, httpx_client, post_id)
    if db_post is None:
        raise HTTPException(404, "No such post")
    return db_post


@member_ratelimit_bucket
@member_router.patch("/post/{post_id}", response_model=schemas.Post)
async def update_post(request: Request, post_id: int, data: schemas.PostUpdate) -> models.Post:
    """Update title or body of a post with given `post_id`"""
    db_session = request.state.db_session

    db_post = await crud.update_post(db_session, post_id, data)
    if not db_post:
        raise HTTPException(404, "No such post")
    return db_post


@member_ratelimit_bucket
@member_router.delete("/post/{post_id}")
async def delete_post(request: Request, post_id: int) -> Response:
    """Delete post with given `post_id` from the database."""
    db_session = request.state.db_session

    status = await crud.delete_post(db_session, post_id)
    if status is False:
        raise HTTPException(404, "No such post")
    return Response(status_code=200)


@router.get("/posts/{user_id}", response_model=list[schemas.Post])
async def get_posts(request: Request, user_id: int) -> list[models.Post]:
    """Obtain a list of all posts with given `user_id`.

    Note: This only obtains posts from the cached database, it does not perform an API lookup.
    """
    db_session = request.state.db_session

    db_posts = await crud.get_user_posts(db_session, user_id)
    return db_posts


router.include_router(member_router)
