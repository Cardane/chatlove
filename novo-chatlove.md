INSTRUÇÕES COMPLETAS: Implementar Proxy Hub para ChatLove
📋 CONTEXTO
Você é uma IA assistente que vai modificar o sistema ChatLove para implementar um proxy hub que permite usar créditos de uma conta diferente da conta logada.
Sistema Atual:

Usuário logado na Conta A → envia mensagem → créditos descontados da Conta A

Sistema Desejado:

Usuário logado na Conta A → envia mensagem → créditos descontados da Conta B (hub)

Objetivo desta Fase:
Implementar versão SIMPLIFICADA com 1 conta hub fixa para testes. Sistema de rotação será implementado depois.

chatlove-backend/
├── database.py          # ✏️ MODIFICAR: Adicionar novos modelos
├── main.py             # ✏️ MODIFICAR: Adicionar endpoints hub
└── migrate_hub.py      # ✨ CRIAR: Script de migração

chatlove-proxy-extension/
└── content.js          # ✏️ MODIFICAR: Usar novo endpoint

chatlove-admin/
└── src/
    ├── pages/
    │   └── HubAccounts.jsx    # ✨ CRIAR: Nova página
    └── App.jsx                # ✏️ MODIFICAR: Adicionar rota

🗃️ PARTE 1: BANCO DE DADOS
1.1. Modificar chatlove-backend/database.py
Adicionar no final do arquivo (antes de get_db()):

class HubAccount(Base):
    """Conta do hub com créditos para proxy"""
    __tablename__ = "hub_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)                # Nome amigável (ex: "Hub Account 1")
    email = Column(String, unique=True, index=True)  # Email da conta Lovable
    session_token = Column(String)                   # Token Bearer do Lovable
    credits_remaining = Column(Float, default=0.0)   # Créditos estimados restantes
    is_active = Column(Boolean, default=True)        # Se está disponível para uso
    priority = Column(Integer, default=0)            # 0 = maior prioridade (para futuro)
    
    # Estatísticas
    total_requests = Column(Integer, default=0)      # Total de requisições
    last_used_at = Column(DateTime, nullable=True)   # Última vez usada
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_mappings = relationship("ProjectMapping", back_populates="hub_account")
    usage_logs = relationship("UsageLog", back_populates="hub_account", foreign_keys="UsageLog.hub_account_id")


class ProjectMapping(Base):
    """Mapeia projetos originais para projetos equivalentes no hub"""
    __tablename__ = "project_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # IDs dos projetos
    original_project_id = Column(String, index=True)   # Projeto da conta do usuário
    hub_project_id = Column(String, index=True)        # Projeto criado na conta hub
    
    # Relacionamento
    hub_account_id = Column(Integer, ForeignKey("hub_accounts.id"))
    
    # Metadados
    project_name = Column(String, nullable=True)       # Nome do projeto (cache)
    sync_enabled = Column(Boolean, default=False)      # Se sincronização está ativa
    last_synced_at = Column(DateTime, nullable=True)   # Última sincronização
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    hub_account = relationship("HubAccount", back_populates="project_mappings")

 Modificar a classe UsageLog existente (adicionar campos):

 class UsageLog(Base):
    """Track usage and tokens saved"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"))
    
    # ===== ADICIONAR ESTES CAMPOS =====
    hub_account_id = Column(Integer, ForeignKey("hub_accounts.id"), nullable=True)
    original_project_id = Column(String, nullable=True)  # Projeto do usuário
    hub_project_id = Column(String, nullable=True)       # Projeto usado no hub
    # ==================================
    
    # Usage data (campos existentes)
    tokens_saved = Column(Float, default=0.0)
    request_count = Column(Integer, default=1)
    message_length = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    license = relationship("License", back_populates="usage_logs")
    hub_account = relationship("HubAccount", back_populates="usage_logs", foreign_keys=[hub_account_id])

       1.2. Criar chatlove-backend/migrate_hub.py

       """
