import json
from typing import Annotated

from core.config import get_config
from db.session import get_async_session
from fastapi import Depends, HTTPException, status
from lib.auth import verify_password, oauth2_scheme, decode_access_token
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlmodel import select

config = get_config()


def has_reset_password(user: User) -> bool:
    """
    Checks if a user has reset their password.

    This function reads the users.json file and checks if the user's password matches the one in the file.
    If the user is not present in the file, it returns False.

    Args:
        user (User): The user to check.

    Returns:
        bool: True if the user has reset their password, False otherwise.
    """
    try:
        # read users.json and login with username
        with open(config.USERS_PATH) as f:
            users = json.load(f)
            password = users[user.username]
        return verify_password(password, user.password)
    except KeyError:
        return False


async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User).where(User.is_admin.is_(False)))
    return result.scalars().all()

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[AsyncSession, Depends(get_async_session)]
):
    # Decode the access token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    result = await session.execute(select(User).filter(User.id == int(user_id)))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
