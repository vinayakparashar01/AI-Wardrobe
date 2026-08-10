from typing import Annotated

from app.core.auth import CurrentUser
from app.core.security import hash_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DBSession = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter(
    prefix="/user",
    tags=["Users"],
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user: UserCreate,
    db: DBSession,
):
    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.get(
    "/",
    response_model=list[UserResponse],
)
async def get_users(
    db: DBSession,
):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_current_user(
    current_user: CurrentUser,
):
    return current_user
