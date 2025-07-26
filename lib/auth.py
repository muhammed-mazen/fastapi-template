import asyncio
from datetime import timedelta, datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient, ASGITransport, Auth

from core.config import get_config
from jose import jwt, JWTError
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

config = get_config()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def verify_password_async(plain_password, hashed_password):
    return await asyncio.to_thread(pwd_context.verify, plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)


# JWT Token Creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=config.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.ALGORITHM])
        return payload
    except JWTError:
        return None


class JWTAuth(Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


async def get_client(app: FastAPI):
    return AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    )


async def get_admin_client(app: FastAPI):
    return AsyncClient(
        auth=JWTAuth(create_access_token(data={"sub": str(1)})),
        transport=ASGITransport(app=app),
        base_url="http://test"
    )


async def get_user_client(app: FastAPI):
    return AsyncClient(
        auth=JWTAuth(create_access_token(data={"sub": str(2)})),
        transport=ASGITransport(app=app),
        base_url="http://test"
    )
