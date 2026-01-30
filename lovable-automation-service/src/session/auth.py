"""
Firebase Authentication for Lovable sessions
"""

import asyncio
import json
from typing import Dict, Any, Optional
import httpx
from datetime import datetime, timedelta

from ..core.config import settings
from ..core.exceptions import AuthenticationError
from ..core.logging import LoggerMixin


class FirebaseAuthenticator(LoggerMixin):
    """
    Handles Firebase authentication for Lovable accounts
    """
    
    def __init__(self):
        self.firebase_api_key = "AIzaSyBpZddRwHdCw9T_PXq8_JsMiXB2kDnhPE4"  # Lovable's Firebase API key
        self.firebase_auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.firebase_api_key}"
        self.firebase_refresh_url = f"https://securetoken.googleapis.com/v1/token?key={self.firebase_api_key}"
        
        # Session for HTTP requests
        self.http_client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self) -> None:
        """Initialize the authenticator"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
    
    async def stop(self) -> None:
        """Cleanup the authenticator"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
    
    async def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Firebase and return session data
        
        Returns:
            Dict containing:
            - token: Firebase ID token
            - refresh_token: Firebase refresh token
            - expires_in: Token expiration time in seconds
            - user_id: Firebase user ID
            - cookies: Session cookies (if any)
        """
        if not self.http_client:
            await self.start()
        
        try:
            self.logger.info("Authenticating with Firebase", email=email)
            
            # Prepare authentication payload
            auth_payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            # Make authentication request
            response = await self.http_client.post(
                self.firebase_auth_url,
                json=auth_payload
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", "Unknown authentication error")
                
                self.logger.error(
                    "Firebase authentication failed",
                    email=email,
                    status_code=response.status_code,
                    error=error_message
                )
                
                raise AuthenticationError(f"Firebase authentication failed: {error_message}")
            
            # Parse response
            auth_data = response.json()
            
            # Extract session data
            session_data = {
                "token": auth_data["idToken"],
                "refresh_token": auth_data["refreshToken"],
                "expires_in": int(auth_data["expiresIn"]),
                "user_id": auth_data["localId"],
                "email": auth_data["email"],
                "cookies": self._extract_cookies_from_response(response)
            }
            
            self.logger.info(
                "Firebase authentication successful",
                email=email,
                user_id=session_data["user_id"],
                expires_in=session_data["expires_in"]
            )
            
            return session_data
            
        except httpx.RequestError as e:
            self.logger.error("Network error during authentication", email=email, error=str(e))
            raise AuthenticationError(f"Network error during authentication: {str(e)}")
        
        except Exception as e:
            self.logger.error("Unexpected error during authentication", email=email, error=str(e))
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Firebase token using refresh token
        
        Returns:
            Dict containing refreshed token data
        """
        if not self.http_client:
            await self.start()
        
        try:
            self.logger.info("Refreshing Firebase token")
            
            # Prepare refresh payload
            refresh_payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            # Make refresh request
            response = await self.http_client.post(
                self.firebase_refresh_url,
                json=refresh_payload
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", "Unknown refresh error")
                
                self.logger.error(
                    "Token refresh failed",
                    status_code=response.status_code,
                    error=error_message
                )
                
                raise AuthenticationError(f"Token refresh failed: {error_message}")
            
            # Parse response
            refresh_data = response.json()
            
            # Extract refreshed token data
            token_data = {
                "token": refresh_data["id_token"],
                "refresh_token": refresh_data["refresh_token"],
                "expires_in": int(refresh_data["expires_in"]),
                "user_id": refresh_data["user_id"]
            }
            
            self.logger.info("Token refresh successful", user_id=token_data["user_id"])
            
            return token_data
            
        except httpx.RequestError as e:
            self.logger.error("Network error during token refresh", error=str(e))
            raise AuthenticationError(f"Network error during token refresh: {str(e)}")
        
        except Exception as e:
            self.logger.error("Unexpected error during token refresh", error=str(e))
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase token and get user info
        
        Returns:
            Dict containing user information
        """
        if not self.http_client:
            await self.start()
        
        try:
            verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.firebase_api_key}"
            
            verify_payload = {
                "idToken": token
            }
            
            response = await self.http_client.post(
                verify_url,
                json=verify_payload
            )
            
            if response.status_code != 200:
                raise AuthenticationError("Token verification failed")
            
            verify_data = response.json()
            users = verify_data.get("users", [])
            
            if not users:
                raise AuthenticationError("No user data found")
            
            user_data = users[0]
            
            return {
                "user_id": user_data["localId"],
                "email": user_data["email"],
                "email_verified": user_data.get("emailVerified", False),
                "created_at": user_data.get("createdAt"),
                "last_login": user_data.get("lastLoginAt")
            }
            
        except Exception as e:
            self.logger.error("Token verification failed", error=str(e))
            raise AuthenticationError(f"Token verification failed: {str(e)}")
    
    def _extract_cookies_from_response(self, response: httpx.Response) -> Dict[str, str]:
        """Extract cookies from HTTP response"""
        cookies = {}
        
        # Extract Set-Cookie headers
        set_cookie_headers = response.headers.get_list("set-cookie")
        
        for cookie_header in set_cookie_headers:
            # Parse cookie (simplified parsing)
            if "=" in cookie_header:
                cookie_parts = cookie_header.split(";")[0]  # Get main cookie part
                name, value = cookie_parts.split("=", 1)
                cookies[name.strip()] = value.strip()
        
        return cookies
    
    def calculate_token_expiry(self, expires_in: int) -> datetime:
        """Calculate token expiry datetime"""
        return datetime.utcnow() + timedelta(seconds=expires_in)
    
    def is_token_expired(self, expires_at: datetime, buffer_minutes: int = 5) -> bool:
        """Check if token is expired (with buffer)"""
        buffer_time = datetime.utcnow() + timedelta(minutes=buffer_minutes)
        return expires_at <= buffer_time
    
    async def authenticate_with_retry(self, email: str, password: str, max_retries: int = 3) -> Dict[str, Any]:
        """Authenticate with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.authenticate(email, password)
            except AuthenticationError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        f"Authentication attempt {attempt + 1} failed, retrying in {wait_time}s",
                        email=email,
                        error=str(e)
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(
                        f"All {max_retries} authentication attempts failed",
                        email=email,
                        error=str(e)
                    )
        
        raise last_error
