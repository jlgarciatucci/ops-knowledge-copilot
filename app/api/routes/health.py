from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    return {
        "status": "ok",
        "api": "running",
        "message": "Health endpoint is alive. Database connectivity is checked during app startup."
    }