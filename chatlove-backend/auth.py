"""
ChatLove - Authentication and License Management
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


# =============================================================================
# JWT TOKENS
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# =============================================================================
# LICENSE KEY GENERATION
# =============================================================================

def generate_license_key() -> str:
    """
    Generate unique license key in format: XXXX-XXXX-XXXX-XXXX
    """
    # Generate 16 random characters
    random_bytes = secrets.token_bytes(8)
    hex_string = random_bytes.hex().upper()
    
    # Format as XXXX-XXXX-XXXX-XXXX
    parts = [hex_string[i:i+4] for i in range(0, 16, 4)]
    license_key = "-".join(parts)
    
    return license_key


# =============================================================================
# HARDWARE ID GENERATION
# =============================================================================

def generate_hardware_id(fingerprint_data: dict) -> str:
    """
    Generate unique hardware ID from browser fingerprint
    
    Args:
        fingerprint_data: {
            "userAgent": "...",
            "language": "...",
            "timezone": "...",
            "screen": "1920x1080",
            "canvas": "..."
        }
    
    Returns:
        SHA-256 hash of fingerprint data
    """
    # Combine all fingerprint data
    combined = "|".join([
        str(fingerprint_data.get("userAgent", "")),
        str(fingerprint_data.get("language", "")),
        str(fingerprint_data.get("timezone", "")),
        str(fingerprint_data.get("screen", "")),
        str(fingerprint_data.get("canvas", ""))
    ])
    
    # Generate SHA-256 hash
    hardware_id = hashlib.sha256(combined.encode()).hexdigest()
    
    return hardware_id


def verify_hardware_id(stored_id: str, provided_data: dict) -> bool:
    """Verify hardware ID matches"""
    generated_id = generate_hardware_id(provided_data)
    return stored_id == generated_id


# =============================================================================
# TOKEN CALCULATION
# =============================================================================

def calculate_tokens_saved(message_length: int, complexity: int = 1) -> float:
    """
    Calculate estimated tokens saved
    
    Args:
        message_length: Length of user message
        complexity: Complexity multiplier (1-3)
    
    Returns:
        Estimated tokens saved (0.5 to ~10)
    """
    import random
    
    # Base: 0.5 to 1 token per simple request
    base_tokens = 0.5 + (random.random() * 0.5)
    
    # Multiplier based on message length
    length_multiplier = min(message_length / 100, 5)
    
    # Complexity multiplier
    complexity_multiplier = max(1, min(complexity, 3))
    
    # Calculate total
    total = base_tokens * length_multiplier * complexity_multiplier
    
    # Add random variation (±10%)
    variation = total * (0.9 + random.random() * 0.2)
    
    # Round to 2 decimal places
    return round(variation, 2)
