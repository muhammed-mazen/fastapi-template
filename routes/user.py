import asyncio
from typing import List

from fastapi import APIRouter
from fastapi_cache.decorator import cache
from sqlmodel import select
from core.config import get_config
from db.session import get_async_session
from lib.auth import verify_password, create_access_token, hash_password, verify_password_async
from lib.utils import create_bulk_users
from models.user import User, Profile
from schemas.user import Token, ProfileResponse, ProfileUpdateRequest, UserResponse, LoginRequest, NewUser
from services.user import get_current_user, get_all_users

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from fastapi import HTTPException, status, Depends

router = APIRouter()
config = get_config()


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_async_session)):
    username, password = request.username, request.password
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    is_valid = await verify_password_async(password, user.password) if user else False

    if not is_valid:
        # Add a small delay to prevent brute-force attacks
        await asyncio.sleep(0.5)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid username or password")

    return Token(
        access_token=create_access_token(data={"sub": str(user.id)}),
        token_type="bearer",
        username=user.username,
        is_admin=user.is_admin,
        is_view=False,  # TODO: ADD is_view
        has_password_reset=user.has_password_reset or False,
        is_akg=user.is_akg or False
    )


# Password Reset
@router.post("/reset_password", response_model=str, tags=["User"])
async def reset_password(
        new_password: str,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
):
    if not current_user.has_password_reset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Password has already been reset")

    current_user.password = hash_password(new_password)
    current_user.has_password_reset = False
    session.add(current_user)
    await session.commit()

    return {"msg": "Password reset successfully"}


@router.put("/profile", response_model=ProfileResponse, tags=["User"])
async def update_profile(
        profile_data: ProfileUpdateRequest,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
):
    # Fetch user profile
    result = await session.execute(select(Profile).where(Profile.user_id == current_user.id))
    profile = result.scalars().first()

    profile_data_dict = profile_data.dict(
        exclude_none=True)  # Remove None values
    current_password = profile_data_dict.pop("current_password", None)
    new_password = profile_data_dict.pop("new_password", None)

    if current_user.has_password_reset and new_password:
        current_user.password = hash_password(new_password)
        current_user.has_password_reset = False
        session.add(current_user)
    elif new_password:
        if not current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="current_password_required")
        if not verify_password(current_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="incorrect_current_password")
        current_user.password = hash_password(new_password)
        session.add(current_user)

    # Update or create profile
    if profile:
        for key, value in profile_data_dict.items():
            setattr(profile, key, value)
    else:
        profile = Profile(user_id=current_user.id, **profile_data_dict)
        session.add(profile)

    await session.commit()
    await session.refresh(profile)
    return ProfileResponse(**profile.dict())


@router.get("/akg", response_model=ProfileResponse, tags=["User"])
async def update_akg(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
):
    if current_user.is_akg:
        if not current_user.profile:
            raise HTTPException(
                status_code=404, detail="User profile not found")
        # Return existing profile
        return ProfileResponse(**current_user.profile.model_dump(mode="json"))

    current_user.is_akg = True
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    if not current_user.profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    return ProfileResponse(**current_user.profile.model_dump(mode="json"))


@cache(expire=60)
@router.get("/all_users", response_model=List[UserResponse], tags=["User"])
async def all_users(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    users = await get_all_users(session)
    return [UserResponse(**user.model_dump(mode="json")) for user in users]


@cache(expire=60)
@router.get("/me", response_model=UserResponse, tags=["User"])
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        **current_user.model_dump(mode="json"),
        profile=ProfileResponse(
            **current_user.profile.model_dump(mode="json")) if current_user.profile else None
    )


@router.get("/bulk_users/{user_count}", response_model=List[NewUser], tags=["User"])
async def bulk_users(
        *,
        user_count: int,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if user_count <= 0 or user_count > config.MAX_USERS_PER_REQUEST:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"User count must be between 1 and {config.MAX_USERS_PER_REQUEST}")

    return await create_bulk_users(user_count, session)


@router.post("/users/{username}/block", tags=["User"])
async def block_user(
        *,
        username: str,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Fetch user (case-insensitive)
    result = await session.execute(select(User).where(User.username.ilike(username)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot block/unblock an admin user")

    user.is_active = not user.is_active
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return {"success": True, "message": f"User {username} {'unblocked' if user.is_active else 'blocked'} successfully"}
