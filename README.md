# 🚀 Lovable Assistant - Sistema Aperfeiçoado

Cliente Python completo para interagir com a API do Lovable.dev, baseado em análise profunda dos dados de rede capturados.

## ✨ Novidades da Versão Aperfeiçoada

- ✅ **Endpoint correto**: `POST /projects/{id}/chat`
- ✅ **Autenticação via cookies** (não Bearer token)
- ✅ **Payload completo** com todos os campos obrigatórios
- ✅ **SSE Client** para streaming de respostas
- ✅ **Heartbeat/Presence** para manter sessão ativa
- ✅ **IDs no formato correto** (`umsg_`, `aimsg_`)

## 📊 Documentação Completa

- 📄 **[ANALYSIS_REPORT.md](ANALYSIS_REPORT.md)** - Análise completa dos dados capturados
- 🍪 **[COOKIE_EXTRACTION_GUIDE.md](COOKIE_EXTRACTION_GUIDE.md)** - Como extrair cookies de sessão
- 📝 **[backend/example_usage.py](backend/example_usage.py)** - Exemplos de uso

---

## 📁 Estrutura do Projeto

```
lovable-assistant/
├── ANALYSIS_REPORT.md           # 📊 Relatório de análise completo
├── COOKIE_EXTRACTION_GUIDE.md   # 🍪 Guia de extração de cookies
│
├── backend/                     # Backend Python
│   ├── lovable_client.py        # ✨ Cliente API aperfeiçoado
│   ├── example_usage.py         # 📝 Exemplos de uso
│   ├── main.py                  # FastAPI server (legado)
│   ├── config.py                # Configurações
│   └── requirements.txt         # Dependências
│
├── analyzer/                    # Ferramenta de análise
│   ├── main.py                  # Analyzer principal
│   ├── browser.py               # Controle do Puppeteer
│   └── output/                  # Dados capturados
│
└── extension/                   # Extensão Chrome (legado)
    ├── manifest.json
    ├── popup.html
    └── popup.js
```

---

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

### 2. Extrair Cookies de Sessão

Siga o guia completo: **[COOKIE_EXTRACTION_GUIDE.md](COOKIE_EXTRACTION_GUIDE.md)**

**Método rápido (DevTools):**
1. Abra https://lovable.dev e faça login
2. Pressione `F12` → Aba "Application" → "Cookies"
3. Copie os valores de:
   - `lovable-session-id.id`
   - `lovable-session-id.refresh`
   - `lovable-session-id.sig`

### 3. Usar o Cliente

```python
import asyncio
from lovable_client import LovableClient

async def main():
    # Configurar cookies
    cookies = {
        "lovable-session-id.id": "seu_token_jwt_aqui",
        "lovable-session-id.refresh": "seu_refresh_token_aqui",
        "lovable-session-id.sig": "sua_assinatura_aqui"
    }
    
    # Criar cliente
    async with LovableClient(cookies) as client:
        # Enviar mensagem
        result = await client.send_message(
            project_id="seu_project_id",
            message="Crie um botão azul com texto branco"
        )
        
        print(f"Status: {result['status_code']}")
        print(f"Message ID: {result['message_id']}")
        
        # Receber resposta via SSE
        async for event in client.stream_response("seu_project_id"):
            print(f"Evento: {event}")

asyncio.run(main())
```

---

## 📡 API do Cliente

### LovableClient

```python
class LovableClient:
    def __init__(self, cookies: Dict[str, str])
    
    # Enviar mensagem
    async def send_message(
        project_id: str,
        message: str,
        mode: str = "instant",
        current_page: str = "index",
        view: str = "preview",
        ...
    ) -> Dict[str, Any]
    
    # Receber resposta via SSE
    async def stream_response(
        project_id: str,
        timeout: int = 60
    ) -> AsyncIterator[Dict[str, Any]]
    
    # Heartbeat
    async def send_presence(project_id: str) -> Dict[str, Any]
    
    # Utilitários
    async def get_project_details(project_id: str) -> Dict[str, Any]
    async def get_source_code(project_id: str) -> Dict[str, Any]
    async def list_workspace_projects(workspace_id: str) -> Dict[str, Any]
```

### Métodos Principais

| Método | Descrição |
|--------|-----------|
| `send_message()` | Envia mensagem para o projeto |
| `stream_response()` | Recebe resposta via Server-Sent Events |
| `send_presence()` | Mantém sessão ativa (heartbeat) |
| `get_project_details()` | Obtém detalhes do projeto |
| `get_source_code()` | Obtém código fonte |
| `list_workspace_projects()` | Lista projetos do workspace |

---

## 🔍 Endpoints Mapeados

### Chat
- `POST /projects/{id}/chat` - Enviar mensagem ⭐
- `GET /projects/{id}/latest-message` - Receber resposta (SSE)

