"""
CSS/XPath selectors for Lovable.dev interface
"""

from typing import Dict, Any


class LovableSelectors:
    """
    CSS and XPath selectors for Lovable.dev interface elements
    """
    
    # Authentication selectors
    LOGIN_EMAIL_INPUT = 'input[type="email"]'
    LOGIN_PASSWORD_INPUT = 'input[type="password"]'
    LOGIN_SUBMIT_BUTTON = 'button[type="submit"]'
    LOGIN_FORM = 'form'
    
    # Navigation selectors
    DASHBOARD_LINK = 'a[href="/dashboard"]'
    PROJECTS_LINK = 'a[href*="/projects"]'
    NEW_PROJECT_BUTTON = 'button:has-text("New Project")'
    
    # Project interface selectors
    PROJECT_TITLE = 'h1, [data-testid="project-title"]'
    PROJECT_DESCRIPTION = '[data-testid="project-description"]'
    
    # Chat interface selectors
    CHAT_CONTAINER = '[data-testid="chat-container"], .chat-container'
    CHAT_INPUT = 'textarea[placeholder*="message"], textarea[placeholder*="chat"], #chat-input'
    CHAT_SEND_BUTTON = 'button[type="submit"]:has-text("Send"), button:has-text("Send")'
    CHAT_MESSAGES = '.message, [data-testid="message"]'
    CHAT_MESSAGE_CONTENT = '.message-content, [data-testid="message-content"]'
    CHAT_MESSAGE_USER = '.message.user, [data-testid="user-message"]'
    CHAT_MESSAGE_AI = '.message.ai, [data-testid="ai-message"]'
    
    # Code editor selectors
    CODE_EDITOR = '.monaco-editor, .code-editor, [data-testid="code-editor"]'
    CODE_EDITOR_TEXTAREA = '.monaco-editor textarea, .code-editor textarea'
    FILE_TREE = '.file-tree, [data-testid="file-tree"]'
    FILE_ITEM = '.file-item, [data-testid="file-item"]'
    
    # Preview selectors
    PREVIEW_IFRAME = 'iframe[src*="preview"], iframe[title*="preview"]'
    PREVIEW_CONTAINER = '.preview-container, [data-testid="preview"]'
    
    # Loading states
    LOADING_SPINNER = '.loading, .spinner, [data-testid="loading"]'
    LOADING_OVERLAY = '.loading-overlay, [data-testid="loading-overlay"]'
    
    # Error states
    ERROR_MESSAGE = '.error, .error-message, [data-testid="error"]'
    ERROR_TOAST = '.toast.error, [data-testid="error-toast"]'
    
    # Success states
    SUCCESS_MESSAGE = '.success, .success-message, [data-testid="success"]'
    SUCCESS_TOAST = '.toast.success, [data-testid="success-toast"]'
    
    # Modal/Dialog selectors
    MODAL = '.modal, [role="dialog"]'
    MODAL_CLOSE = '.modal-close, [aria-label="Close"]'
    MODAL_CONFIRM = '.modal button:has-text("Confirm"), .modal button:has-text("OK")'
    MODAL_CANCEL = '.modal button:has-text("Cancel")'
    
    # User menu selectors
    USER_MENU = '.user-menu, [data-testid="user-menu"]'
    USER_AVATAR = '.user-avatar, [data-testid="user-avatar"]'
    LOGOUT_BUTTON = 'button:has-text("Logout"), a:has-text("Logout")'
    
    # Project creation selectors
    CREATE_PROJECT_MODAL = '[data-testid="create-project-modal"]'
    PROJECT_NAME_INPUT = 'input[name="name"], input[placeholder*="project name"]'
    PROJECT_TEMPLATE_SELECT = 'select[name="template"], [data-testid="template-select"]'
    CREATE_PROJECT_SUBMIT = 'button:has-text("Create Project")'
    
    # Streaming response indicators
    STREAMING_INDICATOR = '.streaming, [data-testid="streaming"]'
    TYPING_INDICATOR = '.typing, [data-testid="typing"]'
    
    @classmethod
    def get_chat_input_selectors(cls) -> list:
        """Get all possible chat input selectors"""
        return [
            cls.CHAT_INPUT,
            'textarea[placeholder*="Type a message"]',
            'textarea[placeholder*="Ask me anything"]',
            'textarea[placeholder*="What would you like to build"]',
            '#message-input',
            '.chat-input textarea',
            '[data-testid="chat-input"] textarea'
        ]
    
    @classmethod
    def get_send_button_selectors(cls) -> list:
        """Get all possible send button selectors"""
        return [
            cls.CHAT_SEND_BUTTON,
            'button[aria-label="Send message"]',
            'button[title="Send message"]',
            '.send-button',
            '[data-testid="send-button"]',
            'button:has(svg[data-icon="send"])',
            'button:has(.send-icon)'
        ]
    
    @classmethod
    def get_loading_selectors(cls) -> list:
        """Get all possible loading indicators"""
        return [
            cls.LOADING_SPINNER,
            cls.LOADING_OVERLAY,
            cls.STREAMING_INDICATOR,
            cls.TYPING_INDICATOR,
            '.loading-dots',
            '[data-testid="loading-dots"]',
            '.spinner-border',
            '.animate-spin'
        ]
    
    @classmethod
    def get_message_selectors(cls) -> list:
        """Get all possible message selectors"""
        return [
            cls.CHAT_MESSAGES,
            '.chat-message',
            '[data-testid="chat-message"]',
            '.message-bubble',
            '.conversation-message'
        ]
    
    @classmethod
    def get_error_selectors(cls) -> list:
        """Get all possible error selectors"""
        return [
            cls.ERROR_MESSAGE,
            cls.ERROR_TOAST,
            '.alert-error',
            '.notification-error',
            '[role="alert"]',
            '.toast-error',
            '.error-banner'
        ]


