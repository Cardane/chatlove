# 🚀 Sistema de Automação Lovable - Documentação Técnica

## 📋 Visão Geral

Sistema Python para automatizar interações com Lovable.dev, permitindo que o ChatLove use a API do Lovable sem consumir créditos dos usuários finais. O sistema utiliza automação de navegador para interceptar e reutilizar sessões autenticadas.

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────┐
│           CHATLOVE FRONTEND (React)                 │
│  Interface web para usuários finais                │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/WebSocket
                   ▼
┌─────────────────────────────────────────────────────┐
│        CHATLOVE BACKEND (FastAPI/Python)            │
│  - Validação de licenças                           │
│  - Gerenciamento de usuários                       │
│  - Proxy para Lovable Automation                   │
└──────────────────┬──────────────────────────────────┘
                   │ Internal API
                   ▼
┌─────────────────────────────────────────────────────┐
│     LOVABLE AUTOMATION SERVICE (Python)             │
│  ┌───────────────────────────────────────────┐     │
│  │  🔐 Session Manager                       │     │
│  │  - Autenticação Firebase                  │     │
│  │  - Gerenciamento de tokens                │     │
│  │  - Refresh automático                     │     │
│  │  - Pool de sessões ativas                 │     │
│  └───────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────┐     │
│  │  🌐 Browser Automation                    │     │
│  │  - Playwright headless                    │     │
│  │  - Controle de múltiplos navegadores      │     │
│  │  - Interceptação de requests/responses    │     │
│  │  - Injeção de mensagens                   │     │
│  └───────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────┐     │
│  │  📡 API Interceptor                       │     │
│  │  - Captura de streaming responses         │     │
│  │  - Extração de código gerado              │     │
│  │  - Parsing de mensagens                   │     │
│  │  - Retorno estruturado                    │     │
│  └───────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────┐     │
│  │  ⚡ Queue Manager                         │     │
│  │  - Fila de mensagens                      │     │
│  │  - Rate limiting                          │     │
│  │  - Retry logic                            │     │
│  │  - Load balancing                         │     │
│  └───────────────────────────────────────────┘     │
└──────────────────┬──────────────────────────────────┘
                   │ Automated Browser
                   ▼
┌─────────────────────────────────────────────────────┐
│           LOVABLE.DEV (Target API)                  │
│  - Processamento real de mensagens                 │
│  - Geração de código                               │
│  - Streaming responses                             │
└─────────────────────────────────────────────────────┘
```

## 🔧 Componentes Principais

### 1. 🔐 Session Manager

**Responsabilidades:**
- Autenticação automática via Firebase
- Manutenção de sessões ativas
- Refresh de tokens expirados
- Pool de múltiplas contas Lovable

**Funcionalidades:**
```python
class LovableSessionManager:
    async def authenticate(email: str, password: str) -> Session
    async def refresh_session(session: Session) -> Session
    async def get_active_session() -> Session
    async def maintain_presence(session: Session) -> None
    async def handle_session_expiry(session: Session) -> Session
    async def create_session_pool(accounts: List[Account]) -> SessionPool
```

### 2. 🌐 Browser Automation

**Responsabilidades:**
- Controle de navegadores headless
- Navegação automática
- Injeção de mensagens no chat
- Interceptação de responses

**Funcionalidades:**
```python
class LovableBrowserAutomation:
    async def launch_browser(headless: bool = True) -> Browser
    async def navigate_to_project(project_id: str) -> Page
    async def send_chat_message(message: str) -> None
    async def wait_for_response() -> ChatResponse
    async def extract_generated_code() -> CodeChanges
    async def intercept_network_traffic() -> NetworkInterceptor
```

### 3. 📡 API Interceptor

**Responsabilidades:**
- Captura de requisições HTTP
- Parsing de streaming responses
- Extração de dados estruturados
- Conversão para formato ChatLove

**Funcionalidades:**
```python
class LovableAPIInterceptor:
    async def intercept_chat_request(request: Request) -> None
    async def capture_streaming_response(response: Response) -> AsyncIterator[str]
    async def extract_code_changes(response_data: str) -> CodeChanges
    async def parse_chat_message(data: str) -> ChatMessage
    async def convert_to_chatlove_format(data: Any) -> ChatLoveResponse
```

### 4. ⚡ Queue Manager

**Responsabilidades:**
- Gerenciamento de fila de mensagens
- Rate limiting inteligente
- Retry automático
- Load balancing entre sessões

**Funcionalidades:**
```python
class LovableQueueManager:
    async def enqueue_message(message: ChatMessage) -> str
    async def process_queue() -> None
    async def apply_rate_limiting() -> None
    async def retry_failed_messages() -> None
    async def balance_load_across_sessions() -> Session
```

## 📊 Fluxo de Dados

### 1. Recebimento de Mensagem
```
ChatLove Frontend → ChatLove Backend → Lovable Automation Service
```

### 2. Processamento
```
Queue Manager → Session Manager → Browser Automation → Lovable.dev
```

### 3. Resposta
```
Lovable.dev → API Interceptor → ChatLove Backend → ChatLove Frontend
```

## 🛠️ Stack Técnica

### **Core Dependencies:**
```python
# Browser Automation
playwright==1.40.0
selenium==4.15.0

