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
    """Represents possible outcomes of a member attempting to authorize."""

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
        member = await crud.get_member(db_session, int(token_data["id"]))

        if member is None or member.key_salt != token_data["salt"]:
            raise HTTPException(403, AuthState.INVALID_TOKEN.value)
        elif self.require_admin and not member.is_admin:
            raise HTTPException(403, AuthState.NEEDS_ADMIN.value)

        # Token is valid, store the member_id and is_admin data into the request
        request.state.member = member.member_id
        request.state.is_admin = member.is_admin

        return credentials


def _make_member_token(member_id: int) -> tuple[str, str]:
    """
    Generate a JWT token for given member_id.

    Returns a tuple of the JWT token, and the token salt.
    """
    # 22 characters long string
    token_salt = secrets.token_urlsafe(16)
    token_data = {"id": member_id, "salt": token_salt}
    token = jwt.encode(token_data, Server.JWT_SECRET, algorithm="HS256")
    return token, token_salt


async def reset_member(db_session: AsyncSession, member_id: int, *, is_admin: bool = False) -> schemas.TokenMemberData:
    """Generate a new API token for given member and update the member data to match."""
    token, token_salt = _make_member_token(member_id)
    await crud.update_member(db_session, member_id, is_admin=is_admin, key_salt=token_salt)
    ret = schemas.TokenMemberData(member_id=member_id, api_token=token, is_admin=is_admin)
    return ret


async def generate_member(db_session: AsyncSession, *, is_admin: bool = False) -> schemas.TokenMemberData:
    """Generate and store a new member, returning their API token and member id."""
    new_member = await crud.make_blank_member(db_session)
    member_data = await reset_member(db_session, new_member.member_id, is_admin=is_admin)
    return member_data
