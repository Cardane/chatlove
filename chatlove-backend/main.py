"""
ChatLove - Backend API
FastAPI server with license management and Lovable proxy
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import os
import httpx

from database import get_db, init_db, create_default_admin, User, License, UsageLog, Admin
from auth import (
    verify_password, get_password_hash, create_access_token, verify_token,
    generate_license_key, generate_hardware_id, verify_hardware_id,
    calculate_tokens_saved
)

# Lovable proxy removed - not needed for admin panel

# =============================================================================
# APP SETUP
# =============================================================================

app = FastAPI(
    title="ChatLove API",
    description="License management and Lovable proxy",
    version="1.0.0"
)

# CORS - Using Starlette's CORSMiddleware directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://lovable.dev",
        "https://*.lovable.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    create_default_admin()


# =============================================================================
# MODELS
# =============================================================================

class AdminLogin(BaseModel):
    username: str
    password: str


class LicenseActivate(BaseModel):
    username: str
    license_key: str
    fingerprint: dict  # Browser fingerprint


class LicenseValidate(BaseModel):
    token: str
    fingerprint: dict


class ProxyRequest(BaseModel):
    token: str
    project_id: str
    message: str
    lovable_session: str
    files: Optional[List[dict]] = None


class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None


class LicenseCreate(BaseModel):
    user_id: Optional[int] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Verify admin token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload or payload.get("type") != "admin":
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    admin = db.query(Admin).filter(Admin.id == payload.get("admin_id")).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    return admin


def get_current_license(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Verify license token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload or payload.get("type") != "license":
        raise HTTPException(status_code=401, detail="Invalid license token")
    
    license = db.query(License).filter(License.id == payload.get("license_id")).first()
    if not license or not license.is_active:
        raise HTTPException(status_code=401, detail="License not found or inactive")
    
    return license


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    return {
        "name": "ChatLove API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@app.post("/api/admin/login")
async def admin_login(login: AdminLogin, db: Session = Depends(get_db)):
    """Admin login"""
    admin = db.query(Admin).filter(Admin.username == login.username).first()
    
    if not admin or not verify_password(login.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"admin_id": admin.id, "type": "admin"})
    
    return {
        "success": True,
        "token": token,
        "admin": {
            "id": admin.id,
            "username": admin.username
        }
    }


@app.get("/api/admin/dashboard")
async def admin_dashboard(admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    total_users = db.query(User).count()
    total_licenses = db.query(License).count()
    active_licenses = db.query(License).filter(License.is_active == True, License.is_used == True).count()
    total_tokens = db.query(UsageLog).with_entities(func.sum(UsageLog.tokens_saved)).scalar() or 0
    total_requests = db.query(UsageLog).with_entities(func.sum(UsageLog.request_count)).scalar() or 0
    
    return {
        "total_users": total_users,
        "total_licenses": total_licenses,
        "active_licenses": active_licenses,
        "total_tokens_saved": float(total_tokens),
        "total_requests": int(total_requests)
    }


@app.get("/api/admin/users")
async def list_users(admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).all()
    
    result = []
    for user in users:
        licenses = db.query(License).filter(License.user_id == user.id).all()
        tokens = db.query(UsageLog).join(License).filter(License.user_id == user.id).with_entities(func.sum(UsageLog.tokens_saved)).scalar() or 0
        
        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "licenses_count": len(licenses),
            "tokens_saved": float(tokens)
        })
    
    return result


@app.post("/api/admin/users")
async def create_user(user_data: UserCreate, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Create new user"""
    # Convert empty string to None for email
    email = user_data.email if user_data.email else None
    
    user = User(name=user_data.name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@app.put("/api/admin/users/{user_id}")
async def update_user(user_id: int, user_data: UserCreate, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Update user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert empty string to None for email
    email = user_data.email if user_data.email else None
    
    user.name = user_data.name
    user.email = email
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Delete user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user (licenses will be orphaned but kept)
    db.delete(user)
    db.commit()
    
    return {"success": True, "message": "User deleted"}


@app.get("/api/admin/licenses")
async def list_licenses(admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """List all licenses"""
    licenses = db.query(License).all()
    
    result = []
    for lic in licenses:
        user = db.query(User).filter(User.id == lic.user_id).first() if lic.user_id else None
        tokens = db.query(UsageLog).filter(UsageLog.license_id == lic.id).with_entities(func.sum(UsageLog.tokens_saved)).scalar() or 0
        
        result.append({
            "id": lic.id,
            "license_key": lic.license_key,
            "user_name": user.name if user else None,
            "is_active": lic.is_active,
            "is_used": lic.is_used,
            "created_at": lic.created_at.isoformat(),
            "activated_at": lic.activated_at.isoformat() if lic.activated_at else None,
            "tokens_saved": float(tokens)
        })
    
    return result


@app.post("/api/admin/licenses")
async def create_license(license_data: LicenseCreate, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Generate new license"""
    license_key = generate_license_key()
    
    license = License(
        license_key=license_key,
        user_id=license_data.user_id
    )
    db.add(license)
    db.commit()
    db.refresh(license)
    
    return {
        "success": True,
        "license": {
            "id": license.id,
            "license_key": license.license_key,
            "user_id": license.user_id
        }
    }


@app.put("/api/admin/licenses/{license_id}")
async def update_license(license_id: int, is_active: bool, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Activate/Deactivate license"""
    license = db.query(License).filter(License.id == license_id).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    license.is_active = is_active
    db.commit()
    
    return {"success": True, "is_active": is_active}


@app.delete("/api/admin/licenses/{license_id}")
async def delete_license(license_id: int, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Delete license"""
    license = db.query(License).filter(License.id == license_id).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Delete associated usage logs first
    db.query(UsageLog).filter(UsageLog.license_id == license_id).delete()
    
    # Delete license
    db.delete(license)
    db.commit()
    
    return {"success": True, "message": "License deleted"}


# =============================================================================
# LICENSE ENDPOINTS
# =============================================================================

@app.post("/api/license/activate")
async def activate_license(data: LicenseActivate, db: Session = Depends(get_db)):
    """Activate license (first time)"""
    # Find license
    license = db.query(License).filter(License.license_key == data.license_key).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="Invalid license key")
    
    if not license.is_active:
        raise HTTPException(status_code=403, detail="License is deactivated")
    
    # Generate hardware ID
    hardware_id = generate_hardware_id(data.fingerprint)
    
    # Check if already used
    if license.is_used:
        # Verify hardware ID matches
        if license.hardware_id != hardware_id:
            raise HTTPException(status_code=403, detail="License already activated on another device")
    else:
        # First activation
        license.hardware_id = hardware_id
        license.is_used = True
        license.activated_at = datetime.utcnow()
        
        # Create user if doesn't exist
        if not license.user_id:
            user = User(name=data.username)
            db.add(user)
            db.commit()
            db.refresh(user)
            license.user_id = user.id
        
        db.commit()
    
    # Generate token
    token = create_access_token({
        "license_id": license.id,
        "user_id": license.user_id,
        "type": "license"
    })
    
    return {
        "success": True,
        "token": token,
        "user": {
            "id": license.user_id,
            "name": data.username
        }
    }


@app.post("/api/license/validate")
async def validate_license(data: LicenseValidate, db: Session = Depends(get_db)):
    """Validate existing license"""
    payload = verify_token(data.token)
    
    if not payload or payload.get("type") != "license":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    license = db.query(License).filter(License.id == payload.get("license_id")).first()
    
    if not license or not license.is_active:
        raise HTTPException(status_code=401, detail="License not found or inactive")
    
    # Verify hardware ID
    hardware_id = generate_hardware_id(data.fingerprint)
    if license.hardware_id != hardware_id:
        raise HTTPException(status_code=403, detail="Hardware ID mismatch")
    
    return {"success": True, "valid": True}


@app.post("/api/license/usage")
async def log_usage(message_length: int, license: License = Depends(get_current_license), db: Session = Depends(get_db)):
    """Log usage and calculate tokens saved"""
    tokens_saved = calculate_tokens_saved(message_length)
    
    usage = UsageLog(
        license_id=license.id,
        tokens_saved=tokens_saved,
        message_length=message_length
    )
    db.add(usage)
    db.commit()
    
    return {
        "success": True,
        "tokens_saved": tokens_saved
    }


# =============================================================================
# CREDITS ENDPOINTS
# =============================================================================

@app.post("/api/credits/log")
async def log_credits(data: dict, db: Session = Depends(get_db)):
    """Registra créditos economizados"""
    license_key = data.get("license_key")
    tokens_saved = data.get("tokens_saved", 0)
    message_length = data.get("message_length", 0)
    
    if not license_key:
        raise HTTPException(status_code=400, detail="License key não fornecida")
    
    # Buscar licença
    license = db.query(License).filter(License.license_key == license_key).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    
    # Criar registro de uso
    usage = UsageLog(
        license_id=license.id,
        tokens_saved=float(tokens_saved),
        message_length=int(message_length),
        request_count=1
    )
    db.add(usage)
    db.commit()
    
    return {"success": True, "tokens_saved": tokens_saved}


@app.get("/api/credits/total/{license_key}")
async def get_total_credits(license_key: str, db: Session = Depends(get_db)):
    """Retorna total de créditos economizados por uma licença"""
    license = db.query(License).filter(License.license_key == license_key).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    
    # Somar todos os créditos
    total = db.query(UsageLog).filter(
        UsageLog.license_id == license.id
    ).with_entities(
        func.sum(UsageLog.tokens_saved)
    ).scalar() or 0
    
    return {
        "success": True,
        "total_credits": float(total),
        "license_key": license_key
    }


# =============================================================================
# PROXY ENDPOINT
# =============================================================================

@app.post("/api/proxy")
async def send_via_proxy(request: ProxyRequest, db: Session = Depends(get_db)):
    """Send message via Lovable proxy using user's session"""
    # Verify license token
    payload = verify_token(request.token)
    
    if not payload or payload.get("type") != "license":
        raise HTTPException(status_code=401, detail="Invalid license token")
    
    license = db.query(License).filter(License.id == payload.get("license_id")).first()
    
    if not license or not license.is_active:
        raise HTTPException(status_code=401, detail="License not found or inactive")
    
    # Calculate tokens saved (estimate: 4 chars = 1 token)
    tokens_saved = calculate_tokens_saved(len(request.message))
    
    try:
        # Generate unique message IDs using official TypeID library
        from typeid_python import TypeID
        
        # Generate TypeIDs with correct prefixes
        message_id = str(TypeID(prefix="umsg"))
        ai_message_id = str(TypeID(prefix="aimsg"))
        
        # Prepare payload according to Lovable API format
        payload_data = {
            "message": request.message,
            "id": message_id,
            "mode": "instant",
            "debug_mode": False,
            "prev_session_id": None,  # First message or get from context
            "user_input": {},
            "ai_message_id": ai_message_id,
            "current_page": "index",
            "view": "preview",
            "view_description": "The user is currently viewing the preview.",
            "model": None,
            "session_replay": "[]",
            "client_logs": [],
            "network_requests": [],
            "runtime_errors": [],
            "integration_metadata": {
                "browser": {
                    "preview_viewport_width": 800,
                    "preview_viewport_height": 600
                }
            }
        }
        
        # Add files if provided
        if request.files:
            payload_data["files"] = request.files
        
        # Send message to Lovable API using CORRECT endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.lovable.dev/projects/{request.project_id}/chat",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {request.lovable_session}",
                    "Origin": "https://lovable.dev",
                    "Referer": "https://lovable.dev/",
                    "x-client-git-sha": "02e494f6d51b5ea5a1fc25226f7e37dab356d0cd",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                json=payload_data,
                timeout=60.0
            )
            
            # Lovable returns 202 Accepted for async processing
            if response.status_code not in [200, 202]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lovable API error: {response.text}"
                )
            
            # For 202, the response is processed asynchronously
            result = {
                "status": "accepted",
                "message_id": message_id,
                "ai_message_id": ai_message_id
            }
            
            if response.status_code == 200:
                try:
                    result = response.json()
                except:
                    pass
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout ao conectar com Lovable")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Erro de conexão: {str(e)}")
    
    # Log usage
    usage = UsageLog(
        license_id=license.id,
        tokens_saved=tokens_saved,
        message_length=len(request.message)
    )
    db.add(usage)
    db.commit()
    
    # Return success with Lovable response
    return {
        "success": True,
        "message": "Mensagem enviada com sucesso!",
        "tokens_saved": tokens_saved,
        "lovable_response": result
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8000))
    
    print("=" * 60)
    print("CHATLOVE API")
    print("=" * 60)
    print(f"Server: http://127.0.0.1:{PORT}")
    print(f"Docs:   http://127.0.0.1:{PORT}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
