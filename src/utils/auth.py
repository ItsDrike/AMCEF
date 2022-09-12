import secrets
from enum import Enum
from typing import Optional, TypedDict, cast

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud, schemas
from src.constants import Server
from src.models import Member


class TokenData(TypedDict):
    id: int
    salt: str


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


async def validate_token(
    db_session: AsyncSession,
    token: Optional[str],
    *,
    needs_admin: bool = False,
) -> tuple[TokenData, Member]:
    """Check that given token meets specified criteria and matches our database.

    If some criteria will not be met, a 403 HTTPException will be raised. Otherwise, data from the token
    along with fetched member data from the database will be returned.
    """
    if token is None:
        raise HTTPException(403, AuthState.NO_TOKEN.value)

    try:
        token_data = cast(TokenData, jwt.decode(token, Server.JWT_SECRET))
    except JWTError:
        raise HTTPException(403, AuthState.INVALID_TOKEN.value)

    member = await crud.get_member(db_session, int(token_data["id"]))
    if member is None or member.ket_salt != token_data["salt"]:
        raise HTTPException(403, AuthState.INVALID_TOKEN.value)

    if needs_admin and not member.is_admin:
        raise HTTPException(403, AuthState.NEEDS_ADMIN.value)

    return token_data, member


class JWTBearer(HTTPBearer):
    """Dependency for routes to enforce JWT auth."""

    def __init__(self, auto_error: bool = True, require_admin: bool = False):
        super().__init__(auto_error=auto_error)
        self.require_admin = require_admin

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        """Check if the supplied credentials are valid for this endpoint."""
        credentials = cast(HTTPAuthorizationCredentials, await super().__call__(request))
        jwt_token = credentials.credentials
        db_session = request.state.db_session
        _, member = await validate_token(db_session, jwt_token, needs_admin=self.require_admin)

        # Token is valid, store the member_id and is_admin data into the request
        request.state.member_id = member.member_id
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
