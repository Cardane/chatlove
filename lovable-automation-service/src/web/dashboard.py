"""
Web Dashboard for Lovable Automation Service
"""

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from typing import Dict, Any

from ..core.logging import LoggerMixin


class DashboardManager(LoggerMixin):
    """Manages the web dashboard interface"""
    
    def __init__(self):
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.static_dir = os.path.join(os.path.dirname(__file__), "static")
        
        # Create directories if they don't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)
        
        self.templates = Jinja2Templates(directory=self.templates_dir)


def create_dashboard_app() -> FastAPI:
    """Create FastAPI app with dashboard routes"""
    
    dashboard = DashboardManager()
    
    # Create dashboard routes
    async def dashboard_home(request: Request):
        """Dashboard home page"""
        return dashboard.templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "Lovable Automation Service - Dashboard",
                "service_name": "Lovable Automation Service"
            }
        )
    
    async def dashboard_status(request: Request):
        """Dashboard status page"""
        # This would get real status from the service
        status_data = {
            "service_status": "running",
            "configured_accounts": 1,
            "active_sessions": 0,
            "queue_size": 0,
            "processed_messages": 0
        }
        
        return dashboard.templates.TemplateResponse(
            "status.html",
            {
                "request": request,
                "title": "System Status",
                "status": status_data
            }
        )
    
    async def dashboard_sessions(request: Request):
        """Dashboard sessions page"""
        return dashboard.templates.TemplateResponse(
            "sessions.html",
            {
                "request": request,
                "title": "Session Management",
                "sessions": []
            }
        )
    
    async def dashboard_logs(request: Request):
        """Dashboard logs page"""
        return dashboard.templates.TemplateResponse(
            "logs.html",
            {
                "request": request,
                "title": "System Logs",
                "logs": []
            }
        )
    
    async def chat_interface(request: Request):
        """Chat interface page"""
        return dashboard.templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "title": "ChatLove - Interface de Chat"
            }
        )
    
    # Return the routes
    return {
        "dashboard_home": dashboard_home,
        "dashboard_status": dashboard_status,
        "dashboard_sessions": dashboard_sessions,
        "dashboard_logs": dashboard_logs,
        "chat_interface": chat_interface,
        "templates": dashboard.templates,
        "static_dir": dashboard.static_dir
    }
