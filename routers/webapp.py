from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

@router.get("/webapp")
async def serve_webapp():
    """Serve o Mini App HTML"""
    file_path = Path("static/index.html")
    if file_path.exists():
        return FileResponse(file_path)
    return {"error": "Web app not found"}, 404

