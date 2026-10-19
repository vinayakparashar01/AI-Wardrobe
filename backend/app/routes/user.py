from fastapi import APIRouter, status

from app.core.auth import CurrentUser, DBSession
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user as create_user_service
from app.services.user_service import get_users as get_users_service

router = APIRouter(prefix="/user", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user: UserCreate,
    db: DBSession,
):
    return await create_user_service(user, db)


@router.get("/", response_model=list[UserResponse])
async def get_users(db: DBSession):
    return await get_users_service(db)


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):  # type:ignore
    return current_user
