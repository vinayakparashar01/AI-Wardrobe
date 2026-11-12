from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


async def create_user(user: UserCreate, db: AsyncSession) -> User:
    normalized_email = user.email.lower().strip()

    # Pre-check for existing user by email
    existing_result = await db.execute(
        select(User).where(User.email == normalized_email)
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered. Please log in or use another email.",
        )

    new_user = User(
        name=user.name.strip(),
        email=normalized_email,
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered. Please log in or use another email.",
        ) from exc
    except Exception:
        await db.rollback()
        raise

    return new_user


async def get_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User))
    return list(result.scalars().all())
