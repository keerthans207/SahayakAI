"""API v1 routers."""

from fastapi import APIRouter

from app.api.v1 import admin, applications, chat, documents, eligibility, health, schemes, speech

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(schemes.router, prefix="/schemes", tags=["schemes"])
api_router.include_router(eligibility.router, prefix="/eligibility", tags=["eligibility"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

__all__ = ["api_router"]
