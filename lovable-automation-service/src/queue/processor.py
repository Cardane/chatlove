"""
Message Processor for Lovable Automation Service
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..core.logging import LoggerMixin, log_queue_event
from ..core.exceptions import MessageProcessingError, SessionPoolExhaustedError
from ..models.message import ChatMessage, MessageStatus
from ..models.response import ChatLoveResponse
from ..session.manager import LovableSessionManager
from ..browser.automation import LovableBrowserAutomation


class MessageProcessor(LoggerMixin):
    """
    Processes messages through browser automation
    """
    
    def __init__(self, session_manager: LovableSessionManager, browser_automation: LovableBrowserAutomation):
        self.session_manager = session_manager
        self.browser_automation = browser_automation
        self.processing_tasks: Dict[str, asyncio.Task] = {}
    
    async def process_message(self, message: ChatMessage) -> ChatLoveResponse:
        """Process a single message"""
        try:
            self.logger.info(f"Processing message: {message.id}")
            
            # Get active session
            async with self.session_manager.get_session_context() as session:
                # Mark message as processing
                message.mark_processing(session.id)
                
                # Navigate to project
                page = await self.browser_automation.navigate_to_project(session, message.project_id)
                
                # Handle authentication if needed
                if not await self.browser_automation.handle_authentication(page, session):
                    raise MessageProcessingError("Authentication failed")
                
                # Send message and get response
                lovable_response = await self.browser_automation.send_chat_message(page, message)
                
                # Check for errors
                error_message = await self.browser_automation.check_for_errors(page)
                if error_message:
                    raise MessageProcessingError(f"Lovable error: {error_message}")
                
                # Convert to ChatLove response
                tokens_saved = len(message.content) / 4  # Estimate
                response = ChatLoveResponse.from_lovable_response(lovable_response, tokens_saved)
                
                # Mark message as completed
                message.mark_completed()
                
                # Update session usage
                session.increment_message_count()
                
                self.logger.info(f"Message processed successfully: {message.id}")
                
                return response
        
        except Exception as e:
            self.logger.error(f"Failed to process message {message.id}: {str(e)}")
            
            # Mark message as failed
            message.mark_failed(str(e))
            
            # Return error response
            return ChatLoveResponse.error(
                message=f"Erro ao processar mensagem: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    async def process_message_async(self, message: ChatMessage) -> str:
        """Process message asynchronously and return task ID"""
        task_id = str(uuid.uuid4())
        
        # Create processing task
        task = asyncio.create_task(self._process_message_task(message, task_id))
        self.processing_tasks[task_id] = task
        
        log_queue_event("async_processing_started", message.id, task_id=task_id)
        
        return task_id
    
    async def _process_message_task(self, message: ChatMessage, task_id: str) -> None:
        """Internal task for processing message"""
        try:
            response = await self.process_message(message)
            
            # Store result (could be in Redis or database)
            # For now, just log completion
            log_queue_event(
                "async_processing_completed",
                message.id,
                task_id=task_id,
                success=response.success
            )
        
        except Exception as e:
            self.logger.error(f"Async processing failed for {message.id}: {str(e)}")
            log_queue_event(
                "async_processing_failed",
                message.id,
                task_id=task_id,
                error=str(e)
            )
        
        finally:
            # Remove task from tracking
            if task_id in self.processing_tasks:
                del self.processing_tasks[task_id]
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of processing task"""
        if task_id not in self.processing_tasks:
            return {"status": "not_found"}
        
        task = self.processing_tasks[task_id]
        
        if task.done():
            if task.exception():
                return {
                    "status": "failed",
                    "error": str(task.exception())
                }
            else:
                return {"status": "completed"}
        else:
            return {"status": "processing"}
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a processing task"""
        if task_id not in self.processing_tasks:
            return False
        
        task = self.processing_tasks[task_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.processing_tasks[task_id]
        
        log_queue_event("async_processing_cancelled", "unknown", task_id=task_id)
        
        return True
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        active_tasks = len(self.processing_tasks)
        
        # Count tasks by status
        completed_tasks = 0
        failed_tasks = 0
        processing_tasks = 0
        
        for task in self.processing_tasks.values():
            if task.done():
                if task.exception():
                    failed_tasks += 1
                else:
                    completed_tasks += 1
            else:
                processing_tasks += 1
        
        return {
            "active_tasks": active_tasks,
            "processing_tasks": processing_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks
        }
    
    async def cleanup_completed_tasks(self) -> int:
        """Cleanup completed tasks and return count"""
        completed_tasks = []
        
        for task_id, task in self.processing_tasks.items():
            if task.done():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.processing_tasks[task_id]
        
        return len(completed_tasks)
