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

from database import get_db, init_db, create_default_admin, User, License, UsageLog, Admin, HubAccount, ProjectMapping
from auth import (
    verify_password, get_password_hash, create_access_token, verify_token,
    generate_license_key, generate_hardware_id, verify_hardware_id,
    calculate_tokens_saved
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Lovable API Configuration
LOVABLE_API_URL = "https://api.lovable.dev"

# =============================================================================
# APP SETUP
# =============================================================================

app = FastAPI(
    title="ChatLove API",
    description="License management and Lovable proxy",
    version="1.0.0"
)

# CORS - Using Starlette's CORSMiddleware directly
# Detectar ambiente
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"

if IS_PRODUCTION:
    allowed_origins = [
        "http://209.38.79.211",
        "https://209.38.79.211",
        "https://lovable.dev"
    ]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://209.38.79.211",
        "https://209.38.79.211",
        "https://lovable.dev"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lovable.dev"],  # ← CORREÇÃO: Apenas um valor
    allow_origin_regex=r"chrome-extension://.*",  # Permitir todas extensions do Chrome
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
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
    license_type: Optional[str] = "full"  # "trial" or "full"


class MasterProxyRequest(BaseModel):
    project_id: str
    message: str
    session_token: str
    license_key: Optional[str] = None


class MasterProxyResponse(BaseModel):
    success: bool
    message: str
    credits_saved: bool = True


class ValidateLicenseRequest(BaseModel):
    license_key: str


class HubAccountCreate(BaseModel):
    name: str
    email: str
    session_token: str
    credits_remaining: float = 0.0
    priority: int = 0


class HubAccountUpdate(BaseModel):
    name: Optional[str] = None
    session_token: Optional[str] = None
    credits_remaining: Optional[float] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class ProxyHubRequest(BaseModel):
    license_key: str
    original_project_id: str   # Projeto da conta do usuário
    message: str
    user_session_token: str    # Token da conta do usuário (para futura validação)


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
# HUB HELPER FUNCTIONS
# =============================================================================

def get_active_hub_account(db: Session) -> HubAccount:
    """
    Retorna primeira conta hub ativa
    (Versão simplificada - sem rotação)
    """
    account = db.query(HubAccount).filter(
        HubAccount.is_active == True
    ).order_by(
        HubAccount.priority.asc()
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=503,
            detail="Nenhuma conta hub disponível. Configure uma conta no admin panel."
        )
    
    # Atualizar estatísticas
    account.last_used_at = datetime.utcnow()
    account.total_requests += 1
    db.commit()
    
    return account


async def get_or_create_hub_project(
    original_project_id: str,
    hub_account: HubAccount,
    user_session_token: str,
    db: Session
) -> str:
    """
    Retorna project_id equivalente no hub
    Se não existir, cria novo projeto na conta hub
    """
    
    # Verificar se já existe mapeamento
    mapping = db.query(ProjectMapping).filter(
        ProjectMapping.original_project_id == original_project_id,
        ProjectMapping.hub_account_id == hub_account.id
    ).first()
    
    if mapping:
        print(f"[HUB] Usando projeto mapeado: {mapping.hub_project_id}")
        return mapping.hub_project_id
    
    # Não existe - criar novo projeto no hub
    print(f"[HUB] Criando novo projeto no hub para: {original_project_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Buscar informações do projeto original
        try:
            original_response = await client.get(
                f"https://api.lovable.dev/projects/{original_project_id}",
                headers={"Authorization": f"Bearer {user_session_token}"}
            )
            
            if original_response.status_code == 200:
                original_data = original_response.json()
                project_name = original_data.get("name", "Projeto")
            else:
                project_name = f"Projeto {original_project_id[:8]}"
        except Exception as e:
            print(f"[HUB] Não foi possível buscar nome do projeto: {e}")
            project_name = f"Projeto {original_project_id[:8]}"
        
        # 2. Criar projeto na conta hub
        try:
            create_response = await client.post(
                "https://api.lovable.dev/projects",
                headers={
                    "Authorization": f"Bearer {hub_account.session_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "name": f"[HUB] {project_name}",
                    "template": "blank"
                }
            )
            
            if create_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao criar projeto no hub: {create_response.text}"
                )
            
            hub_project_data = create_response.json()
            hub_project_id = hub_project_data.get("id")
            
            if not hub_project_id:
                raise HTTPException(
                    status_code=500,
                    detail="API não retornou project_id"
                )
            
            print(f"[HUB] Projeto criado no hub: {hub_project_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao criar projeto no hub: {str(e)}"
            )
        
        # 3. Salvar mapeamento
        mapping = ProjectMapping(
            original_project_id=original_project_id,
            hub_project_id=hub_project_id,
            hub_account_id=hub_account.id,
            project_name=project_name
        )
        db.add(mapping)
        db.commit()
        
        print(f"[HUB] Mapeamento salvo: {original_project_id} → {hub_project_id}")
        
        return hub_project_id


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
            "username": admin.username,
            "role": admin.role
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
            "license_type": lic.license_type,
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
            "is_expired": lic.is_expired(),
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
        user_id=license_data.user_id,
        license_type=license_data.license_type or "full"
    )
    db.add(license)
    db.commit()
    db.refresh(license)
    
    return {
        "success": True,
        "license": {
            "id": license.id,
            "license_key": license.license_key,
            "user_id": license.user_id,
            "license_type": license.license_type
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
# HUB PROXY ENDPOINT
# =============================================================================

@app.post("/api/proxy-hub")
async def proxy_hub(request: ProxyHubRequest, db: Session = Depends(get_db)):
    """
    Proxy Hub - Envia mensagens usando conta hub
    
    Fluxo:
    1. Valida licença do usuário
    2. Seleciona conta hub ativa
    3. Obtém/cria projeto equivalente no hub
    4. Envia mensagem usando token da conta hub
    5. Registra uso e economiza créditos
    
    Resultado: Créditos descontados da conta hub, não do usuário!
    """
    
    print("\n" + "=" * 60)
    print("[HUB PROXY] Nova requisição recebida")
    print("=" * 60)
    
    # ========================================
    # 1. VALIDAR LICENÇA
    # ========================================
    license = db.query(License).filter(
        License.license_key == request.license_key
    ).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    
    if not license.is_active:
        raise HTTPException(
            status_code=403,
            detail="Licença desativada pelo administrador"
        )
    
    # Verificar trial expirada
    if license.license_type == "trial":
        if license.expires_at and datetime.utcnow() > license.expires_at:
            raise HTTPException(
                status_code=403,
                detail="Licença trial expirada (15 minutos)"
            )
    
    print(f"[HUB] Licença validada: {request.license_key}")
    
    # ========================================
    # 2. SELECIONAR CONTA HUB
    # ========================================
    try:
        hub_account = get_active_hub_account(db)
        print(f"[HUB] Conta selecionada: {hub_account.name} ({hub_account.email})")
    except HTTPException as e:
        print(f"[HUB] Erro: {e.detail}")
        raise
    
    # ========================================
    # 3. OBTER/CRIAR PROJETO NO HUB
    # ========================================
    try:
        hub_project_id = await get_or_create_hub_project(
            original_project_id=request.original_project_id,
            hub_account=hub_account,
            user_session_token=request.user_session_token,
            db=db
        )
        print(f"[HUB] Projeto hub: {hub_project_id}")
    except HTTPException as e:
        print(f"[HUB] Erro ao mapear projeto: {e.detail}")
        raise
    except Exception as e:
        print(f"[HUB] Erro inesperado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao mapear projeto: {str(e)}"
        )
    
    # ========================================
    # 4. ENVIAR PARA LOVABLE (USANDO TOKEN HUB)
    # ========================================
    lovable_url = f"https://api.lovable.dev/projects/{hub_project_id}/chat"
    
    payload = {
        "message": request.message,
        "timestamp": datetime.now().isoformat()
    }
    
    headers = {
        "Authorization": f"Bearer {hub_account.session_token}",  # ← TOKEN DO HUB!
        "Content-Type": "application/json",
        "User-Agent": "ChatLove-Hub/1.0"
    }
    
    print(f"[HUB] Enviando para Lovable...")
    print(f"[HUB] URL: {lovable_url}")
    print(f"[HUB] Mensagem: {request.message[:50]}...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                lovable_url,
                headers=headers,
                json=payload
            )
            
            print(f"[HUB] Resposta Lovable: {response.status_code}")
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Token da conta hub inválido ou expirado. Atualize no admin."
                )
            elif response.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail="Sem permissão no projeto hub. Verifique configuração."
                )
            elif response.status_code not in [200, 202]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erro do Lovable: {response.text}"
                )
            
            print(f"[HUB] ✓ Mensagem enviada com sucesso!")
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout ao conectar com Lovable API"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enviar para Lovable: {str(e)}"
        )
    
    # ========================================
    # 5. REGISTRAR USO
    # ========================================
    tokens_saved = len(request.message) / 4  # Estimativa simples
    
    usage = UsageLog(
        license_id=license.id,
        tokens_saved=float(tokens_saved),
        message_length=len(request.message),
        request_count=1,
        hub_account_id=hub_account.id,           # ← NOVO
        original_project_id=request.original_project_id,  # ← NOVO
        hub_project_id=hub_project_id            # ← NOVO
    )
    db.add(usage)
    
    # Atualizar créditos estimados da conta hub
    hub_account.credits_remaining -= tokens_saved
    if hub_account.credits_remaining < 0:
        hub_account.credits_remaining = 0
    
    db.commit()
    
    print(f"[HUB] Uso registrado: {tokens_saved:.2f} tokens")
    print(f"[HUB] Créditos restantes (hub): {hub_account.credits_remaining:.2f}")
    print("=" * 60 + "\n")
    
    # ========================================
    # 6. RETORNAR SUCESSO
    # ========================================
    return {
        "success": True,
        "message": "Mensagem enviada via conta hub!",
        "hub_account_name": hub_account.name,
        "hub_account_email": hub_account.email,
        "hub_project_id": hub_project_id,
        "tokens_saved": float(tokens_saved),
        "hub_credits_remaining": float(hub_account.credits_remaining)
    }


