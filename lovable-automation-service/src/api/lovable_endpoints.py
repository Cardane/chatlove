"""
Additional API endpoints for Lovable integration
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..browser.lovable_client import LovableClient
from ..core.logging import get_logger

router = APIRouter(prefix="/api/lovable", tags=["lovable"])
logger = get_logger("lovable_api")

# Global client instance
_client: LovableClient = None

async def get_client() -> LovableClient:
    """Get or create Lovable client instance"""
    global _client
    if not _client:
        _client = LovableClient()
        await _client.start()
    return _client

@router.post("/login")
async def login(email: str, password: str):
    """Login to Lovable.dev"""
    try:
        client = await get_client()
        result = await client.login(email, password)
        return result
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects")
async def get_projects() -> List[Dict[str, Any]]:
    """Get list of user projects"""
    try:
        client = await get_client()
        if not client.is_logged_in:
            raise HTTPException(status_code=401, detail="Not logged in")
        
        projects = await client.get_projects()
        return projects
    except Exception as e:
        logger.error(f"Get projects error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/open")
async def open_project(project_id: str):
    """Open a specific project"""
    try:
        client = await get_client()
        if not client.is_logged_in:
            raise HTTPException(status_code=401, detail="Not logged in")
        
        success = await client.open_project(project_id)
        return {"success": success, "project_id": project_id}
    except Exception as e:
        logger.error(f"Open project error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/message")
async def send_project_message(project_id: str, message: str):
    """Send message to a specific project"""
    try:
        client = await get_client()
        if not client.is_logged_in:
            raise HTTPException(status_code=401, detail="Not logged in")
        
        # Open project if not current
        if client.current_project_id != project_id:
            await client.open_project(project_id)
        
        result = await client.send_message(message)
        return result
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_lovable_status():
    """Get current Lovable client status"""
    try:
        client = await get_client()
        status = await client.get_current_status()
        return status
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/screenshot")
async def take_screenshot():
    """Take screenshot of current page"""
    try:
        client = await get_client()
        if not client.is_logged_in:
            raise HTTPException(status_code=401, detail="Not logged in")
        
        screenshot = await client.take_screenshot()
        return {"screenshot_size": len(screenshot), "format": "png"}
    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
