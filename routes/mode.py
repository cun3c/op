from fastapi import APIRouter
from config import settings

router = APIRouter()

@router.get("/")
async def get_mode():
    return {"mode": settings.MODE}

@router.post("/switch")
async def switch_mode(payload: dict):
    if payload.get("mode") in ["live", "demo"]:
        settings.MODE = payload["mode"]
        return {"status": "switched", "new_mode": settings.MODE}
    return {"status": "error", "message": "Invalid mode"}
