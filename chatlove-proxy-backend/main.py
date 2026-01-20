"""
ChatLove Proxy Backend
Proxy que simula envio para Lovable SEM consumir créditos
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3
from typing import Optional

app = FastAPI(title="ChatLove Proxy API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = "../chatlove-backend/chatlove.db"

# Models
class ProxyRequest(BaseModel):
    license_key: str
    project_id: str
    message: str

class ProxyResponse(BaseModel):
    success: bool
    message: str
    credits_saved: bool = True

# Database functions
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def validate_license(license_key: str) -> bool:
    """Valida se a licença está ativa"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM licenses WHERE license_key = ? AND is_active = 1",
            (license_key,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Erro ao validar licença: {e}")
        return False

def save_message(project_id: str, message: str, license_key: str):
    """Salva mensagem no histórico"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxy_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                message TEXT NOT NULL,
                license_key TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inserir mensagem
        cursor.execute(
            "INSERT INTO proxy_messages (project_id, message, license_key) VALUES (?, ?, ?)",
            (project_id, message, license_key)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar mensagem: {e}")

# Routes
@app.get("/")
async def root():
    return {
        "name": "ChatLove Proxy API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/lovable-proxy", response_model=ProxyResponse)
async def lovable_proxy(request: ProxyRequest):
    """
    Proxy que simula envio para Lovable
    NÃO consome créditos reais
    
    Fluxo:
    1. Valida licença
    2. Registra mensagem
    3. Retorna sucesso (fake)
    4. Extension injeta no DOM do Lovable
    5. Preview atualiza SEM salvar
    6. Usuário clica manualmente para salvar (1 crédito)
    """
    
    # 1. Validar licença
    if not validate_license(request.license_key):
        raise HTTPException(
            status_code=401,
            detail="Licença inválida ou inativa"
        )
    
    # 2. Validar project_id
    if not request.project_id:
        raise HTTPException(
            status_code=400,
            detail="Project ID não fornecido"
        )
    
    # 3. Validar mensagem
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia"
        )
    
    # 4. Salvar mensagem no histórico
    save_message(request.project_id, request.message, request.license_key)
    
    # 5. Retornar sucesso (fake)
    return ProxyResponse(
        success=True,
        message="Mensagem enviada ao preview (não salvo). Para salvar, envie uma mensagem simples no chat real do Lovable.",
        credits_saved=True
    )

@app.get("/api/proxy-history/{project_id}")
async def get_proxy_history(project_id: str, license_key: str):
    """Retorna histórico de mensagens do projeto"""
    
    # Validar licença
    if not validate_license(license_key):
        raise HTTPException(
            status_code=401,
            detail="Licença inválida"
        )
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT message, timestamp 
            FROM proxy_messages 
            WHERE project_id = ? AND license_key = ?
            ORDER BY timestamp DESC
            LIMIT 50
            """,
            (project_id, license_key)
        )
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "message": row[0],
                "timestamp": row[1]
            })
        
        conn.close()
        
        return {
            "success": True,
            "project_id": project_id,
            "messages": messages
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar histórico: {str(e)}"
        )

@app.post("/api/validate-license")
async def validate_license_endpoint(request: dict):
    """Valida se uma licença existe e está ativa"""
    license_key = request.get("license_key")
    
    if not license_key:
        return {"success": False, "valid": False, "message": "Chave de licença não fornecida"}
    
    is_valid = validate_license(license_key)
    
    if is_valid:
        # Marcar licença como usada
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE licenses SET is_used = 1 WHERE license_key = ?",
                (license_key,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao atualizar licença: {e}")
        
        return {"success": True, "valid": True, "message": "Licença válida"}
    else:
        return {"success": False, "valid": False, "message": "Licença inválida ou inativa"}


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("CHATLOVE PROXY API")
    print("=" * 60)
    print("Server: http://127.0.0.1:8001")
    print("Função: Validar licenças e registrar mensagens")
    print("NÃO consome créditos do Lovable!")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8001)
