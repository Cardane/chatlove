"""
Network interceptor for capturing Lovable API responses
"""

import json
import re
from typing import Optional, Dict, Any, List, Callable
from playwright.async_api import Page, Response, Request
from datetime import datetime

from ..core.logging import LoggerMixin
from ..models.response import LovableResponse, StreamingChunk, StreamingChunkType, CodeChanges, FileChange


class NetworkInterceptor(LoggerMixin):
    """
    Intercepts network traffic to capture Lovable API responses
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.response_capture: Optional[LovableResponse] = None
        self.streaming_buffer = ""
        self.chunk_sequence = 0
        
        # API endpoints to intercept
        self.api_patterns = [
            r"https://api\.lovable\.dev/projects/.+/chat",
            r"https://lovable\.dev/api/projects/.+/chat",
            r"https://.*\.lovable\.dev/.*chat.*",
            r"https://.*\.lovable\.dev/.*stream.*"
        ]
        
        # Response handlers
        self.response_handlers: Dict[str, Callable] = {
            "chat": self._handle_chat_response,
            "stream": self._handle_streaming_response,
            "error": self._handle_error_response
        }
    
    async def start(self) -> None:
        """Start intercepting network traffic"""
        try:
            # Intercept responses
            self.page.on("response", self._on_response)
            
            # Intercept requests (optional, for debugging)
            self.page.on("request", self._on_request)
            
            self.logger.debug("Network interceptor started")
            
        except Exception as e:
            self.logger.error(f"Failed to start network interceptor: {str(e)}")
    
    def setup_response_capture(self, response: LovableResponse) -> None:
        """Setup response capture for a specific response object"""
        self.response_capture = response
        self.streaming_buffer = ""
        self.chunk_sequence = 0
        
        self.logger.debug(f"Response capture setup for message: {response.message_id}")
    
    async def _on_request(self, request: Request) -> None:
        """Handle intercepted requests"""
        try:
            url = request.url
            
            # Check if this is a Lovable API request
            if self._is_lovable_api_request(url):
                self.logger.debug(f"Intercepted request: {request.method} {url}")
                
                # Log request payload for debugging
                if request.method == "POST":
                    try:
                        post_data = request.post_data
                        if post_data:
                            self.logger.debug(f"Request payload: {post_data[:500]}...")
                    except:
                        pass
        
        except Exception as e:
            self.logger.error(f"Error handling request: {str(e)}")
    
    async def _on_response(self, response: Response) -> None:
        """Handle intercepted responses"""
        try:
            url = response.url
            
            # Check if this is a Lovable API response
            if self._is_lovable_api_response(url):
                self.logger.debug(f"Intercepted response: {response.status} {url}")
                
                # Determine response type
                response_type = self._determine_response_type(url, response)
                
                # Handle based on type
                handler = self.response_handlers.get(response_type, self._handle_generic_response)
                await handler(response)
        
        except Exception as e:
            self.logger.error(f"Error handling response: {str(e)}")
    
    def _is_lovable_api_request(self, url: str) -> bool:
        """Check if URL matches Lovable API patterns"""
        return any(re.match(pattern, url) for pattern in self.api_patterns)
    
    def _is_lovable_api_response(self, url: str) -> bool:
        """Check if response URL matches Lovable API patterns"""
        return self._is_lovable_api_request(url)
    
    def _determine_response_type(self, url: str, response: Response) -> str:
        """Determine the type of response based on URL and headers"""
        content_type = response.headers.get("content-type", "").lower()
        
        # Check for streaming responses
        if "text/stream" in content_type or "application/stream" in content_type:
            return "stream"
        
        # Check for chat endpoints
        if "/chat" in url:
            return "chat"
        
        # Check for error status codes
        if response.status >= 400:
            return "error"
        
        return "generic"
    
    async def _handle_chat_response(self, response: Response) -> None:
        """Handle chat API responses"""
        try:
            if not self.response_capture:
                return
            
            # Get response body
            response_text = await response.text()
            
            if not response_text:
                return
            
            self.logger.debug(f"Chat response received: {len(response_text)} characters")
            
            # Try to parse as JSON
            try:
                response_data = json.loads(response_text)
                await self._process_json_response(response_data)
            except json.JSONDecodeError:
                # Handle as plain text or streaming data
                await self._process_text_response(response_text)
        
        except Exception as e:
            self.logger.error(f"Error handling chat response: {str(e)}")
    
    async def _handle_streaming_response(self, response: Response) -> None:
        """Handle streaming API responses"""
        try:
            if not self.response_capture:
                return
            
            # Mark as streaming
            self.response_capture.is_streaming = True
            
            # Get response body
            response_text = await response.text()
            
            if response_text:
                await self._process_streaming_data(response_text)
        
        except Exception as e:
            self.logger.error(f"Error handling streaming response: {str(e)}")
    
    async def _handle_error_response(self, response: Response) -> None:
        """Handle error responses"""
        try:
            if not self.response_capture:
                return
            
            error_text = await response.text()
            
            # Try to parse error details
            error_message = f"HTTP {response.status}"
            error_code = str(response.status)
            
            try:
                error_data = json.loads(error_text)
                if isinstance(error_data, dict):
                    error_message = error_data.get("message", error_message)
                    error_code = error_data.get("code", error_code)
            except:
                if error_text:
                    error_message = error_text[:200]  # Truncate long error messages
            
            # Mark response as error
            self.response_capture.mark_error(error_message, error_code)
            
            self.logger.error(f"API error response: {error_message}")
        
        except Exception as e:
            self.logger.error(f"Error handling error response: {str(e)}")
    
    async def _handle_generic_response(self, response: Response) -> None:
        """Handle generic responses"""
        try:
            if not self.response_capture:
                return
            
            response_text = await response.text()
            
            if response_text:
                # Try to extract useful information
                try:
                    response_data = json.loads(response_text)
                    await self._process_json_response(response_data)
                except:
                    await self._process_text_response(response_text)
        
        except Exception as e:
            self.logger.error(f"Error handling generic response: {str(e)}")
    
    async def _process_json_response(self, data: Dict[str, Any]) -> None:
        """Process JSON response data"""
        try:
            if not self.response_capture:
                return
            
            # Extract AI message ID
            if "ai_message_id" in data:
                self.response_capture.ai_message_id = data["ai_message_id"]
            
            # Extract content
            if "content" in data:
                self.response_capture.content = data["content"]
            
            # Extract code changes
            if "code_changes" in data or "files" in data:
                code_changes = await self._extract_code_changes(data)
                if code_changes:
                    self.response_capture.code_changes = code_changes
            
            # Extract metadata
            if "model" in data:
                self.response_capture.model_used = data["model"]
            
            if "tokens" in data:
                self.response_capture.tokens_used = data["tokens"]
            
            self.logger.debug("JSON response processed successfully")
        
        except Exception as e:
            self.logger.error(f"Error processing JSON response: {str(e)}")
    
    async def _process_text_response(self, text: str) -> None:
        """Process plain text response"""
        try:
            if not self.response_capture:
                return
            
            # Add to content
            if not self.response_capture.content:
                self.response_capture.content = text
            else:
                self.response_capture.content += text
            
            self.logger.debug(f"Text response processed: {len(text)} characters")
        
        except Exception as e:
            self.logger.error(f"Error processing text response: {str(e)}")
    
    async def _process_streaming_data(self, data: str) -> None:
        """Process streaming response data"""
        try:
            if not self.response_capture:
                return
            
            # Add to streaming buffer
            self.streaming_buffer += data
            
            # Try to extract complete chunks
            chunks = self._extract_streaming_chunks(self.streaming_buffer)
            
            for chunk_data in chunks:
                chunk = StreamingChunk(
                    id=f"chunk_{self.chunk_sequence}",
                    type=self._determine_chunk_type(chunk_data),
                    content=chunk_data,
                    sequence=self.chunk_sequence,
                    timestamp=datetime.utcnow()
                )
                
                self.response_capture.add_streaming_chunk(chunk)
                self.chunk_sequence += 1
            
            # Check for completion markers
            if self._is_streaming_complete(data):
                self.response_capture.mark_streaming_complete()
        
        except Exception as e:
            self.logger.error(f"Error processing streaming data: {str(e)}")
    
    def _extract_streaming_chunks(self, buffer: str) -> List[str]:
        """Extract complete chunks from streaming buffer"""
        chunks = []
        
        # Common streaming formats
        patterns = [
            r"data: ({.*?})\n\n",  # Server-sent events
            r"({.*?})\n",          # JSON lines
            r"chunk: (.*?)\n",     # Custom chunk format
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, buffer, re.DOTALL)
            if matches:
                chunks.extend(matches)
                # Remove processed chunks from buffer
                for match in matches:
                    buffer = buffer.replace(match, "", 1)
        
        # Update buffer
        self.streaming_buffer = buffer
        
        return chunks
    
    def _determine_chunk_type(self, chunk_data: str) -> StreamingChunkType:
        """Determine the type of streaming chunk"""
        try:
            # Try to parse as JSON
            data = json.loads(chunk_data)
            
            if isinstance(data, dict):
                # Check for specific fields
                if "code" in data or "file" in data:
                    return StreamingChunkType.CODE
                elif "error" in data:
                    return StreamingChunkType.ERROR
                elif "complete" in data or "done" in data:
                    return StreamingChunkType.COMPLETE
                elif "metadata" in data:
                    return StreamingChunkType.METADATA
            
            return StreamingChunkType.TEXT
        
        except:
            # Check for code patterns in text
            if any(keyword in chunk_data.lower() for keyword in ["function", "class", "import", "export"]):
                return StreamingChunkType.CODE
            
            return StreamingChunkType.TEXT
    
    def _is_streaming_complete(self, data: str) -> bool:
        """Check if streaming is complete"""
        completion_markers = [
            "[DONE]",
            "data: [DONE]",
            '"complete": true',
            '"done": true',
            "stream_end"
        ]
        
        return any(marker in data for marker in completion_markers)
    
    async def _extract_code_changes(self, data: Dict[str, Any]) -> Optional[CodeChanges]:
        """Extract code changes from response data"""
        try:
            code_changes = CodeChanges()
            
            # Look for file changes in various formats
            files_data = data.get("files", [])
            if not files_data:
                files_data = data.get("code_changes", {}).get("files", [])
            
            for file_data in files_data:
                if isinstance(file_data, dict):
                    file_change = FileChange(
                        file_path=file_data.get("path", file_data.get("file_path", "")),
                        action=file_data.get("action", "update"),
                        content=file_data.get("content"),
                        diff=file_data.get("diff")
                    )
                    
                    code_changes.add_file_change(file_change)
            
            # Extract summary if available
            if "summary" in data:
                code_changes.summary = data["summary"]
            
            return code_changes if code_changes.files else None
        
        except Exception as e:
            self.logger.error(f"Error extracting code changes: {str(e)}")
            return None
    
    def get_captured_data(self) -> Optional[Dict[str, Any]]:
        """Get all captured data for debugging"""
        if not self.response_capture:
            return None
        
        return {
            "message_id": self.response_capture.message_id,
            "ai_message_id": self.response_capture.ai_message_id,
            "content": self.response_capture.content,
            "streaming_chunks_count": len(self.response_capture.streaming_chunks),
            "is_streaming": self.response_capture.is_streaming,
            "is_streaming_complete": self.response_capture.is_streaming_complete,
            "success": self.response_capture.success,
            "error_message": self.response_capture.error_message
        }
