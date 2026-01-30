"""
Main entry point for Lovable Automation Service
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

from src.core.config import settings
from src.core.logging import setup_logging, get_logger
from src.core.exceptions import LovableAutomationError
from src.session.manager import LovableSessionManager
from src.models.message import ChatMessage
from src.models.response import ChatLoveResponse
from src.web.dashboard import create_dashboard_app
from src.api.lovable_endpoints import router as lovable_router


# Setup logging
setup_logging()
logger = get_logger("main")

# Global session manager
session_manager: LovableSessionManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global session_manager
    
    logger.info("Starting Lovable Automation Service")
    
    try:
        # Initialize session manager
        session_manager = LovableSessionManager()
        await session_manager.start()
        
        logger.info("Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start service: {str(e)}")
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down Lovable Automation Service")
        
        if session_manager:
            await session_manager.stop()
        
        logger.info("Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Lovable Automation Service",
    description="Automated Lovable.dev interaction service for ChatLove",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Setup dashboard
dashboard_routes = create_dashboard_app()
templates = dashboard_routes["templates"]

# Dashboard routes
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Dashboard home page"""
    return await dashboard_routes["dashboard_home"](request)

@app.get("/dashboard/status", response_class=HTMLResponse)
async def dashboard_status(request: Request):
    """Dashboard status page"""
    return await dashboard_routes["dashboard_status"](request)

@app.get("/dashboard/sessions", response_class=HTMLResponse)
async def dashboard_sessions(request: Request):
    """Dashboard sessions page"""
    return await dashboard_routes["dashboard_sessions"](request)

@app.get("/dashboard/logs", response_class=HTMLResponse)
async def dashboard_logs(request: Request):
    """Dashboard logs page"""
    return await dashboard_routes["dashboard_logs"](request)

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Chat interface page"""
    return await dashboard_routes["chat_interface"](request)

# Include Lovable API routes
app.include_router(lovable_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "lovable-automation-service",
        "version": "1.0.0"
    }


# Session manager status
@app.get("/status")
async def get_status():
    """Get service status and statistics"""
    if not session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = session_manager.get_stats()
    
    return {
        "service": "lovable-automation-service",
        "status": "running" if stats["is_running"] else "stopped",
        "stats": stats
    }


# Global Lovable client
lovable_client = None

# Process message endpoint
@app.post("/process-message")
async def process_message(message: ChatMessage):
    """Process a chat message through Lovable"""
    global lovable_client
    
    try:
        logger.info(
            "Processing message",
            message_id=message.id,
            user_id=message.user_id,
            project_id=message.project_id,
            content_length=len(message.content)
        )
        
        # Initialize Lovable client if needed
        if not lovable_client:
            from src.browser.lovable_client import LovableClient
            lovable_client = LovableClient()
            await lovable_client.start()
            
            # Login with configured account
            from src.core.config import get_lovable_accounts
            accounts = get_lovable_accounts()
            if accounts:
                account = accounts[0]
                login_result = await lovable_client.login(account["email"], account["password"])
                if not login_result["success"]:
                    return ChatLoveResponse.error(
                        message=f"Falha no login: {login_result['error']}",
                        error_code="LOGIN_ERROR"
                    )
        
        # Check if logged in
        if not lovable_client.is_logged_in:
            return ChatLoveResponse.error(
                message="Cliente não está logado no Lovable",
                error_code="NOT_LOGGED_IN"
            )
        
        # If project_id is provided, open the project
        if message.project_id and message.project_id != "chat-project":
            if lovable_client.current_project_id != message.project_id:
                project_opened = await lovable_client.open_project(message.project_id)
                if not project_opened:
                    return ChatLoveResponse.error(
                        message=f"Falha ao abrir projeto {message.project_id}",
                        error_code="PROJECT_ERROR"
                    )
        
        # Send message to Lovable
        result = await lovable_client.send_message(message.content)
        
        if result["success"]:
            # Extract response content
            response_content = "Mensagem enviada com sucesso!"
            code_blocks = []
            
            if "response" in result and result["response"]:
                response_data = result["response"]
                
                # Extract messages
                if "messages" in response_data and response_data["messages"]:
                    latest_message = response_data["messages"][-1]
                    if "content" in latest_message:
                        response_content = latest_message["content"]
                
                # Extract code blocks
                if "codeBlocks" in response_data and response_data["codeBlocks"]:
                    code_blocks = response_data["codeBlocks"]
            
            # Format code changes
            code_changes = None
            if code_blocks:
                code_changes = {
                    "files": [
                        {
                            "file_path": f"generated_code.{block.get('language', 'txt')}",
                            "content": block["content"],
                            "language": block.get("language", "text")
                        }
                        for block in code_blocks
                    ]
                }
            
            response = ChatLoveResponse(
                success=True,
                message="Mensagem processada com sucesso via Lovable real!",
                response_content=response_content,
                code_changes=code_changes,
                processing_time=1.0,
                session_id="lovable_session",
                tokens_saved=len(message.content) / 4
            )
            
            logger.info(
                "Message processed successfully via real Lovable",
                message_id=message.id,
                response_length=len(response_content),
                code_blocks_count=len(code_blocks)
            )
            
            return response
        else:
            return ChatLoveResponse.error(
                message=f"Erro do Lovable: {result.get('error', 'Erro desconhecido')}",
                error_code="LOVABLE_ERROR"
            )
    
    except Exception as e:
        logger.error(
            "Failed to process message",
            message_id=message.id,
            error=str(e)
        )
        
        return ChatLoveResponse.error(
            message=f"Erro ao processar mensagem: {str(e)}",
            error_code="PROCESSING_ERROR"
        )


# Session management endpoints
@app.get("/sessions")
async def get_sessions():
    """Get information about all sessions"""
    if not session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_report = session_manager.pool_manager.get_health_report()
    return health_report


@app.post("/sessions/health-check")
async def perform_health_check():
    """Perform health check on all sessions"""
    if not session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    results = await session_manager.pool_manager.perform_health_checks()
    return results


@app.post("/sessions/cleanup")
async def cleanup_sessions():
    """Cleanup expired sessions"""
    if not session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    removed_count = session_manager.pool_manager.cleanup_expired_sessions()
    
    return {
        "success": True,
        "removed_sessions": removed_count,
        "message": f"Cleaned up {removed_count} expired sessions"
    }


@app.post("/sessions/rebalance")
async def rebalance_sessions():
    """Rebalance load across sessions"""
    if not session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    session_manager.pool_manager.rebalance_load()
    
    return {
        "success": True,
        "message": "Session load rebalanced"
    }


# Error handlers
@app.exception_handler(LovableAutomationError)
async def automation_error_handler(request, exc: LovableAutomationError):
    """Handle automation-specific errors"""
    logger.error(
        "Automation error",
        error_type=type(exc).__name__,
        error_message=exc.message,
        error_code=exc.error_code,
        details=exc.details
    )
    
    return HTTPException(
        status_code=500,
        detail={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main function"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("LOVABLE AUTOMATION SERVICE")
    logger.info("=" * 60)
    logger.info(f"Host: {settings.api_host}")
    logger.info(f"Port: {settings.api_port}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Max Sessions: {settings.max_concurrent_sessions}")
    logger.info("=" * 60)
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=False  # Set to True for development
    )


if __name__ == "__main__":
    main()
