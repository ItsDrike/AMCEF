import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response

from src import crud, models, schemas
from src.constants import Server
from src.utils.auth import JWTBearer, generate_member

log = logging.getLogger(__name__)

router = APIRouter(
    tags=["Admin-only endpoints"],
    include_in_schema=Server.SHOW_ADMIN_ENDPOINTS,
    dependencies=[Depends(JWTBearer(require_admin=True))],
)


@router.get("/admin")
async def admin_check(request: Request) -> Response:
    """Check if the authenticated member is an admin."""
    return Response("You're an admin!")


@router.get("/member/{member_id}", response_model=schemas.MemberData)
async def get_member(request: Request, member_id: int) -> models.Member:
    """Obtain info about member with given `member_id`."""
    db_session = request.state.db_session

    member = await crud.get_member(db_session, member_id)
    if not member:
        raise HTTPException(404, "No such member")
    return member


@router.post("/member")
async def add_member(request: Request, is_admin: bool) -> schemas.TokenMemberData:
    """Create a new member."""
    db_session = request.state.db_session

    member = await generate_member(db_session, is_admin=is_admin)
    return member


@router.patch("/member/{member_id}", response_model=schemas.MemberData)
async def update_member(request: Request, member_id: int, is_admin: bool) -> models.Member:
    """Update admin status of a member."""
    db_session = request.state.db_session

    db_member = await crud.update_member(db_session, member_id, is_admin=is_admin)
    if not db_member:
        raise HTTPException(404, "No such member")
    return db_member


@router.delete("/member/{member_id}")
async def remove_member(request: Request, member_id: int) -> Response:
    """Remove member with given `member_id`."""
    db_session = request.state.db_session

    status = await crud.delete_member(db_session, member_id)
    if status is False:
        raise HTTPException(404, "No such member")
    return Response(status_code=200)