# Async Processing
asyncio
aiohttp==3.9.0
aiofiles==23.2.0

# Queue Management
redis==5.0.0
celery==5.3.0

# Database
sqlalchemy==2.0.0
asyncpg==0.29.0

# Authentication
firebase-admin==6.2.0
cryptography==41.0.0

# Monitoring
prometheus-client==0.19.0
structlog==23.2.0
```

### **Infrastructure:**
- **Database:** PostgreSQL (sessões, logs, cache)
- **Cache/Queue:** Redis (fila de mensagens, cache de sessões)
- **Monitoring:** Prometheus + Grafana
- **Deployment:** Docker + Docker Compose

## 🔒 Segurança

### **Autenticação:**
- Credenciais Lovable em variáveis de ambiente
- Tokens Firebase criptografados no banco
- Rotação automática de sessões
- Isolamento de sessões por usuário

### **Rate Limiting:**
- Limite de mensagens por minuto
- Throttling inteligente baseado em uso
- Detecção de padrões suspeitos
- Fallback para múltiplas contas

### **Monitoramento:**
- Logs detalhados de todas as operações
- Alertas para falhas de autenticação
- Métricas de uso e performance
- Detecção de bloqueios

## 📁 Estrutura de Arquivos

```
lovable-automation-service/
├── 📁 src/
│   ├── 📁 core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações
│   │   ├── exceptions.py          # Exceções customizadas
│   │   └── logging.py             # Setup de logs
│   ├── 📁 session/
│   │   ├── __init__.py
│   │   ├── manager.py             # Session Manager
│   │   ├── auth.py                # Autenticação Firebase
│   │   └── pool.py                # Pool de sessões
│   ├── 📁 browser/
│   │   ├── __init__.py
│   │   ├── automation.py          # Browser Automation
│   │   ├── interceptor.py         # Network Interceptor
│   │   └── selectors.py           # CSS/XPath selectors
│   ├── 📁 queue/
│   │   ├── __init__.py
│   │   ├── manager.py             # Queue Manager
│   │   ├── processor.py           # Message Processor
│   │   └── retry.py               # Retry Logic
│   ├── 📁 api/
│   │   ├── __init__.py
│   │   ├── interceptor.py         # API Interceptor
│   │   ├── parser.py              # Response Parser
│   │   └── converter.py           # Format Converter
│   ├── 📁 models/
│   │   ├── __init__.py
│   │   ├── session.py             # Session Models
│   │   ├── message.py             # Message Models
│   │   └── response.py            # Response Models
│   └── 📁 utils/
│       ├── __init__.py
│       ├── crypto.py              # Criptografia
│       ├── validators.py          # Validadores
│       └── helpers.py             # Funções auxiliares
├── 📁 tests/
│   ├── test_session_manager.py
│   ├── test_browser_automation.py
│   ├── test_api_interceptor.py
│   └── test_queue_manager.py
├── 📁 docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── 📁 scripts/
│   ├── setup.py                   # Setup inicial
│   ├── migrate.py                 # Migrações
│   └── monitor.py                 # Monitoramento
├── 📁 config/
│   ├── development.env
│   ├── production.env
│   └── selectors.json             # CSS/XPath selectors
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── main.py                        # Entry point
```

## ⚙️ Configuração

### **Variáveis de Ambiente:**
```bash
# Lovable Accounts
LOVABLE_ACCOUNTS='[{"email":"user1@example.com","password":"pass1"},{"email":"user2@example.com","password":"pass2"}]'

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/chatlove
REDIS_URL=redis://localhost:6379/0

# Security
ENCRYPTION_KEY=your-32-byte-encryption-key
JWT_SECRET=your-jwt-secret

# Rate Limiting
MAX_MESSAGES_PER_MINUTE=10
MAX_CONCURRENT_SESSIONS=5

# Monitoring
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
```

### **Configuração do Banco:**
```sql
-- Tabela de sessões
CREATE TABLE lovable_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    firebase_token TEXT,
    session_cookies JSONB,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de mensagens
CREATE TABLE message_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    session_id UUID REFERENCES lovable_sessions(id),
    response_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- Índices
CREATE INDEX idx_sessions_active ON lovable_sessions(is_active, expires_at);
CREATE INDEX idx_queue_status ON message_queue(status, created_at);
```

## 🚀 Deployment

### **Docker Compose:**
```yaml
version: '3.8'
services:
  lovable-automation:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - LOVABLE_ACCOUNTS=${LOVABLE_ACCOUNTS}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    ports:
      - "8001:8000"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: chatlove
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 📈 Monitoramento

### **Métricas Principais:**
- Número de sessões ativas
- Taxa de sucesso de mensagens
- Tempo médio de resposta
- Uso de recursos (CPU, RAM)
- Erros de autenticação
- Rate limiting hits

### **Alertas:**
- Falha de autenticação em múltiplas contas
- Tempo de resposta > 30 segundos
- Fila de mensagens > 100 itens
- Uso de CPU > 80%
- Detecção de bloqueio pelo Lovable

