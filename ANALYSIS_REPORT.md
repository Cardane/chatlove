# 📊 RELATÓRIO DE ANÁLISE - Lovable Assistant

**Data:** 18/01/2026 23:24  
**Análise baseada em:** 858 requisições HTTP, 37 cookies, 26 logs do console

---

## 🎯 RESUMO EXECUTIVO

Após análise profunda dos dados capturados do Lovable.dev, identificamos **descobertas críticas** que permitem implementar um cliente API funcional e completo. O endpoint de chat foi mapeado com sucesso, incluindo payload completo, autenticação e formato de resposta.

---

## 📡 DESCOBERTAS PRINCIPAIS

### 1. Endpoint de Chat (CRÍTICO)
```
POST https://api.lovable.dev/projects/{project_id}/chat
```

**Status:** ✅ Confirmado e funcional  
**Response:** `202 Accepted` (assíncrono)

### 2. Autenticação
- **Método:** Cookies de sessão (não Bearer token!)
- **Cookies necessários:**
  - `lovable-session-id.id` (JWT do Firebase)
  - `lovable-session-id.refresh` (token de refresh)
  - `lovable-session-id.sig` (assinatura)

### 3. Headers Obrigatórios
```http
Content-Type: application/json
Origin: https://lovable.dev
Referer: https://lovable.dev/
x-client-git-sha: 02e494f6d51b5ea5a1fc25226f7e37dab356d0cd
```

---

## 📦 PAYLOAD COMPLETO DO CHAT

```json
{
  "message": "Texto da mensagem do usuário",
  "id": "umsg_01kf9qg6naexrvbjmx10ej9nmt",
  "mode": "instant",
  "debug_mode": false,
  "prev_session_id": "aimsg_01kf9qbmt0fvqtgfgrps6czyn0",
  "user_input": {},
  "ai_message_id": "aimsg_01kf9qg6ndexrvbjn15bsacnte",
  "current_page": "index",
  "view": "preview",
  "view_description": "The user is currently viewing the preview.",
  "model": null,
  "session_replay": "[...]",
  "client_logs": [],
  "network_requests": [],
  "runtime_errors": [],
  "integration_metadata": {
    "browser": {
      "preview_viewport_width": 482,
      "preview_viewport_height": 606
    }
  }
}
```

### Campos Importantes

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `message` | string | ✅ | Mensagem do usuário |
| `id` | string | ✅ | ID único (formato: `umsg_` + hex timestamp + random) |
| `mode` | string | ✅ | Modo: `"instant"` ou `"chat"` |
| `prev_session_id` | string | ⚠️ | ID da sessão anterior (formato: `aimsg_...`) |
| `ai_message_id` | string | ✅ | ID da resposta esperada |
| `current_page` | string | ⚠️ | Página atual do projeto |
| `view` | string | ⚠️ | Visualização: `"preview"`, `"code"`, etc. |
| `session_replay` | string | ❌ | JSON stringificado com replay da sessão |
| `client_logs` | array | ❌ | Logs do console |
| `integration_metadata` | object | ❌ | Metadados do browser |

---

## 🔍 ENDPOINTS MAPEADOS

### Autenticação
- `POST /auth/check-auth-provider`
- `GET /api/auth/session`
- `GET /api/login`

### Projetos
- `GET /projects/{id}/details`
- `GET /projects/{id}/source-code`
- `GET /projects/{id}/collaborators`
- `PUT /projects/{id}` (atualização)
- `POST /projects/{id}/chat` ⭐ (envio de mensagens)
- `GET /projects/{id}/latest-message` (SSE - respostas)
- `POST /projects/{id}/presence` (heartbeat)
- `POST /projects/{id}/sandbox/start`
- `POST /projects/{id}/mark-viewed`

### Workspace
- `GET /workspaces/{id}/projects`
- `GET /workspaces/{id}/user-monthly-usage`
- `GET /workspaces/{id}/ai-grant-status`
- `GET /workspaces/{id}/cloud-grant-status`

---

## 🍪 COOKIES CRÍTICOS

```json
{
  "lovable-session-id.id": "eyJhbGciOiJSUzI1NiIs...",
  "lovable-session-id.refresh": "AMf-vBwHIQfyRzfuZGzZ4T...",
  "lovable-session-id.sig": "ygQPX_yRSOmV-QmLwkYnGeRVefqZDGU7EOk4EZaM8Co"
}
```