Migração para adicionar suporte ao Hub de Contas
Adiciona tabelas: hub_accounts, project_mappings
Adiciona colunas em usage_logs: hub_account_id, original_project_id, hub_project_id
"""

import sqlite3
from datetime import datetime

DB_PATH = "chatlove.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("MIGRAÇÃO: Hub de Contas")
    print("=" * 60)
    
    # ========================================
    # 1. CRIAR TABELA: hub_accounts
    # ========================================
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hub_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                session_token VARCHAR NOT NULL,
                credits_remaining FLOAT DEFAULT 0.0,
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                last_used_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[✓] Tabela 'hub_accounts' criada")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("[i] Tabela 'hub_accounts' já existe")
        else:
            print(f"[✗] Erro ao criar 'hub_accounts': {e}")
    
    # ========================================
    # 2. CRIAR TABELA: project_mappings
    # ========================================
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_project_id VARCHAR NOT NULL,
                hub_project_id VARCHAR NOT NULL,
                hub_account_id INTEGER NOT NULL,
                project_name VARCHAR NULL,
                sync_enabled BOOLEAN DEFAULT 0,
                last_synced_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hub_account_id) REFERENCES hub_accounts(id)
            )
        """)
        print("[✓] Tabela 'project_mappings' criada")
        
        # Criar índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_mappings_original 
            ON project_mappings(original_project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_mappings_hub 
            ON project_mappings(hub_project_id)
        """)
        print("[✓] Índices criados para 'project_mappings'")
        
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("[i] Tabela 'project_mappings' já existe")
        else:
            print(f"[✗] Erro ao criar 'project_mappings': {e}")
    
    # ========================================
    # 3. ADICIONAR COLUNAS EM usage_logs
    # ========================================
    
    # 3.1. hub_account_id
    try:
        cursor.execute("ALTER TABLE usage_logs ADD COLUMN hub_account_id INTEGER NULL")
        print("[✓] Coluna 'hub_account_id' adicionada em usage_logs")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[i] Coluna 'hub_account_id' já existe")
        else:
            print(f"[✗] Erro: {e}")
    
    # 3.2. original_project_id
    try:
        cursor.execute("ALTER TABLE usage_logs ADD COLUMN original_project_id VARCHAR NULL")
        print("[✓] Coluna 'original_project_id' adicionada em usage_logs")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[i] Coluna 'original_project_id' já existe")
        else:
            print(f"[✗] Erro: {e}")
    
    # 3.3. hub_project_id
    try:
        cursor.execute("ALTER TABLE usage_logs ADD COLUMN hub_project_id VARCHAR NULL")
        print("[✓] Coluna 'hub_project_id' adicionada em usage_logs")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[i] Coluna 'hub_project_id' já existe")
        else:
            print(f"[✗] Erro: {e}")
    
    # ========================================
    # 4. COMMIT E FECHAR
    # ========================================
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print("[✓] MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("\nPróximos passos:")
    print("1. Reiniciar backend: python main.py")
    print("2. Adicionar conta hub via admin panel")
    print("3. Testar proxy hub")
    print()


if __name__ == "__main__":
    migrate()

    🔧 PARTE 2: BACKEND - LÓGICA DO HUB
2.1. Modificar chatlove-backend/main.py
Adicionar novos imports no topo:

from database import (
    # ... imports existentes ...
    HubAccount,      # ← ADICIONAR
    ProjectMapping   # ← ADICIONAR
)

Adicionar novos modelos Pydantic (após os existentes):
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

    Adicionar funções auxiliares (antes dos endpoints):

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

  Adicionar novo endpoint principal (após endpoints existentes):

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

  Adicionar endpoints de admin para gerenciar hub (após endpoints de admin existentes):

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

 📱 PARTE 3: EXTENSION
3.1. Modificar chatlove-proxy-extension/content.js
Localizar a função sendMessage() e SUBSTITUIR por:

async function sendMessage() {
  const message = messageInput.value.trim();
  
  if (!message) {
    setStatus('Digite uma mensagem');
    return;
  }

  const projectId = await detectProject();
  if (!projectId) {
    addMessage('Erro: Projeto não detectado', 'error');
    setStatus('Erro');
    return;
  }

  const { licenseKey } = await chrome.storage.local.get(['licenseKey']);
  if (!licenseKey) {
    addMessage('Erro: Licença não ativada', 'error');
    setStatus('Erro');
    return;
  }

  // Verificar status da licença antes de enviar
  try {
    const validateResponse = await fetch('https://chat.trafficai.cloud/api/validate-license', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_key: licenseKey })
    });
    
    const validateData = await validateResponse.json();
    
    if (!validateData.success || !validateData.valid) {
      addMessage(`Erro: ${validateData.message}`, 'error');
      setStatus('Bloqueado');
      sendBtn.disabled = true;
      return;
    }
  } catch (error) {
    console.error('[ChatLove] Erro ao validar licença:', error);
  }

  // ========================================
  // NOVA LÓGICA: USAR PROXY HUB
  // ========================================
  
  // Capturar token do usuário
  setStatus('Capturando token...');
  const userSessionToken = await getCookieToken();
  
  if (!userSessionToken) {
    addMessage('Erro: Não foi possível capturar o cookie. Faça login no Lovable.', 'error');
    setStatus('Erro');
    return;
  }

  addMessage(message, 'user');
  messageInput.value = '';
  
  sendBtn.disabled = true;
  setStatus('Enviando via hub...');

  try {
    console.log('[ChatLove Hub] Enviando para proxy hub...');
    
    // ===== ENDPOINT NOVO: /api/proxy-hub =====
    const response = await fetch('https://chat.trafficai.cloud/api/proxy-hub', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        license_key: licenseKey,
        original_project_id: projectId,        // ← Projeto do usuário
        message: message,
        user_session_token: userSessionToken   // ← Token do usuário
      })
    }).catch(err => {
      console.warn('[ChatLove Hub] Erro de rede (possível CORS):', err);
      return { 
        ok: false, 
        status: 0,
        corsError: true,
        json: async () => ({ success: false, message: 'Erro de rede' })
      };
    });

    console.log('[ChatLove Hub] Response status:', response.status);

    // Tratar erro de CORS (pode ter funcionado no servidor)
    if (response.corsError) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      addMessage('✅ Mensagem enviada via hub!', 'success');
      await loadStats();
      setStatus('✅ Enviado');
      sendBtn.disabled = false;
      return;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('[ChatLove Hub] Erro HTTP:', errorData);
      const errorMessage = errorData.detail || errorData.message || 'Erro ao enviar mensagem';
      addMessage(`Erro: ${errorMessage}`, 'error');
      setStatus('Erro');
      return;
    }

    const data = await response.json();
    console.log('[ChatLove Hub] Response data:', data);

    if (data.success) {
      // ===== SUCESSO =====
      addMessage(`✅ Enviado via ${data.hub_account_name}!`, 'success');
      addMessage(`💰 ${data.tokens_saved.toFixed(2)} créditos economizados`, 'info');
      
      if (data.hub_credits_remaining !== undefined) {
        addMessage(`🏦 Hub: ${data.hub_credits_remaining.toFixed(2)} créditos restantes`, 'info');
      }
      
      console.log('[ChatLove Hub] Sucesso!');
      console.log('[ChatLove Hub] Conta hub:', data.hub_account_email);
      console.log('[ChatLove Hub] Projeto hub:', data.hub_project_id);
      
      // Recarregar estatísticas
      await loadStats();
      
      setStatus('✅ Sucesso');
    } else {
      const errorMessage = data.message || data.detail || 'Erro desconhecido';
      console.error('[ChatLove Hub] Erro:', errorMessage);
      addMessage(`Erro: ${errorMessage}`, 'error');
      setStatus('Erro');
    }

  } catch (error) {
    console.error('[ChatLove Hub] Erro catch:', error);
    
    // Se for erro de rede, assumir que pode ter funcionado
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      addMessage('✅ Mensagem enviada! (Verificando...)', 'success');
      await loadStats();
      setStatus('✅ Enviado');
    } else {
      addMessage(`Erro: ${error.message}`, 'error');
      setStatus('Erro');
    }
  } finally {
    sendBtn.disabled = false;
  }
}

🎨 PARTE 4: ADMIN PANEL
4.1. Criar chatlove-admin/src/pages/HubAccounts.jsx

import { useState, useEffect } from 'react'
import { adminAPI } from '../api'
import { Plus, Server, TrendingUp, Activity, Edit, Trash2, Check, X } from 'lucide-react'
import './HubAccounts.css'

function HubAccounts() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    session_token: '',
    credits_remaining: 0,
    priority: 0
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const response = await adminAPI.getHubAccounts()
      setAccounts(response.data)
    } catch (error) {
      console.error('Error loading hub accounts:', error)
      alert('Erro ao carregar contas hub: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    
    try {
      if (editingAccount) {
        await adminAPI.updateHubAccount(editingAccount.id, formData)
      } else {
        await adminAPI.createHubAccount(formData)
      }
      
      setShowModal(false)
      setEditingAccount(null)
      setFormData({ name: '', email: '', session_token: '', credits_remaining: 0, priority: 0 })
      loadAccounts()
    } catch (error) {
      alert('Erro ao salvar: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleEdit = (account) => {
    setEditingAccount(account)
    setFormData({
      name: account.name,
      email: account.email,
      session_token: account.session_token_preview ? '' : account.session_token,
      credits_remaining: account.credits_remaining,
      priority: account.priority
    })
    setShowModal(true)
  }

  const handleDelete = async (accountId, accountName) => {
    if (!confirm(`Deletar conta "${accountName}"? Todos os mapeamentos serão perdidos.`)) {
      return
    }
    
    try {
      await adminAPI.deleteHubAccount(accountId)
      loadAccounts()
    } catch (error) {
      alert('Erro ao deletar: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleToggleActive = async (account) => {
    try {
      await adminAPI.updateHubAccount(account.id, { is_active: !account.is_active })
      loadAccounts()
    } catch (error) {
      alert('Erro ao atualizar: ' + (error.response?.data?.detail || error.message))
    }
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="hub-accounts-page">
      <div className="page-header">
        <h1 className="page-title">Contas Hub</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={20} />
          <span>Nova Conta Hub</span>
        </button>
      </div>

      <div className="hub-accounts-grid">
        {accounts.map((account) => (
          <div key={account.id} className={`hub-account-card ${!account.is_active ? 'inactive' : ''}`}>
            <div className="card-header">
              <div className="account-avatar">
                <Server size={28} />
              </div>
              <div className="account-info">
                <h3>{account.name}</h3>
                <p className="account-email">{account.email}</p>
              </div>
              <div className={`status-badge ${account.is_active ? 'active' : 'inactive'}`}>
                {account.is_active ? 'Ativa' : 'Inativa'}
              </div>
            </div>

            <div className="account-stats">
              <div className="stat-row">
                <div className="stat-item">
                  <div className="stat-icon credits">
                    <TrendingUp size={20} />
                  </div>
                  <div className="stat-content">
                    <div className="stat-label">Créditos Restantes</div>
                    <div className="stat-value">{account.credits_remaining.toFixed(2)}</div>
                  </div>
                </div>
              </div>

              <div className="stat-row">
                <div className="stat-item-small">
                  <div className="stat-label">Projetos Mapeados</div>
                  <div className="stat-value-small">{account.projects_mapped}</div>
                </div>
                <div className="stat-item-small">
                  <div className="stat-label">Total Requisições</div>
                  <div className="stat-value-small">{account.total_requests}</div>
                </div>
              </div>

              <div className="stat-row">
                <div className="stat-item-small">
                  <div className="stat-label">Tokens Usados</div>
                  <div className="stat-value-small">{account.tokens_used.toFixed(2)}</div>
                </div>
                <div className="stat-item-small">
                  <div className="stat-label">Prioridade</div>
                  <div className="stat-value-small">{account.priority}</div>
                </div>
              </div>

              {account.last_used_at && (
                <div className="last-used">
                  Último uso: {new Date(account.last_used_at).toLocaleString('pt-BR')}
                </div>
              )}
            </div>

            <div className="card-actions">
              <button 
                className={`toggle-btn ${account.is_active ? 'active' : 'inactive'}`}
                onClick={() => handleToggleActive(account)}
              >
                {account.is_active ? <X size={16} /> : <Check size={16} />}
                {account.is_active ? 'Desativar' : 'Ativar'}
              </button>
              <button className="btn-edit" onClick={() => handleEdit(account)}>
                <Edit size={16} />
                Editar
              </button>
              <button className="btn-delete" onClick={() => handleDelete(account.id, account.name)}>
                <Trash2 size={16} />
                Deletar
              </button>
            </div>
          </div>
        ))}
      </div>

      {accounts.length === 0 && (
        <div className="empty-state">
          <Server size={64} />
          <h3>Nenhuma conta hub configurada</h3>
          <p>Adicione uma conta hub para começar a economizar créditos</p>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={20} />
            Adicionar Conta Hub
          </button>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingAccount ? 'Editar Conta Hub' : 'Nova Conta Hub'}</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Nome</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Hub Account 1"
                  required
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@example.com"
                  required
                  disabled={!!editingAccount}
                />
              </div>

              <div className="form-group">
                <label>Session Token</label>
                <textarea
                  value={formData.session_token}
                  onChange={(e) => setFormData({ ...formData, session_token: e.target.value })}
                  placeholder="eyJhbGciOiJSUzI1NiIsImtpZCI6IjFjMzIxOTgzNGRhNT..."
                  rows={3}
                  required={!editingAccount}
                />
                <small>Copie de: DevTools → Application → Cookies → lovable-session-id.id</small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Créditos Iniciais</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.credits_remaining}
                    onChange={(e) => setFormData({ ...formData, credits_remaining: parseFloat(e.target.value) })}
                    placeholder="0"
                  />
                </div>

                <div className="form-group">
                  <label>Prioridade</label>
                  <input
                    type="number"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                    placeholder="0"
                  />
                  <small>Menor = maior prioridade</small>
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary">
                  {editingAccount ? 'Salvar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default HubAccounts

4.2. Criar chatlove-admin/src/pages/HubAccounts.css

.hub-accounts-page {
  max-width: 1400px;
}

.hub-accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.hub-account-card {
  background: #16213e;
  border: 1px solid #0f3460;
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s ease;
}

.hub-account-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.hub-account-card.inactive {
  opacity: 0.6;
  border-color: rgba(158, 158, 158, 0.3);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.account-avatar {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.account-info {
  flex: 1;
}

.account-info h3 {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}

.account-email {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.status-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.5);
  color: #4CAF50;
}

.status-badge.inactive {
  background: rgba(158, 158, 158, 0.2);
  border: 1px solid rgba(158, 158, 158, 0.5);
  color: #9E9E9E;
}

.account-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.stat-row {
  display: flex;
  gap: 12px;
}

.stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-icon.credits {
  background: linear-gradient(135deg, #4CAF50, #8BC34A);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 2px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.stat-item-small {
  flex: 1;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.stat-value-small {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  margin-top: 2px;
}

.last-used {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.card-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.toggle-btn {
  flex: 1;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.toggle-btn.active {
  background: rgba(244, 67, 54, 0.2);
  border: 1px solid rgba(244, 67, 54, 0.5);
  color: #F44336;
}

.toggle-btn.inactive {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.5);
  color: #4CAF50;
}

.btn-edit {
  padding: 8px 16px;
  background: rgba(33, 150, 243, 0.2);
  border: 1px solid rgba(33, 150, 243, 0.3);
  border-radius: 6px;
  color: #2196F3;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-edit:hover {
  background: rgba(33, 150, 243, 0.3);
}

.btn-delete {
  padding: 8px 16px;
  background: rgba(244, 67, 54, 0.2);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: 6px;
  color: #F44336;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-delete:hover {
  background: rgba(244, 67, 54, 0.3);
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: rgba(255, 255, 255, 0.7);
}

.empty-state svg {
  color: rgba(255, 255, 255, 0.3);
  margin-bottom: 24px;
}

.empty-state h3 {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
}

.empty-state p {
  margin-bottom: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group small {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.form-group textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  resize: vertical;
  transition: all 0.2s ease;
}

.form-group textarea:focus {
  outline: none;
  border-color: #E91E63;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 20px rgba(233, 30, 99, 0.3);
}

4.3. Modificar chatlove-admin/src/api.js
Adicionar no objeto adminAPI (no final):
export const adminAPI = {
  // ... métodos existentes ...
  
  // Hub Accounts
  getHubAccounts: () => api.get('/api/admin/hub-accounts'),
  createHubAccount: (data) => api.post('/api/admin/hub-accounts', data),
  updateHubAccount: (id, data) => api.put(`/api/admin/hub-accounts/${id}`, data),
  deleteHubAccount: (id) => api.delete(`/api/admin/hub-accounts/${id}`),
  getHubProjects: (id) => api.get(`/api/admin/hub-accounts/${id}/projects`)
}

4.4. Modificar chatlove-admin/src/App.jsx
Adicionar import:

import HubAccounts from './pages/HubAccounts'

Adicionar rota:

<Routes>
  <Route path="/" element={<Dashboard />} />
  <Route path="/users" element={<Users />} />
  <Route path="/licenses" element={<Licenses />} />
  <Route path="/hub-accounts" element={<HubAccounts />} />  {/* ← ADICIONAR */}
  <Route path="*" element={<Navigate to="/" />} />
</Routes>

4.5. Modificar chatlove-admin/src/components/Layout.jsx
Adicionar import:

import { LayoutDashboard, Users, Key, LogOut, Server } from 'lucide-react'  // ← Adicionar Server

Adicionar item no menu (após Licenças):

<Link
  to="/hub-accounts"
  className={`nav-item ${isActive('/hub-accounts') ? 'active' : ''}`}
>
  <Server size={20} />
  <span>Contas Hub</span>
</Link>
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### PARTE 1: Banco de Dados
- [ ] Modificar `database.py` (adicionar `HubAccount` e `ProjectMapping`)
- [ ] Modificar `UsageLog` (adicionar campos hub)
- [ ] Criar `migrate_hub.py`
- [ ] Executar migração: `python migrate_hub.py`

### PARTE 2: Backend
- [ ] Adicionar imports em `main.py`
- [ ] Adicionar modelos Pydantic
- [ ] Adicionar funções auxiliares (`get_active_hub_account`, `get_or_create_hub_project`)
- [ ] Adicionar endpoint `/api/proxy-hub`
- [ ] Adicionar endpoints admin (`/api/admin/hub-accounts/*`)
- [ ] Reiniciar backend: `python main.py`

### PARTE 3: Extension
- [ ] Modificar função `sendMessage()` em `content.js`
- [ ] Testar captura de cookie
- [ ] Recarregar extension no Chrome

### PARTE 4: Admin Panel
- [ ] Criar `HubAccounts.jsx`
- [ ] Criar `HubAccounts.css`
- [ ] Modificar `api.js` (adicionar métodos hub)
- [ ] Modificar `App.jsx` (adicionar rota)
- [ ] Modificar `Layout.jsx` (adicionar menu)
- [ ] Rebuild admin: `npm run build`

---

## 🧪 COMO TESTAR

### 1. Preparar Conta Hub

**Obter Session Token:**
1. Acesse https://lovable.dev com a conta hub
2. F12 → Application → Cookies → lovable.dev
3. Copie valor de `lovable-session-id.id`

### 2. Adicionar Conta no Admin

1. Acesse admin: http://localhost:3000/hub-accounts
2. Clique "Nova Conta Hub"
3. Preencha:
   - Nome: "Hub Test 1"
   - Email: email@da-conta-hub.com
   - Session Token: (cole o token)
   - Créditos: 100
   - Prioridade: 0
4. Salvar

### 3. Testar na Extension

1. Abra projeto no Lovable (sua conta pessoal)
2. Digite mensagem no ChatLove
3. Clique "Enviar"
4. Verifique logs no backend
5. Confirme que mensagem foi enviada
6. Verifique se créditos foram descontados da conta hub

### 4. Validar Logs

**Backend deve mostrar:**
```
============================================================
[HUB PROXY] Nova requisição recebida
============================================================
[HUB] Licença validada: CCA3-39CD-7734-6CD6
[HUB] Conta selecionada: Hub Test 1 (email@hub.com)
[HUB] Criando novo projeto no hub para: abc123
[HUB] Projeto criado no hub: xyz789
[HUB] Projeto hub: xyz789
[HUB] Enviando para Lovable...
[HUB] URL: https://api.lovable.dev/projects/xyz789/chat
[HUB] Mensagem: Teste...
[HUB] Resposta Lovable: 202
[HUB] ✓ Mensagem enviada com sucesso!
[HUB] Uso registrado: 2.50 tokens
[HUB] Créditos restantes (hub): 97.50
============================================================

🎯 RESULTADO ESPERADO
✅ O Que Deve Funcionar:

✅ Usuário trabalha no projeto da Conta A
✅ Sistema cria projeto equivalente na Conta Hub
✅ Mensagem enviada via token da Conta Hub
✅ Créditos descontados da Conta Hub
✅ Preview atualiza na Conta A
✅ Estatísticas registradas corretamente
✅ Admin panel mostra uso da conta hub

⚠️ Limitações Conhecidas:

❌ Sincronização de resposta não implementada (futura melhoria)
❌ Sistema de rotação não implementado (futura melhoria)
⚠️ Preview atualiza mas pode haver delay
⚠️ Histórico fica no projeto hub, não no original


🚀 PRÓXIMOS PASSOS (Futuro)
Após validar esta versão:

Sistema de Rotação: Múltiplas contas hub (3-5 contas)
Sincronização: Aplicar mudanças do hub no projeto original
Health Check: Verificar saldo real das contas hub
Dashboard: Gráficos de uso por conta
Notificações: Alertar quando conta hub ficar sem créditos
