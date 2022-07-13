import secrets
from enum import Enum
from typing import cast

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, schemas
from src.constants import Server


class AuthState(Enum):
    """Represents possible outcomes of a user attempting to authorize."""

    NO_TOKEN = (
        "There is no token provided, provide one in an Authorization header in the format 'Bearer {your token here}'."
        "If you don't have a token, ask an administrator to generate you one."
    )
    INVALID_TOKEN = (
        "The token provided is not a valid token or has expired, ask an administrator to generate you a new token."
    )
    NEEDS_ADMIN = "This endpoint is limited to admins."


class JWTBearer(HTTPBearer):
    """Dependency for routes to enforce JWT auth."""

    def __init__(self, auto_error: bool = True, require_admin: bool = False):
        super().__init__(auto_error=auto_error)
        self.require_admin = require_admin

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        """Check if the supplied credentials are valid for this endpoint."""
        credentials = cast(HTTPAuthorizationCredentials, await super().__call__(request))
        jwt_token = credentials.credentials
        if not jwt_token:
            raise HTTPException(403, AuthState.NO_TOKEN.value)

        try:
            token_data = jwt.decode(jwt_token, Server.JWT_SECRET)
        except JWTError:
            raise HTTPException(403, AuthState.INVALID_TOKEN.value)

        db_session = request.state.db_session
        user = await crud.get_user(db_session, int(token_data["id"]))

        if user is None or user.key_salt != token_data["salt"]:
            raise HTTPException(403, AuthState.INVALID_TOKEN.value)
        elif self.require_admin and not user.is_admin:
            raise HTTPException(403, AuthState.NEEDS_ADMIN.value)

        # Token is valid, store the user_id and is_admin data into the request
        request.state.user_id = user.user_id
        request.state.is_admin = user.is_admin

        return credentials


def _make_user_token(user_id: int) -> tuple[str, str]:
    """
    Generate a JWT token for given user_id.

    Returns a tuple of the JWT token, and the token salt.
    """
    # 22 characters long string
    token_salt = secrets.token_urlsafe(16)
    token_data = {"id": user_id, "salt": token_salt}
    token = jwt.encode(token_data, Server.JWT_SECRET, algorithm="HS256")
    return token, token_salt


async def generate_user_token(db_session: AsyncSession, user_id: int) -> str:
    """Generate a new API token for given user and store this user into the database."""

    token, token_salt = _make_user_token(user_id)
    # TODO: Obtain admin status from config somewhere
    is_admin = False

    user = schemas.User(user_id=user_id, is_admin=is_admin, key_salt=token_salt)
    await crud.add_user(db_session, user)
    return token