# XPath selectors for more complex queries
class LovableXPathSelectors:
    """XPath selectors for complex element queries"""
    
    # Chat input by placeholder text
    CHAT_INPUT_BY_PLACEHOLDER = "//textarea[contains(@placeholder, 'message') or contains(@placeholder, 'chat') or contains(@placeholder, 'build')]"
    
    # Send button by text content
    SEND_BUTTON_BY_TEXT = "//button[contains(text(), 'Send') or @aria-label='Send message' or @title='Send message']"
    
    # Last message in chat
    LAST_MESSAGE = "(//div[contains(@class, 'message') or @data-testid='message'])[last()]"
    
    # Last AI message
    LAST_AI_MESSAGE = "(//div[contains(@class, 'message') and contains(@class, 'ai') or @data-testid='ai-message'])[last()]"
    
    # Loading indicator that's visible
    VISIBLE_LOADING = "//div[contains(@class, 'loading') or contains(@class, 'spinner')][not(contains(@style, 'display: none'))]"
    
    # Error message that's visible
    VISIBLE_ERROR = "//div[contains(@class, 'error') or @role='alert'][not(contains(@style, 'display: none'))]"
    
    # Project link by name
    PROJECT_LINK_BY_NAME = "//a[contains(@href, '/projects/') and contains(text(), '{project_name}')]"
    
    # File in file tree by name
    FILE_BY_NAME = "//div[contains(@class, 'file-item') and contains(text(), '{file_name}')]"


# Dynamic selectors that can be formatted
class LovableDynamicSelectors:
    """Dynamic selectors that can be formatted with parameters"""
    
    @staticmethod
    def project_link(project_id: str) -> str:
        """Get selector for specific project link"""
        return f'a[href="/projects/{project_id}"]'
    
    @staticmethod
    def file_item(file_name: str) -> str:
        """Get selector for specific file item"""
        return f'[data-testid="file-item"]:has-text("{file_name}")'
    
    @staticmethod
    def message_by_content(content: str) -> str:
        """Get selector for message containing specific content"""
        return f'.message:has-text("{content[:50]}")'  # Truncate for selector
    
    @staticmethod
    def button_by_text(text: str) -> str:
        """Get selector for button with specific text"""
        return f'button:has-text("{text}")'
    
    @staticmethod
    def input_by_placeholder(placeholder: str) -> str:
        """Get selector for input with specific placeholder"""
        return f'input[placeholder*="{placeholder}"]'


# Selector validation and fallbacks
class SelectorValidator:
    """Validates and provides fallback selectors"""
    
    @staticmethod
    def get_fallback_selectors(primary_selector: str) -> list:
        """Get fallback selectors for common elements"""
        fallbacks = {
            LovableSelectors.CHAT_INPUT: LovableSelectors.get_chat_input_selectors(),
            LovableSelectors.CHAT_SEND_BUTTON: LovableSelectors.get_send_button_selectors(),
            LovableSelectors.LOADING_SPINNER: LovableSelectors.get_loading_selectors(),
            LovableSelectors.CHAT_MESSAGES: LovableSelectors.get_message_selectors(),
            LovableSelectors.ERROR_MESSAGE: LovableSelectors.get_error_selectors()
        }
        
        return fallbacks.get(primary_selector, [primary_selector])
    
    @staticmethod
    def is_valid_selector(selector: str) -> bool:
        """Basic validation for CSS selectors"""
        if not selector or not isinstance(selector, str):
            return False
        
        # Basic checks for common selector patterns
        invalid_chars = ['<', '>', '{', '}']
        return not any(char in selector for char in invalid_chars)
