"""
ChatLove Master Proxy
Servidor que usa credenciais de uma conta master do Lovable
para enviar mensagens sem consumir créditos do usuário final.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import httpx
import os
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = FastAPI(title="ChatLove Master Proxy API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração da conta master
MASTER_SESSION_TOKEN = os.getenv("MASTER_SESSION_TOKEN", "")
LOVABLE_API_URL = "https://api.lovable.dev"

# Models
class MasterProxyRequest(BaseModel):
    project_id: str
    message: str
    session_token: str  # Token capturado automaticamente pela extension
    license_key: Optional[str] = None  # Opcional, só para validação

class MasterProxyResponse(BaseModel):
    success: bool
    message: str
    credits_saved: bool = True

# =============================================================================
# ROUTES
# =============================================================================

@app.get("/")
async def root():
    return {
        "name": "ChatLove Master Proxy API",
        "version": "1.0.0",
        "status": "running",
        "description": "Proxy que usa conta master do Lovable"
    }

@app.post("/api/master-proxy", response_model=MasterProxyResponse)
async def master_proxy(request: MasterProxyRequest):
    """
    Recebe mensagem do usuário e envia para Lovable usando conta master.
    
    Fluxo:
    1. Recebe mensagem da extension
    2. Valida project_id
    3. Envia para API do Lovable usando token da conta master
    4. Preview atualiza no projeto do usuário
    5. Créditos são consumidos da conta master
    """
    
    # Log da requisição recebida
    print(f"[MASTER PROXY] Requisição recebida:")
    print(f"  Project ID: {request.project_id}")
    print(f"  Message: {request.message[:50]}...")
    print(f"  License Key: {request.license_key}")
    print(f"  Session Token: {request.session_token[:50]}...")
    
    # Usar token recebido da extension (dinâmico)
    session_token = request.session_token
    
    if not session_token:
        print("[MASTER PROXY] ERRO: Session token não fornecido!")
        raise HTTPException(
            status_code=400,
            detail="Session token não fornecido pela extension."
        )
    
    # Validar project_id
    if not request.project_id:
        print("[MASTER PROXY] ERRO: Project ID vazio!")
        raise HTTPException(
            status_code=400,
            detail="Project ID não fornecido"
        )
    
    # Validar mensagem
    if not request.message or not request.message.strip():
        print("[MASTER PROXY] ERRO: Mensagem vazia!")
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia"
        )
    
    # Preparar requisição para Lovable
    lovable_url = f"{LOVABLE_API_URL}/projects/{request.project_id}/chat"
    
    # Usar token dinâmico capturado pela extension
    headers = {
        "Authorization": f"Bearer {session_token}",  # ← Token dinâmico!
        "Content-Type": "application/json",
        "User-Agent": "ChatLove-Master-Proxy/1.0"
    }
    
    payload = {
        "message": request.message,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"[MASTER PROXY] Enviando para Lovable:")
    print(f"  URL: {lovable_url}")
    print(f"  Payload: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                lovable_url,
                headers=headers,
                json=payload
            )
            
            print(f"[MASTER PROXY] Resposta do Lovable:")
            print(f"  Status: {response.status_code}")
            print(f"  Body: {response.text[:200] if response.text else '(vazio)'}")
            
            # 200 OK ou 202 Accepted = Sucesso
            if response.status_code in [200, 202]:
                print("[MASTER PROXY] ✅ Sucesso! Mensagem aceita pelo Lovable.")
                
                # Registrar créditos no backend
                tokens_saved = len(request.message) / 4  # Estimativa: 4 chars = 1 token
                
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        await client.post(
                            "http://127.0.0.1:8000/api/credits/log",
                            json={
                                "license_key": request.license_key,
                                "tokens_saved": tokens_saved,
                                "message_length": len(request.message)
                            }
                        )
                        print(f"[MASTER PROXY] Créditos registrados: {tokens_saved:.2f}")
                except Exception as e:
                    print(f"[MASTER PROXY] Erro ao registrar créditos: {e}")
                
                return MasterProxyResponse(
                    success=True,
                    message="Mensagem enviada com sucesso usando conta master!",
                    credits_saved=True
                )
            elif response.status_code == 401:
                print("[MASTER PROXY] ❌ Token inválido!")
                raise HTTPException(
                    status_code=401,
                    detail="Token da conta master inválido ou expirado. Atualize MASTER_SESSION_TOKEN."
                )
            elif response.status_code == 403:
                print("[MASTER PROXY] ❌ Sem permissão! Use projeto da conta master.")
                raise HTTPException(
                    status_code=403,
                    detail="Sem permissão neste projeto. Use um projeto da conta master ou compartilhe o projeto com ela."
                )
            else:
                print(f"[MASTER PROXY] ❌ Erro {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erro ao enviar para Lovable: {response.text}"
                )
                
    except httpx.TimeoutException as e:
        print(f"[MASTER PROXY] ❌ Timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail="Timeout ao conectar com Lovable API"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MASTER PROXY] ❌ Erro inesperado: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar requisição: {str(e)}"
        )

@app.get("/health")
async def health():
    """Health check"""
    has_token = bool(MASTER_SESSION_TOKEN)
    
    return {
        "status": "healthy" if has_token else "warning",
        "timestamp": datetime.now().isoformat(),
        "master_token_configured": has_token,
        "message": "OK" if has_token else "Configure MASTER_SESSION_TOKEN"
    }

@app.get("/api/validate-master-token")
async def validate_master_token():
    """Valida se o token da conta master está configurado e válido"""
    
    if not MASTER_SESSION_TOKEN:
        return {
            "valid": False,
            "message": "Token não configurado"
        }
    
    try:
        # Testar token fazendo uma requisição simples
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{LOVABLE_API_URL}/user/me",
                headers={"Authorization": f"Bearer {MASTER_SESSION_TOKEN}"}
            )
            
            if response.status_code == 200:
                return {
                    "valid": True,
                    "message": "Token válido",
                    "account": response.json()
                }
            else:
                return {
                    "valid": False,
                    "message": f"Token inválido (status {response.status_code})"
                }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Erro ao validar: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("CHATLOVE MASTER PROXY API")
    print("=" * 60)
    print("Server: http://127.0.0.1:8002")
    print("Função: Usar conta master para enviar mensagens")
    print("Créditos consumidos da conta master!")
    print("=" * 60)
    
    if not MASTER_SESSION_TOKEN:
        print("⚠️  AVISO: MASTER_SESSION_TOKEN não configurado!")
        print("Configure a variável de ambiente antes de usar.")
        print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8002)