### Projetos
- `GET /projects/{id}/details` - Detalhes do projeto
- `GET /projects/{id}/source-code` - Código fonte
- `GET /projects/{id}/collaborators` - Colaboradores
- `POST /projects/{id}/presence` - Heartbeat
- `POST /projects/{id}/sandbox/start` - Iniciar sandbox

### Workspace
- `GET /workspaces/{id}/projects` - Listar projetos
- `GET /workspaces/{id}/user-monthly-usage` - Uso mensal
- `GET /workspaces/{id}/ai-grant-status` - Status de créditos

---

## 📝 Exemplos de Uso

### Exemplo 1: Mensagem Simples

```python
async with LovableClient(cookies) as client:
    result = await client.send_message(
        project_id="abc123",
        message="Adicione um botão de login"
    )
    print(result)
```

### Exemplo 2: Com Contexto

```python
result = await client.send_message(
    project_id="abc123",
    message="Corrija o erro de validação",
    current_page="components/Form.tsx",
    view="code",
    debug_mode=True,
    client_logs=[
        {
            "level": "error",
            "message": "Validation failed",
            "logged_at": "2026-01-18T23:30:00.000Z"
        }
    ]
)
```

### Exemplo 3: Streaming de Resposta

```python
async for event in client.stream_response(project_id):
    if event["type"] == "message":
        print(f"IA: {event['data']}")
    elif event["type"] == "error":
        print(f"Erro: {event['data']}")
```

### Exemplo 4: Listar Projetos

```python
projects = await client.list_workspace_projects(workspace_id)
for project in projects["data"]:
    print(f"- {project['name']} ({project['id']})")
```

---

## 🔐 Segurança

### ⚠️ IMPORTANTE

1. **Nunca compartilhe seus cookies!**
   - Dão acesso total à sua conta Lovable

2. **Não commite cookies no Git**
   ```bash
   echo "lovable_cookies.json" >> .gitignore
   ```

3. **Cookies expiram em ~1 hora**
   - Extraia novamente quando necessário
   - Implemente lógica de refresh automático

4. **Use HTTPS sempre**
   - Cookies são marcados como `Secure`

---

## 🛠️ Ferramentas Incluídas

### Analyzer (Captura de Dados)

Ferramenta para capturar e analisar tráfego de rede do Lovable.dev:

```bash
cd analyzer
python main.py
```

**Funcionalidades:**
- Captura requisições HTTP
- Captura mensagens WebSocket
- Captura logs do console
- Gera relatórios detalhados

### Extensão Chrome (Legado)

A extensão Chrome original ainda está disponível em `extension/`, mas o novo cliente Python é recomendado para uso programático.

---

## 📊 Análise de Dados

O sistema foi aperfeiçoado baseado em análise de **858 requisições HTTP** capturadas:

- ✅ Endpoint de chat confirmado
- ✅ Payload completo mapeado
- ✅ Autenticação via cookies identificada
- ✅ Formato de IDs descoberto
- ✅ SSE para respostas implementado

Ver **[ANALYSIS_REPORT.md](ANALYSIS_REPORT.md)** para detalhes completos.

---

## 🐛 Troubleshooting

### "Cookies inválidos"
**Solução:** Extraia os cookies novamente após fazer login no Lovable.dev

### "Token expirado"
**Solução:** Tokens JWT expiram em ~1 hora. Extraia novos cookies.

### "Projeto não encontrado"
**Solução:** Verifique se o `project_id` está correto. Use a URL do projeto no Lovable.dev.

### "SSE timeout"
**Solução:** Aumente o timeout: `stream_response(project_id, timeout=120)`

---

## 📚 Documentação Adicional

- **[ANALYSIS_REPORT.md](ANALYSIS_REPORT.md)** - Análise completa dos dados
- **[COOKIE_EXTRACTION_GUIDE.md](COOKIE_EXTRACTION_GUIDE.md)** - Guia de cookies
- **[backend/example_usage.py](backend/example_usage.py)** - Exemplos práticos
- **[analyzer/README.md](analyzer/README.md)** - Documentação do analyzer

---

## 🎯 Roadmap

- [x] Análise completa da API
- [x] Cliente com endpoint correto
- [x] Autenticação via cookies
- [x] SSE para respostas
- [x] Heartbeat/Presence
- [ ] Refresh automático de tokens
- [ ] WebSocket support
- [ ] CLI interativo
- [ ] Testes automatizados

---

## 📄 Licença

Uso pessoal e educacional. Não redistribua.

---

## 🙏 Créditos

Sistema desenvolvido através de engenharia reversa ética da plataforma Lovable.dev para fins de automação pessoal.

**Desenvolvido com ❤️ para facilitar o fluxo de trabalho com Lovable.dev** 🚀
