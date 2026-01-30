# 🚀 Lovable Automation Service

Sistema Python para automatizar interações com Lovable.dev, permitindo que o ChatLove use a API do Lovable sem consumir créditos dos usuários finais.

## 📋 Visão Geral

O Lovable Automation Service é um microsserviço que:

- ✅ **Gerencia sessões** autenticadas do Lovable.dev
- ✅ **Processa mensagens** de chat através de automação de navegador
- ✅ **Intercepta respostas** da API do Lovable
- ✅ **Balanceia carga** entre múltiplas contas Lovable
- ✅ **Monitora saúde** das sessões ativas
- ✅ **Integra com ChatLove** Backend

## 🏗️ Arquitetura

```
ChatLove Backend → Lovable Automation Service → Lovable.dev
                        ↓
                   Session Pool
                   Browser Automation
                   API Interceptor
                   Queue Manager
```

## 🛠️ Instalação

### Pré-requisitos

- Python 3.9+
- PostgreSQL
- Redis
- Playwright (para automação de navegador)

### 1. Clone e Configure

```bash
# Clone o repositório
git clone <repository-url>
cd lovable-automation-service

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt

# Instale navegadores do Playwright
playwright install
```

### 2. Configuração

```bash
# Copie arquivo de configuração
cp config/development.env .env

# Edite as configurações
nano .env
```

### 3. Configure Contas Lovable

Edite o arquivo `.env` e configure as contas Lovable:

```bash
LOVABLE_ACCOUNTS='[
  {"email":"conta1@example.com","password":"senha1"},
  {"email":"conta2@example.com","password":"senha2"}
]'
```

### 4. Execute o Serviço

```bash
# Desenvolvimento
python main.py

# Ou com uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```

### Status do Serviço
```http
GET /status
```

### Processar Mensagem
```http
POST /process-message
Content-Type: application/json

{
  "id": "msg_123",
  "user_id": "user_456",
  "project_id": "proj_789",
  "content": "Create a login form",
  "project_context": {},
  "priority": "normal"
}
```

### Gerenciamento de Sessões
```http
GET /sessions                    # Listar sessões
POST /sessions/health-check      # Verificar saúde
POST /sessions/cleanup           # Limpar expiradas
POST /sessions/rebalance         # Rebalancear carga
```

## 🔧 Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `DATABASE_URL` | URL do PostgreSQL | `postgresql://user:pass@localhost:5432/chatlove` |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379/0` |
| `LOVABLE_ACCOUNTS` | Contas Lovable (JSON) | `[]` |
| `MAX_CONCURRENT_SESSIONS` | Máximo de sessões | `5` |
| `MAX_MESSAGES_PER_MINUTE` | Rate limit | `10` |
| `BROWSER_HEADLESS` | Navegador headless | `true` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `API_PORT` | Porta da API | `8001` |

### Exemplo de Configuração Completa

```bash
# Database
DATABASE_URL=postgresql://chatlove:password@localhost:5432/chatlove
REDIS_URL=redis://localhost:6379/0

# Lovable Accounts
LOVABLE_ACCOUNTS='[
  {"email":"lovable1@mycompany.com","password":"secure_password_1"},
  {"email":"lovable2@mycompany.com","password":"secure_password_2"}
]'

# Security
ENCRYPTION_KEY=your-32-byte-encryption-key-here
JWT_SECRET=your-jwt-secret-key-here

# Performance
MAX_MESSAGES_PER_MINUTE=20
MAX_CONCURRENT_SESSIONS=5
BROWSER_TIMEOUT=60

# Monitoring
LOG_LEVEL=INFO
PROMETHEUS_PORT=9090
```

## 🐳 Docker

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  lovable-automation:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/chatlove
      - REDIS_URL=redis://redis:6379/0
      - LOVABLE_ACCOUNTS=${LOVABLE_ACCOUNTS}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: chatlove
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
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

## 🧪 Testes

```bash
# Executar testes
pytest

# Com coverage
pytest --cov=src

# Testes específicos
pytest tests/test_session_manager.py
```

## 📊 Monitoramento

### Métricas Disponíveis

