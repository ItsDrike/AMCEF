from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response

from src import crud, models, schemas

router = APIRouter(tags=["User posts endpoints"])


@router.post("/post", response_model=schemas.Post)
async def create_post(request: Request, data: schemas.PostCreate) -> models.Post:
    db_session = request.state.db_session

    db_post = await crud.add_post(db_session, data)
    return db_post


@router.get("/post/{post_id}", response_model=schemas.Post)
async def get_post(request: Request, post_id: int) -> models.Post:
    db_session = request.state.db_session

    db_post = await crud.get_post(db_session, post_id)
    if not db_post:
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
