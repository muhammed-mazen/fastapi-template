from fastapi import APIRouter

from routes.user import router as users

api_router = APIRouter()

routers = [
    users
]

for router in routers:
    api_router.include_router(router)