- **Sessões ativas**: Número de sessões funcionais
- **Taxa de sucesso**: Percentual de mensagens processadas com sucesso
- **Tempo de resposta**: Tempo médio de processamento
- **Uso de recursos**: CPU, RAM, etc.
- **Erros**: Contagem e tipos de erros

### Logs Estruturados

```json
{
  "timestamp": "2024-01-22T00:30:00Z",
  "level": "INFO",
  "logger": "session",
  "event": "session_authenticated",
  "session_id": "sess_123",
  "email": "user@example.com",
  "expires_at": "2024-01-23T00:30:00Z"
}
```

## 🔒 Segurança

### Boas Práticas Implementadas

- ✅ **Tokens criptografados** no banco de dados
- ✅ **Rate limiting** para prevenir abuso
- ✅ **Rotação automática** de sessões
- ✅ **Logs detalhados** para auditoria
- ✅ **Isolamento de sessões** por usuário
- ✅ **Validação de entrada** em todos os endpoints

### Configuração de Segurança

```bash
# Gere chaves seguras
ENCRYPTION_KEY=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)

# Configure rate limiting
MAX_MESSAGES_PER_MINUTE=10
MAX_CONCURRENT_SESSIONS=5
```

## 🚀 Deploy em Produção

### 1. Configuração do Servidor

```bash
# Instale dependências do sistema
sudo apt update
sudo apt install -y python3.9 python3-pip postgresql redis-server

# Configure PostgreSQL
sudo -u postgres createdb chatlove
sudo -u postgres createuser chatlove_user

# Configure Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2. Deploy da Aplicação

```bash
# Clone e configure
git clone <repository-url> /opt/lovable-automation
cd /opt/lovable-automation

# Instale dependências
pip3 install -r requirements.txt
playwright install --with-deps

# Configure ambiente
cp config/production.env .env
# Edite .env com configurações de produção

# Configure systemd service
sudo cp scripts/lovable-automation.service /etc/systemd/system/
sudo systemctl enable lovable-automation
sudo systemctl start lovable-automation
```

### 3. Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name automation.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Integração com ChatLove

### No ChatLove Backend

```python
import httpx

class LovableAutomationClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def process_message(self, message: dict) -> dict:
        response = await self.client.post(
            f"{self.base_url}/process-message",
            json=message
        )
        return response.json()

# Uso
automation_client = LovableAutomationClient()

@app.post("/api/lovable/chat")
async def lovable_chat(message: ChatMessage):
    result = await automation_client.process_message({
        "id": str(uuid.uuid4()),
        "user_id": message.user_id,
        "project_id": message.project_id,
        "content": message.content
    })
    
    return result
```

## 📈 Performance

### Benchmarks Esperados

- **Throughput**: 50-100 mensagens/minuto
- **Latência**: < 5 segundos por mensagem
- **Disponibilidade**: 99.9%
- **Sessões simultâneas**: 5-10 por instância

### Otimizações

- **Pool de sessões** para reutilização
- **Cache Redis** para dados frequentes
- **Load balancing** entre sessões
- **Retry automático** para falhas temporárias

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Falha de Autenticação
```bash
# Verifique as credenciais
curl -X GET http://localhost:8001/sessions

# Logs detalhados
tail -f logs/lovable-automation.log | grep auth
```

#### 2. Sessões Expiradas
```bash
# Force cleanup
curl -X POST http://localhost:8001/sessions/cleanup

# Rebalanceie carga
curl -X POST http://localhost:8001/sessions/rebalance
```

#### 3. Rate Limiting
```bash
# Verifique configuração
echo $MAX_MESSAGES_PER_MINUTE

# Ajuste se necessário
export MAX_MESSAGES_PER_MINUTE=20
```

### Logs Úteis

```bash
# Logs gerais
tail -f logs/lovable-automation.log

# Logs de sessão
grep "session" logs/lovable-automation.log

# Logs de erro
grep "ERROR" logs/lovable-automation.log
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentação**: [Wiki](https://github.com/your-repo/wiki)
- **Email**: support@yourcompany.com

---

**Desenvolvido com ❤️ para o ChatLove**