## 🔄 Integração com ChatLove

### **API Endpoints:**
```python
# Endpoint no ChatLove Backend
@app.post("/api/lovable/chat")
async def lovable_chat(message: ChatMessage, user: User = Depends(get_current_user)):
    # Validar licença do usuário
    if not user.has_active_license():
        raise HTTPException(401, "Licença inválida")
    
    # Enviar para Lovable Automation Service
    response = await lovable_automation_client.send_message(
        user_id=user.id,
        message=message.content,
        project_context=message.context
    )
    
    return response

# WebSocket para streaming
@app.websocket("/ws/lovable/{user_id}")
async def lovable_websocket(websocket: WebSocket, user_id: str):
    await websocket.accept()
    
    async for chunk in lovable_automation_client.stream_response(user_id):
        await websocket.send_text(chunk)
```

## 🧪 Testes

### **Testes Unitários:**
```python
# test_session_manager.py
async def test_authenticate_success():
    manager = LovableSessionManager()
    session = await manager.authenticate("test@example.com", "password")
    assert session.is_active
    assert session.firebase_token is not None

# test_browser_automation.py
async def test_send_message():
    automation = LovableBrowserAutomation()
    browser = await automation.launch_browser()
    page = await automation.navigate_to_project("test-project")
    response = await automation.send_chat_message("Create a button")
    assert response.success
    assert "button" in response.generated_code.lower()
```

### **Testes de Integração:**
```python
# test_full_flow.py
async def test_complete_message_flow():
    # Simular mensagem do ChatLove
    message = ChatMessage(
        user_id="test-user",
        content="Create a login form",
        project_context={}
    )
    
    # Processar através do sistema completo
    response = await lovable_automation_service.process_message(message)
    
    # Verificar resposta
    assert response.success
    assert response.generated_code
    assert "form" in response.generated_code.lower()
    assert "login" in response.generated_code.lower()
```

## 📋 Roadmap de Implementação

### **Fase 1: Core Infrastructure (Semana 1-2)**
- [ ] Setup do projeto e estrutura de arquivos
- [ ] Implementação do Session Manager básico
- [ ] Autenticação Firebase
- [ ] Configuração do banco de dados
- [ ] Testes unitários básicos

### **Fase 2: Browser Automation (Semana 3-4)**
- [ ] Implementação do Browser Automation
- [ ] Sistema de interceptação de network
- [ ] Parsing de responses do Lovable
- [ ] Testes de automação

### **Fase 3: Queue System (Semana 5-6)**
- [ ] Implementação do Queue Manager
- [ ] Rate limiting e retry logic
- [ ] Load balancing entre sessões
- [ ] Monitoramento básico

### **Fase 4: Integration (Semana 7-8)**
- [ ] Integração com ChatLove Backend
- [ ] API endpoints e WebSocket
- [ ] Testes de integração completos
- [ ] Documentação de API

### **Fase 5: Production Ready (Semana 9-10)**
- [ ] Docker e deployment
- [ ] Monitoramento avançado
- [ ] Alertas e logging
- [ ] Testes de carga
- [ ] Documentação completa

### **Fase 6: Optimizations (Semana 11-12)**
- [ ] Cache inteligente
- [ ] Otimizações de performance
- [ ] Múltiplas contas Lovable
- [ ] Fallback strategies
- [ ] Métricas avançadas

## 🎯 Benefícios Esperados

### **Para o ChatLove:**
- ✅ **Economia:** 1 conta Lovable para N usuários
- ✅ **Escalabilidade:** Suporte a milhares de usuários simultâneos
- ✅ **Confiabilidade:** Sistema robusto com retry e fallback
- ✅ **Controle:** Logs completos e monitoramento detalhado

### **Para os Usuários:**
- ✅ **Acesso Ilimitado:** Sem preocupação com créditos Lovable
- ✅ **Performance:** Respostas rápidas via pool de sessões
- ✅ **Disponibilidade:** Sistema 24/7 com alta disponibilidade
- ✅ **Experiência:** Interface familiar do ChatLove

## ⚠️ Considerações Importantes

### **Legais e Éticas:**
- Uso apenas para fins educacionais e de desenvolvimento
- Respeitar termos de serviço do Lovable
- Não abusar da API ou causar sobrecarga
- Implementar rate limiting responsável

### **Técnicas:**
- Monitorar mudanças na API do Lovable
- Manter seletores CSS/XPath atualizados
- Implementar fallbacks para falhas
- Considerar detecção de bot pelo Lovable

### **Operacionais:**
- Backup regular de sessões e dados
- Rotação de credenciais
- Monitoramento proativo
- Plano de contingência para bloqueios

---

## 🚀 Próximos Passos

1. **Revisar e aprovar** esta documentação
2. **Criar nova tarefa** para implementação da Fase 1
3. **Setup do ambiente** de desenvolvimento
4. **Implementar** Session Manager básico
5. **Testar** autenticação Firebase

**Esta documentação serve como blueprint completo para implementação do sistema de automação Lovable integrado ao ChatLove.**
