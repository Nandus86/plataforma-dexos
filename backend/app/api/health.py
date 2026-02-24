"""
Health Check API
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/version")
async def get_version():
    """Get robust backend version string"""
    import os
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        version_file = os.path.join(current_dir, "VERSION")
        with open(version_file, "r") as f:
            version = f.read().strip()
    except Exception:
        version = "1.0.0"
        
    return {
        "version": version
    }