# =============================================================================
# ADMIN - HUB ACCOUNTS
# =============================================================================

@app.get("/api/admin/hub-accounts")
async def list_hub_accounts(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lista todas as contas hub"""
    accounts = db.query(HubAccount).all()
    
    result = []
    for account in accounts:
        # Contar projetos mapeados
        projects_count = db.query(ProjectMapping).filter(
            ProjectMapping.hub_account_id == account.id
        ).count()
        
        # Total de tokens usados
        tokens_used = db.query(UsageLog).filter(
            UsageLog.hub_account_id == account.id
        ).with_entities(
            func.sum(UsageLog.tokens_saved)
        ).scalar() or 0
        
        result.append({
            "id": account.id,
            "name": account.name,
            "email": account.email,
            "credits_remaining": float(account.credits_remaining),
            "is_active": account.is_active,
            "priority": account.priority,
            "total_requests": account.total_requests,
            "projects_mapped": projects_count,
            "tokens_used": float(tokens_used),
            "last_used_at": account.last_used_at.isoformat() if account.last_used_at else None,
            "created_at": account.created_at.isoformat(),
            # Esconder token (segurança)
            "session_token_preview": account.session_token[:20] + "..." if account.session_token else None
        })
    
    return result


@app.post("/api/admin/hub-accounts")
async def create_hub_account(
    data: HubAccountCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Adiciona nova conta hub"""
    
    # Verificar se email já existe
    existing = db.query(HubAccount).filter(
        HubAccount.email == data.email
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Conta hub com este email já existe"
        )
    
    account = HubAccount(
        name=data.name,
        email=data.email,
        session_token=data.session_token,
        credits_remaining=data.credits_remaining,
        priority=data.priority
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return {
        "success": True,
        "account": {
            "id": account.id,
            "name": account.name,
            "email": account.email,
            "credits_remaining": account.credits_remaining
        }
    }


@app.put("/api/admin/hub-accounts/{account_id}")
async def update_hub_account(
    account_id: int,
    data: HubAccountUpdate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Atualiza conta hub"""
    
    account = db.query(HubAccount).filter(
        HubAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Conta hub não encontrada")
    
    # Atualizar campos fornecidos
    if data.name is not None:
        account.name = data.name
    if data.session_token is not None:
        account.session_token = data.session_token
    if data.credits_remaining is not None:
        account.credits_remaining = data.credits_remaining
    if data.is_active is not None:
        account.is_active = data.is_active
    if data.priority is not None:
        account.priority = data.priority
    
    account.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(account)
    
    return {
        "success": True,
        "account": {
            "id": account.id,
            "name": account.name,
            "is_active": account.is_active,
            "credits_remaining": account.credits_remaining
        }
    }


@app.delete("/api/admin/hub-accounts/{account_id}")
async def delete_hub_account(
    account_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Remove conta hub"""
    
    account = db.query(HubAccount).filter(
        HubAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Conta hub não encontrada")
    
    # Deletar mapeamentos associados
    db.query(ProjectMapping).filter(
        ProjectMapping.hub_account_id == account_id
    ).delete()
    
    # Deletar conta
    db.delete(account)
    db.commit()
    
    return {"success": True, "message": "Conta hub removida"}


@app.get("/api/admin/hub-accounts/{account_id}/projects")
async def list_hub_projects(
    account_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lista projetos mapeados de uma conta hub"""
    
    mappings = db.query(ProjectMapping).filter(
        ProjectMapping.hub_account_id == account_id
    ).all()
    
    result = []
    for mapping in mappings:
        # Contar uso deste projeto
        usage_count = db.query(UsageLog).filter(
            UsageLog.hub_project_id == mapping.hub_project_id
        ).count()
        
        result.append({
            "id": mapping.id,
            "original_project_id": mapping.original_project_id,
            "hub_project_id": mapping.hub_project_id,
            "project_name": mapping.project_name,
            "usage_count": usage_count,
            "created_at": mapping.created_at.isoformat()
        })
    
    return result


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
# VALIDATE LICENSE ENDPOINT (from proxy-backend)
# =============================================================================

@app.post("/api/validate-license")
async def validate_license_simple(request: ValidateLicenseRequest, db: Session = Depends(get_db)):
    """Valida se uma licença existe e está ativa (usado pelo popup)"""
    license = db.query(License).filter(
        License.license_key == request.license_key
    ).first()
    
    if not license:
        return {"success": False, "valid": False, "message": "Licença não encontrada"}
    
    # VERIFICAR SE ESTÁ DESATIVADA
    if not license.is_active:
        return {"success": False, "valid": False, "message": "Licença desativada pelo administrador"}
    
    # MARCAR COMO USADA NA PRIMEIRA VALIDAÇÃO
    if not license.is_used:
        license.is_used = True
        license.activated_at = datetime.utcnow()
        
        # Se for trial, definir expiração
        if license.license_type == "trial":
            from datetime import timedelta
            license.expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        db.commit()
    
    # VERIFICAR SE É TRIAL E JÁ EXPIROU
    if license.license_type == "trial":
        if license.expires_at:
            if datetime.utcnow() > license.expires_at:
                return {"success": False, "valid": False, "message": "Licença de teste expirada (15 minutos)"}
    
    # Retornar informações da licença para o frontend
    return {
        "success": True,
        "valid": True,
        "message": "Licença válida",
        "license_type": license.license_type,
        "expires_at": license.expires_at.isoformat() if license.expires_at else None
    }


# =============================================================================
# MASTER PROXY ENDPOINT
# =============================================================================

@app.post("/api/master-proxy", response_model=MasterProxyResponse)
async def master_proxy(request: MasterProxyRequest, db: Session = Depends(get_db)):
    """
    Proxy para enviar mensagens ao Lovable usando session token do usuário
    """
    
    # Validar dados
    if not request.session_token:
        raise HTTPException(status_code=400, detail="Session token não fornecido")
    
    if not request.project_id:
        raise HTTPException(status_code=400, detail="Project ID não fornecido")
    
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia")
    
    # VALIDAR LICENÇA ANTES DE ENVIAR
    if request.license_key:
        license = db.query(License).filter(
            License.license_key == request.license_key
        ).first()
        
        if not license:
            raise HTTPException(status_code=404, detail="Licença não encontrada")
        
        # Verificar se está desativada
        if not license.is_active:
            raise HTTPException(
                status_code=403,
                detail="Licença desativada pelo administrador. Entre em contato com o suporte."
            )
        
        # Verificar se é trial e expirou
        if license.license_type == "trial":
            if license.expires_at and datetime.utcnow() > license.expires_at:
                raise HTTPException(
                    status_code=403,
                    detail="Licença de teste expirada (15 minutos). Adquira uma licença completa para continuar."
                )
    
    # Preparar requisição para Lovable
    lovable_url = f"{LOVABLE_API_URL}/projects/{request.project_id}/chat"
    
    headers = {
        "Authorization": f"Bearer {request.session_token}",
        "Content-Type": "application/json",
        "User-Agent": "ChatLove/1.0"
    }
    
    payload = {
        "message": request.message,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                lovable_url,
                headers=headers,
                json=payload
            )
            
            # 200 OK ou 202 Accepted = Sucesso
            if response.status_code in [200, 202]:
                # Registrar créditos
                if request.license_key:
                    tokens_saved = len(request.message) / 4
                    
                    try:
                        license = db.query(License).filter(
                            License.license_key == request.license_key
                        ).first()
                        
                        if license:
                            usage = UsageLog(
                                license_id=license.id,
                                tokens_saved=float(tokens_saved),
                                message_length=len(request.message),
                                request_count=1
                            )
                            db.add(usage)
                            db.commit()
                    except Exception as e:
                        print(f"[MASTER PROXY] Erro ao registrar créditos: {e}")
                
                return MasterProxyResponse(
                    success=True,
                    message="Mensagem enviada com sucesso!",
                    credits_saved=True
                )
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Token inválido ou expirado")
            elif response.status_code == 403:
                raise HTTPException(status_code=403, detail="Sem permissão neste projeto")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erro ao enviar para Lovable: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout ao conectar com Lovable API")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar requisição: {str(e)}")


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
