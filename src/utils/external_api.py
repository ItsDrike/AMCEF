import logging
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession as DBAsyncSession

from src import crud, models, schemas
from src.constants import Connection

log = logging.getLogger(__name__)


async def ensure_valid_user_id(httpx_client: httpx.AsyncClient, user_id: int) -> None:
    """
    Custom validation logic for user_id using external API.

    We do this here instead of in the Post model schema because we're making an asynchronous
    request and pydantic doesn't support async validators.
    """
    log.debug(f"Checking validity of {user_id=}")
    response = await httpx_client.get(f"{Connection.API_BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        log.debug(f"Validity for {user_id=} confirmed")
        return
    if response.status_code != 404:
        # Make sure we exit loudly with HTTPError from httpx in case the API fails
        # this should produce HTTP code 500 when unhandled within route
        response.raise_for_status()

    log.debug(f"Validity for {user_id=} failed, no such user.")
    raise ValueError(f"User with {user_id=} doesn't exist.")


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
    log.debug(f"Looking up post {post_id}")
    db_post = await crud.get_post(db_session, post_id)
    if db_post is not None:
        log.debug(f"Post {post_id} found from database")
        return db_post

    log.debug(f"Post {post_id} not present in database, falling back to API lookup")
    response = await httpx_client.get(f"{Connection.API_BASE_URL}/posts/{post_id}")
    if response.status_code == 404:
        log.debug(f"Post {post_id} not present on API.")
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
    log.debug(f"Obtained post {post_id} from the API, storing it into the database")
    db_post = await crud.add_post(db_session, post_schema)
    return db_post
