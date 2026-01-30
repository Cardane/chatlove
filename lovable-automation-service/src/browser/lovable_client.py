"""
Real Lovable.dev Client with Playwright
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from ..core.logging import LoggerMixin
from ..core.config import settings


class LovableClient(LoggerMixin):
    """
    Real client for interacting with Lovable.dev
    """
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.current_project_id = None
        self.projects = []
    
    async def start(self) -> None:
        """Start the browser"""
        try:
            self.logger.info("Starting Lovable client")
            
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Set to True for production
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await self.context.new_page()
            
            self.logger.info("Lovable client started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Lovable client: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.logger.info("Lovable client stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Lovable client: {str(e)}")
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login to Lovable.dev
        """
        if not self.page:
            raise RuntimeError("Client not started")
        
        try:
            self.logger.info(f"Logging in to Lovable as {email}")
            
            # Navigate to login page
            await self.page.goto("https://lovable.dev/login", wait_until='networkidle')
            
            # Wait for login form
            await self.page.wait_for_selector('input[type="email"]', timeout=10000)
            
            # Fill login form
            await self.page.fill('input[type="email"]', email)
            await self.page.fill('input[type="password"]', password)
            
            # Click login button
            await self.page.click('button[type="submit"]')
            
            # Wait for successful login (redirect to dashboard)
            try:
                await self.page.wait_for_url("**/dashboard**", timeout=30000)
                self.is_logged_in = True
                
                self.logger.info(f"Successfully logged in to Lovable as {email}")
                
                return {
                    "success": True,
                    "message": "Login successful",
                    "current_url": self.page.url
                }
                
            except Exception as e:
                # Check for error messages
                error_message = await self._get_error_message()
                
                return {
                    "success": False,
                    "error": error_message or f"Login failed: {str(e)}"
                }
            
        except Exception as e:
            self.logger.error(f"Login failed for {email}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get list of user projects
        """
        if not self.page or not self.is_logged_in:
            raise RuntimeError("Not logged in")
        
        try:
            self.logger.info("Fetching projects from Lovable")
            
            # Navigate to projects page
            await self.page.goto("https://lovable.dev/dashboard/projects", wait_until='networkidle')
            
            # Wait for projects to load
            await asyncio.sleep(3)
            
            # Extract project data using multiple strategies
            projects = await self.page.evaluate("""
                () => {
                    const projects = [];
                    
                    // Strategy 1: Look for project cards with links
                    const projectLinks = document.querySelectorAll('a[href*="/projects/"]');
                    projectLinks.forEach(link => {
                        const href = link.href;
                        const match = href.match(/\/projects\/([^\/\\?]+)/);
                        if (match) {
                            const projectId = match[1];
                            
                            // Try to find project name
                            let name = 'Unnamed Project';
                            const nameElement = link.querySelector('h1, h2, h3, h4, [class*="title"], [class*="name"]') ||
                                              link.closest('[class*="card"], [class*="item"]')?.querySelector('h1, h2, h3, h4, [class*="title"], [class*="name"]');
                            
                            if (nameElement) {
                                name = nameElement.textContent.trim();
                            }
                            
                            // Try to find description
                            let description = '';
                            const descElement = link.querySelector('p, [class*="desc"]') ||
                                              link.closest('[class*="card"], [class*="item"]')?.querySelector('p, [class*="desc"]');
                            
                            if (descElement) {
                                description = descElement.textContent.trim();
                            }
                            
                            // Try to find last modified date
                            let lastModified = '';
                            const dateElement = link.querySelector('[class*="date"], [class*="time"]') ||
                                              link.closest('[class*="card"], [class*="item"]')?.querySelector('[class*="date"], [class*="time"]');
                            
                            if (dateElement) {
                                lastModified = dateElement.textContent.trim();
                            }
                            
                            projects.push({
                                id: projectId,
                                name: name,
                                description: description,
                                lastModified: lastModified,
                                url: href
                            });
                        }
                    });
                    
                    // Strategy 2: Look for any elements with project IDs in data attributes
                    const dataElements = document.querySelectorAll('[data-project-id], [data-id*="-"]');
                    dataElements.forEach(el => {
                        const projectId = el.dataset.projectId || el.dataset.id;
                        if (projectId && !projects.find(p => p.id === projectId)) {
                            const nameElement = el.querySelector('h1, h2, h3, h4, [class*="title"], [class*="name"]');
                            const name = nameElement ? nameElement.textContent.trim() : 'Unnamed Project';
                            
                            projects.push({
                                id: projectId,
                                name: name,
                                description: '',
                                lastModified: '',
                                url: `https://lovable.dev/projects/${projectId}`
                            });
                        }
                    });
                    
                    // Remove duplicates and filter valid projects
                    const uniqueProjects = projects.filter((project, index, self) => 
                        index === self.findIndex(p => p.id === project.id) && 
                        project.id && 
                        project.id.length > 5 &&
                        project.name !== 'Unnamed Project'
                    );
                    
                    return uniqueProjects;
                }
            """)
            
            self.projects = projects
            self.logger.info(f"Found {len(projects)} projects")
            
            return projects
            
        except Exception as e:
            self.logger.error(f"Failed to get projects: {str(e)}")
            return []
    
    async def open_project(self, project_id: str) -> bool:
        """
        Open a specific project
        """
        if not self.page or not self.is_logged_in:
            raise RuntimeError("Not logged in")
        
        try:
            self.logger.info(f"Opening project {project_id}")
            
            # Navigate to project
            project_url = f"https://lovable.dev/projects/{project_id}"
            await self.page.goto(project_url, wait_until='networkidle')
            
            # Wait for project to load
            await asyncio.sleep(5)
            
            # Check if we're in the project (look for chat interface)
            chat_selectors = [
                'textarea[placeholder*="message"]',
                'textarea[placeholder*="Message"]',
                'input[placeholder*="message"]',
                'input[placeholder*="Message"]',
                '[class*="chat"] textarea',
                '[class*="input"] textarea'
            ]
            
            chat_found = False
            for selector in chat_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        chat_found = True
                        break
                except:
                    continue
            
            if chat_found:
                self.current_project_id = project_id
                self.logger.info(f"Successfully opened project {project_id}")
                return True
            else:
                self.logger.warning(f"Project {project_id} opened but chat interface not found")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to open project {project_id}: {str(e)}")
            return False
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message to the current project's chat
        """
        if not self.page or not self.is_logged_in or not self.current_project_id:
            raise RuntimeError("Not logged in or no project open")
        
        try:
            self.logger.info(f"Sending message: {message[:100]}...")
            
            # Find chat input
            chat_input = None
            chat_selectors = [
                'textarea[placeholder*="message"]',
                'textarea[placeholder*="Message"]',
                'input[placeholder*="message"]',
                'input[placeholder*="Message"]',
                '[class*="chat"] textarea',
                '[class*="input"] textarea'
            ]
            
            for selector in chat_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        chat_input = element
                        break
                except:
                    continue
            
            if not chat_input:
                return {
                    "success": False,
                    "error": "Chat input not found"
                }
            
            # Clear and type message
            await chat_input.fill(message)
            
            # Find send button
            send_button = None
            send_selectors = [
                'button[type="submit"]',
                'button[aria-label*="Send"]',
                'button[title*="Send"]',
                '[class*="send"] button',
                'button:has-text("Send")',
                'button:has-text("→")'
            ]
            
            for selector in send_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible() and await element.is_enabled():
                        send_button = element
                        break
                except:
                    continue
            
            if not send_button:
                # Try pressing Enter
                await chat_input.press('Enter')
            else:
                await send_button.click()
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Try to extract the response
            response_content = await self._extract_latest_response()
            
            self.logger.info("Message sent successfully")
            
            return {
                "success": True,
                "message_sent": message,
                "response": response_content,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message_sent": message
            }
    
    async def _extract_latest_response(self) -> Dict[str, Any]:
        """
        Extract the latest AI response from the chat
        """
        try:
            # Wait a bit more for the response to fully load
            await asyncio.sleep(5)
            
            response_data = await self.page.evaluate("""
                () => {
                    // Look for message containers
                    const messageSelectors = [
                        '[class*="message"]',
                        '[class*="chat"]',
                        '[data-testid*="message"]',
                        '.prose',
                        '[class*="response"]'
                    ];
                    
                    let messages = [];
                    
                    messageSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text.length > 10) {
                                messages.push({
                                    content: text,
                                    html: el.innerHTML,
                                    selector: selector
                                });
                            }
                        });
                    });
                    
                    // Look for code blocks
                    const codeBlocks = [];
                    const codeElements = document.querySelectorAll('pre code, .code-block, [class*="code"]');
                    codeElements.forEach(el => {
                        const content = el.textContent.trim();
                        if (content.length > 10) {
                            const language = el.className.match(/language-(\w+)/)?.[1] || 'text';
                            codeBlocks.push({
                                content: content,
                                language: language
                            });
                        }
                    });
                    
                    return {
                        messages: messages.slice(-3), // Get last 3 messages
                        codeBlocks: codeBlocks,
                        pageTitle: document.title,
                        url: window.location.href
                    };
                }
            """)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract response: {str(e)}")
            return {
                "messages": [],
                "codeBlocks": [],
                "error": str(e)
            }
    
    async def _get_error_message(self) -> Optional[str]:
        """
        Extract error message from the page
        """
        try:
            error_selectors = [
                '[class*="error"]',
                '[class*="alert"]',
                '[role="alert"]',
                '.text-red-500',
                '.text-danger'
            ]
            
            for selector in error_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        text = await element.text_content()
                        if text and text.strip():
                            return text.strip()
                except:
                    continue
            
            return None
            
        except Exception as e:
            return None
    
    async def get_current_status(self) -> Dict[str, Any]:
        """
        Get current status of the client
        """
        return {
            "is_logged_in": self.is_logged_in,
            "current_project_id": self.current_project_id,
            "projects_count": len(self.projects),
            "current_url": self.page.url if self.page else None
        }
    
    async def take_screenshot(self, path: str = None) -> bytes:
        """
        Take a screenshot of the current page
        """
        if not self.page:
            raise RuntimeError("Client not started")
        
        return await self.page.screenshot(path=path, full_page=True)
