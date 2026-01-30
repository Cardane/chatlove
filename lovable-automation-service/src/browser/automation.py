"""
Browser automation for Lovable.dev using Playwright
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response
from datetime import datetime

from ..core.config import settings, get_browser_config
from ..core.exceptions import (
    BrowserError, BrowserLaunchError, NavigationError, 
    ElementNotFoundError, InterceptionError
)
from ..core.logging import LoggerMixin, log_browser_event
from ..models.session import Session
from ..models.message import ChatMessage
from ..models.response import LovableResponse, StreamingChunk, StreamingChunkType
from .selectors import LovableSelectors, LovableXPathSelectors, SelectorValidator
from .interceptor import NetworkInterceptor


class LovableBrowserAutomation(LoggerMixin):
    """
    Handles browser automation for Lovable.dev interactions
    """
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.interceptors: Dict[str, NetworkInterceptor] = {}
        self.selectors = LovableSelectors()
        self.xpath_selectors = LovableXPathSelectors()
        
    async def start(self) -> None:
        """Initialize Playwright and launch browser"""
        try:
            self.logger.info("Starting browser automation")
            
            # Launch Playwright
            self.playwright = await async_playwright().start()
            
            # Get browser config
            browser_config = get_browser_config()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=browser_config["headless"],
                args=browser_config["args"]
            )
            
            self.logger.info("Browser automation started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start browser automation: {str(e)}")
            raise BrowserLaunchError(f"Failed to launch browser: {str(e)}")
    
    async def stop(self) -> None:
        """Stop browser automation and cleanup"""
        try:
            self.logger.info("Stopping browser automation")
            
            # Close all pages and contexts
            for page in self.pages.values():
                if not page.is_closed():
                    await page.close()
            
            for context in self.contexts.values():
                await context.close()
            
            # Close browser
            if self.browser:
                await self.browser.close()
            
            # Stop Playwright
            if self.playwright:
                await self.playwright.stop()
            
            self.logger.info("Browser automation stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping browser automation: {str(e)}")
    
    async def create_session_context(self, session: Session) -> BrowserContext:
        """Create a browser context for a session"""
        try:
            context_id = f"session_{session.id}"
            
            # Create new context
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )
            
            # Set session cookies if available
            if session.session_cookies:
                cookies = []
                for name, value in session.session_cookies.items():
                    cookies.append({
                        "name": name,
                        "value": value,
                        "domain": ".lovable.dev",
                        "path": "/"
                    })
                await context.add_cookies(cookies)
            
            self.contexts[context_id] = context
            session.browser_context_id = context_id
            
            log_browser_event("context_created", context_id, session_id=session.id)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to create browser context: {str(e)}")
            raise BrowserError(f"Failed to create browser context: {str(e)}")
    
    async def navigate_to_project(self, session: Session, project_id: str) -> Page:
        """Navigate to a Lovable project"""
        try:
            # Get or create context
            context_id = session.browser_context_id
            if not context_id or context_id not in self.contexts:
                context = await self.create_session_context(session)
            else:
                context = self.contexts[context_id]
            
            # Create new page
            page = await context.new_page()
            page_id = f"page_{uuid.uuid4()}"
            self.pages[page_id] = page
            
            # Setup network interceptor
            interceptor = NetworkInterceptor(page)
            await interceptor.start()
            self.interceptors[page_id] = interceptor
            
            # Navigate to project
            project_url = f"{settings.lovable_web_url}/projects/{project_id}"
            
            log_browser_event("navigating", page_id, url=project_url, session_id=session.id)
            
            response = await page.goto(project_url, wait_until="networkidle")
            
            if not response or response.status >= 400:
                raise NavigationError(f"Failed to navigate to project: HTTP {response.status if response else 'No response'}")
            
            # Wait for page to load
            await self._wait_for_page_load(page)
            
            # Update session
            session.page_url = project_url
            
            log_browser_event("navigated", page_id, url=project_url, session_id=session.id)
            
            return page
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to project: {str(e)}")
            raise NavigationError(f"Failed to navigate to project: {str(e)}")
    
    async def send_chat_message(self, page: Page, message: ChatMessage) -> LovableResponse:
        """Send a chat message and capture the response"""
        try:
            self.logger.info(f"Sending chat message: {message.content[:100]}...")
            
            # Find chat input
            chat_input = await self._find_chat_input(page)
            if not chat_input:
                raise ElementNotFoundError("Chat input not found")
            
            # Clear and type message
            await chat_input.clear()
            await chat_input.type(message.content)
            
            # Find and click send button
            send_button = await self._find_send_button(page)
            if not send_button:
                raise ElementNotFoundError("Send button not found")
            
            # Setup response capture
            response = LovableResponse(message_id=message.id)
            
            # Get interceptor for this page
            page_id = self._get_page_id(page)
            interceptor = self.interceptors.get(page_id)
            
            if interceptor:
                # Setup response capture
                interceptor.setup_response_capture(response)
            
            # Click send button
            await send_button.click()
            
            # Wait for response
            await self._wait_for_response(page, response)
            
            self.logger.info(f"Message sent successfully, response received")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to send chat message: {str(e)}")
            raise BrowserError(f"Failed to send chat message: {str(e)}")
    
    async def _find_chat_input(self, page: Page) -> Optional[Any]:
        """Find chat input element with fallback selectors"""
        selectors = self.selectors.get_chat_input_selectors()
        
        for selector in selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element and await element.is_visible():
                    return element
            except:
                continue
        
        # Try XPath selector
        try:
            element = await page.wait_for_selector(
                f"xpath={self.xpath_selectors.CHAT_INPUT_BY_PLACEHOLDER}", 
                timeout=5000
            )
            if element and await element.is_visible():
                return element
        except:
            pass
        
        return None
    
    async def _find_send_button(self, page: Page) -> Optional[Any]:
        """Find send button element with fallback selectors"""
        selectors = self.selectors.get_send_button_selectors()
        
        for selector in selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element and await element.is_visible() and await element.is_enabled():
                    return element
            except:
                continue
        
        # Try XPath selector
        try:
            element = await page.wait_for_selector(
                f"xpath={self.xpath_selectors.SEND_BUTTON_BY_TEXT}", 
                timeout=5000
            )
            if element and await element.is_visible() and await element.is_enabled():
                return element
        except:
            pass
        
        return None
    
    async def _wait_for_page_load(self, page: Page) -> None:
        """Wait for page to fully load"""
        try:
            # Wait for network to be idle
            await page.wait_for_load_state("networkidle")
            
            # Wait for common elements to be present
            selectors_to_check = [
                self.selectors.CHAT_CONTAINER,
                self.selectors.CHAT_INPUT,
                "body"  # Fallback
            ]
            
            for selector in selectors_to_check:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    break
                except:
                    continue
            
        except Exception as e:
            self.logger.warning(f"Page load wait completed with warnings: {str(e)}")
    
    async def _wait_for_response(self, page: Page, response: LovableResponse, timeout: int = 60) -> None:
        """Wait for AI response to complete"""
        try:
            start_time = datetime.utcnow()
            
            # Wait for loading indicators to appear and disappear
            loading_selectors = self.selectors.get_loading_selectors()
            
            # First, wait for loading to start (optional)
            for selector in loading_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    self.logger.debug(f"Loading indicator appeared: {selector}")
                    break
                except:
                    continue
            
            # Then wait for loading to finish
            for selector in loading_selectors:
                try:
                    await page.wait_for_selector(selector, state="hidden", timeout=timeout * 1000)
                    self.logger.debug(f"Loading indicator disappeared: {selector}")
                except:
                    continue
            
            # Wait for new message to appear
            try:
                await page.wait_for_selector(
                    f"xpath={self.xpath_selectors.LAST_AI_MESSAGE}",
                    timeout=timeout * 1000
                )
            except:
                self.logger.warning("Could not detect new AI message")
            
            # Mark response as complete
            response.mark_complete()
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            response.processing_time = processing_time
            
            self.logger.info(f"Response completed in {processing_time:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error waiting for response: {str(e)}")
            response.mark_error(f"Timeout waiting for response: {str(e)}")
    
    async def extract_generated_code(self, page: Page) -> Dict[str, Any]:
        """Extract generated code changes from the page"""
        try:
            code_changes = {}
            
            # Try to extract from file tree or code editor
            # This would need to be implemented based on Lovable's actual UI
            
            # For now, return empty changes
            return code_changes
            
        except Exception as e:
            self.logger.error(f"Failed to extract generated code: {str(e)}")
            return {}
    
    async def handle_authentication(self, page: Page, session: Session) -> bool:
        """Handle authentication if needed"""
        try:
            # Check if already authenticated
            current_url = page.url
            if "/login" not in current_url and "/auth" not in current_url:
                return True
            
            # Find login form elements
            email_input = await page.wait_for_selector(self.selectors.LOGIN_EMAIL_INPUT, timeout=10000)
            password_input = await page.wait_for_selector(self.selectors.LOGIN_PASSWORD_INPUT, timeout=5000)
            submit_button = await page.wait_for_selector(self.selectors.LOGIN_SUBMIT_BUTTON, timeout=5000)
            
            if not all([email_input, password_input, submit_button]):
                raise ElementNotFoundError("Login form elements not found")
            
            # Fill login form
            await email_input.fill(session.account.email)
            await password_input.fill(session.account.password)
            
            # Submit form
            await submit_button.click()
            
            # Wait for navigation
            await page.wait_for_url(lambda url: "/login" not in url and "/auth" not in url, timeout=30000)
            
            self.logger.info("Authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False
    
    async def check_for_errors(self, page: Page) -> Optional[str]:
        """Check for error messages on the page"""
        try:
            error_selectors = self.selectors.get_error_selectors()
            
            for selector in error_selectors:
                try:
                    error_element = await page.query_selector(selector)
                    if error_element and await error_element.is_visible():
                        error_text = await error_element.text_content()
                        if error_text and error_text.strip():
                            return error_text.strip()
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for page errors: {str(e)}")
            return None
    
    def _get_page_id(self, page: Page) -> Optional[str]:
        """Get page ID from internal mapping"""
        for page_id, stored_page in self.pages.items():
            if stored_page == page:
                return page_id
        return None
    
    async def cleanup_session_resources(self, session: Session) -> None:
        """Cleanup browser resources for a session"""
        try:
            context_id = session.browser_context_id
            if not context_id:
                return
            
            # Close pages associated with this context
            pages_to_remove = []
            for page_id, page in self.pages.items():
                if page.context == self.contexts.get(context_id):
                    if not page.is_closed():
                        await page.close()
                    pages_to_remove.append(page_id)
            
            # Remove pages from tracking
            for page_id in pages_to_remove:
                del self.pages[page_id]
                if page_id in self.interceptors:
                    del self.interceptors[page_id]
            
            # Close context
            if context_id in self.contexts:
                await self.contexts[context_id].close()
                del self.contexts[context_id]
            
            # Clear session browser context
            session.browser_context_id = None
            
            log_browser_event("session_cleanup", context_id, session_id=session.id)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up session resources: {str(e)}")
    
    async def take_screenshot(self, page: Page, path: str = None) -> bytes:
        """Take a screenshot of the current page"""
        try:
            screenshot_options = {
                "full_page": True,
                "type": "png"
            }
            
            if path:
                screenshot_options["path"] = path
            
            screenshot = await page.screenshot(**screenshot_options)
            
            self.logger.debug(f"Screenshot taken: {len(screenshot)} bytes")
            
            return screenshot
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {str(e)}")
            return b""
