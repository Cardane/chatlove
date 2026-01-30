"""
Configuration settings for Lovable Automation Service
"""

import os
import json
from typing import List, Dict, Any
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql://user:pass@localhost:5432/chatlove"
    redis_url: str = "redis://localhost:6379/0"
    
    # Lovable Accounts
    lovable_accounts: str = '[]'
    
    # Security
    encryption_key: str = "your-32-byte-encryption-key-here"
    jwt_secret: str = "your-jwt-secret-here"
    
    # Rate Limiting
    max_messages_per_minute: int = 10
    max_concurrent_sessions: int = 5
    
    # Browser Settings
    browser_headless: bool = True
    browser_timeout: int = 30
    
    # Monitoring
    prometheus_port: int = 9090
    log_level: str = "INFO"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    
    # Firebase Settings
    firebase_credentials_path: str = ""
    
    # Lovable API
    lovable_api_url: str = "https://api.lovable.dev"
    lovable_web_url: str = "https://lovable.dev"
    
    @validator('lovable_accounts')
    def parse_lovable_accounts(cls, v):
        """Parse Lovable accounts from JSON string"""
        try:
            accounts = json.loads(v)
            if not isinstance(accounts, list):
                raise ValueError("Lovable accounts must be a list")
            
            for account in accounts:
                if not isinstance(account, dict) or 'email' not in account or 'password' not in account:
                    raise ValueError("Each account must have 'email' and 'password' fields")
            
            return accounts
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format for lovable_accounts")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_lovable_accounts() -> List[Dict[str, str]]:
    """Get parsed Lovable accounts"""
    return settings.lovable_accounts


def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    return {
        "url": settings.database_url,
        "echo": settings.log_level == "DEBUG"
    }


def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration"""
    return {
        "url": settings.redis_url,
        "decode_responses": True
    }


def get_browser_config() -> Dict[str, Any]:
    """Get browser configuration"""
    return {
        "headless": settings.browser_headless,
        "timeout": settings.browser_timeout * 1000,  # Convert to milliseconds
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor"
        ]
    }