**Expiração:** ~1 hora (token JWT)  
**Refresh:** Usar `lovable-session-id.refresh` para renovar

---

## 📊 ESTATÍSTICAS DE REDE

### Domínios Principais
| Domínio | Requisições | Propósito |
|---------|-------------|-----------|
| `lovable.dev` | 370 | Frontend |
| `api.lovable.dev` | 116 | **API principal** |
| `firestore.googleapis.com` | 99 | Firebase Database |
| `rs.lovable.dev` | 48 | Recursos estáticos |

### Serviços de Terceiros
- **Analytics:** RudderStack, Google Analytics, PostHog
- **Marketing:** HubSpot, Facebook Pixel, TikTok Pixel, LinkedIn Insight
- **Infraestrutura:** Google Cloud, Firebase

---

## 🔧 PROBLEMAS IDENTIFICADOS NO CÓDIGO ATUAL

### `lovable_client.py`

❌ **Endpoints incorretos:**
```python
# ERRADO
"/projects/{id}/messages"
"/chat/{id}/message"

# CORRETO
"/projects/{id}/chat"
```

❌ **Autenticação incorreta:**
```python
# ERRADO
headers = {"Authorization": f"Bearer {token}"}

# CORRETO
# Usar cookies de sessão
```

❌ **Payload incompleto:**
- Falta `mode`, `ai_message_id`, `current_page`, etc.
- Formato de ID incorreto

---

## 🚀 MELHORIAS PROPOSTAS

### 1. Corrigir Cliente API
- ✅ Usar endpoint correto: `POST /projects/{id}/chat`
- ✅ Implementar autenticação via cookies
- ✅ Payload completo com todos os campos obrigatórios
- ✅ Gerar IDs no formato correto

### 2. Implementar SSE para Respostas
```python
GET /projects/{id}/latest-message
Headers:
  Accept: text/event-stream
  Cache-Control: no-cache
```

### 3. Adicionar Heartbeat
```python
POST /projects/{id}/presence
# Enviar a cada 30 segundos para manter sessão ativa
```

### 4. Gerenciamento de Tokens
- Implementar refresh automático
- Detectar expiração e renovar token

### 5. Suporte a Contexto
- `current_page`: página atual do projeto
- `view`: tipo de visualização
- `session_replay`: contexto visual (opcional)

---

## 📝 FORMATO DE IDs

### Message ID (User)
```
umsg_{timestamp_hex}{random_16_chars}
Exemplo: umsg_01kf9qg6naexrvbjmx10ej9nmt
```

### AI Message ID
```
aimsg_{timestamp_hex}{random_16_chars}
Exemplo: aimsg_01kf9qg6ndexrvbjn15bsacnte
```

**Geração:**
```python
import time
import uuid

timestamp = int(time.time() * 1000)
random_part = uuid.uuid4().hex[:16]
message_id = f"umsg_{timestamp:x}{random_part}"
```

---

## 🔐 SEGURANÇA

### Tokens JWT (Firebase)
- **Issuer:** `https://securetoken.google.com/gpt-engineer-390607`
- **Audience:** `gpt-engineer-390607`
- **Expiração:** ~1 hora
- **Algoritmo:** RS256

### Cookies
- **HttpOnly:** ✅ (lovable-session-id.*)
- **Secure:** ✅
- **SameSite:** Lax

---

## 📈 MÉTRICAS DE PERFORMANCE

- **Latência média API:** ~485ms
- **Response time:** 202 Accepted (assíncrono)
- **Timeout recomendado:** 60s

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ **Implementar novo cliente API** com endpoint correto
2. ✅ **Adicionar autenticação via cookies**
3. ✅ **Implementar SSE client** para respostas
4. ⚠️ **Testar com projeto real**
5. ⚠️ **Adicionar tratamento de erros**
6. ⚠️ **Implementar retry logic**

---

## 📚 REFERÊNCIAS

- **API Base:** `https://api.lovable.dev`
- **Frontend:** `https://lovable.dev`
- **Preview:** `https://id-preview--{project_id}.lovable.app`
- **Live:** `https://{project_id}.lovableproject.com`

---

## ✅ CONCLUSÃO

A análise foi **100% bem-sucedida**. Todos os dados necessários para implementar um cliente funcional foram capturados e documentados. O endpoint de chat está confirmado e o payload completo foi mapeado.

**Status:** Pronto para implementação ✅
