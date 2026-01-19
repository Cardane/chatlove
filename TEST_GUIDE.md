# 🧪 Guia de Teste - ChatLove

## ✅ Correções Implementadas

### 1. Backend - Endpoint Proxy Corrigido
**Arquivo:** `chatlove-backend/main.py`

**Mudanças:**
- ✅ Endpoint correto: `https://api.lovable.dev/projects/{project_id}/chat`
- ✅ Headers completos: Origin, Referer, x-client-git-sha
- ✅ Payload no formato Lovable: message_id, ai_message_id, mode, etc.
- ✅ Geração de IDs únicos no formato correto
- ✅ Timeout aumentado para 60s
- ✅ Suporte para resposta 202 Accepted (assíncrono)

### 2. Estrutura do Payload
```json
{
  "message": "texto do usuário",
  "id": "umsg_18d1a2b3c4d5e6f7",
  "mode": "instant",
  "debug_mode": false,
  "prev_session_id": null,
  "user_input": {},
  "ai_message_id": "aimsg_18d1a2b3c4d5e6f8",
  "current_page": "index",
  "view": "preview",
  "view_description": "The user is currently viewing the preview.",
  "model": null,
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
```

---

## 🚀 Como Testar

### Passo 1: Iniciar o Backend
```bash
cd chatlove-backend
python main.py
```

**Verificar:**
- ✅ Servidor rodando em `http://127.0.0.1:8000`
- ✅ Docs disponíveis em `http://127.0.0.1:8000/docs`

### Passo 2: Carregar a Extensão
1. Abra Chrome/Edge
2. Vá para `chrome://extensions/`
3. Ative "Modo do desenvolvedor"
4. Clique em "Carregar sem compactação"
5. Selecione a pasta `chatlove-extension`

**Verificar:**
- ✅ Extensão aparece na lista
- ✅ Ícone aparece na barra de ferramentas

### Passo 3: Ativar Licença
1. Clique no ícone da extensão
2. Digite seu nome de usuário
3. Cole a chave de licença
4. Clique em "Ativar"

**Verificar:**
- ✅ Mensagem de sucesso
- ✅ Status muda para "Ativada"

### Passo 4: Acessar Lovable.dev
1. Faça login no https://lovable.dev
2. Abra um projeto existente
3. Aguarde a sidebar do ChatLove aparecer

**Verificar:**
- ✅ Sidebar aparece à direita
- ✅ Projeto detectado corretamente
- ✅ Status "Pronto"

### Passo 5: Enviar Mensagem
1. Digite uma mensagem na sidebar
2. Clique em "Enviar"
3. Aguarde resposta

**Verificar:**
- ✅ Mensagem aparece no chat
- ✅ Status muda para "Enviando..."
- ✅ Resposta de sucesso ou erro

---

## 🔍 Debugging

### Verificar Cookies
Abra DevTools (F12) e execute:
```javascript
document.cookie.split(';').find(c => c.includes('lovable-session-id.id'))
```

**Esperado:** Cookie presente com valor JWT

### Verificar Requisição
No DevTools, aba Network:
1. Filtre por "chat"
2. Envie uma mensagem
3. Verifique a requisição

**Esperado:**
- URL: `https://api.lovable.dev/projects/{id}/chat`
- Method: POST
- Status: 202 Accepted
- Headers: Authorization, Origin, Referer, x-client-git-sha

### Logs do Backend
No terminal onde o backend está rodando:
```
INFO:     127.0.0.1:xxxxx - "POST /api/proxy HTTP/1.1" 200 OK
```

### Logs da Extensão
No console da página (F12):
```
♥ ChatLove loaded!
[ChatLove] License not activated. Please activate in extension popup.
```

---

## ❌ Possíveis Erros

### Erro: "Session cookie not found"
**Causa:** Não está logado no Lovable.dev  
**Solução:** Faça login no Lovable.dev primeiro

### Erro: "Projeto não detectado"
**Causa:** URL não contém ID do projeto  
**Solução:** Abra um projeto específico (URL: `/projects/{id}`)

### Erro: "License not activated"
**Causa:** Licença não foi ativada  
**Solução:** Clique no ícone da extensão e ative a licença

### Erro: "Lovable API error: 401"
**Causa:** Cookie de sessão inválido ou expirado  
**Solução:** Faça logout e login novamente no Lovable.dev

### Erro: "Lovable API error: 404"
**Causa:** Projeto não existe ou ID incorreto  
**Solução:** Verifique se o projeto existe e está acessível

### Erro: "Timeout ao conectar com Lovable"
**Causa:** API do Lovable não respondeu em 60s  
**Solução:** Tente novamente, pode ser problema temporário

---

## 📊 Teste de Integração Completo

### Script de Teste (Python)
```python
import requests
import time
import uuid

API_URL = "http://127.0.0.1:8000"

# 1. Ativar licença
response = requests.post(f"{API_URL}/api/license/activate", json={
    "username": "teste",
    "license_key": "CHATLOVE-XXXX-XXXX-XXXX-XXXX",
    "fingerprint": {
        "userAgent": "Test",
        "language": "pt-BR",
        "timezone": "America/Sao_Paulo",
        "platform": "Win32",
        "hardwareConcurrency": 8
    }
})

print("Ativação:", response.json())
token = response.json()["token"]

# 2. Validar licença
response = requests.post(f"{API_URL}/api/license/validate", json={
    "token": token,
    "fingerprint": {
        "userAgent": "Test",
        "language": "pt-BR",
        "timezone": "America/Sao_Paulo",
        "platform": "Win32",
        "hardwareConcurrency": 8
    }
})

print("Validação:", response.json())

# 3. Enviar mensagem (requer cookie real do Lovable)
# Este teste só funciona com um cookie válido
response = requests.post(f"{API_URL}/api/proxy", json={
    "token": token,
    "project_id": "b8d9f10c-304b-4383-8175-788ebed41708",
    "message": "Olá, teste!",
    "lovable_session": "SEU_COOKIE_AQUI"
})

print("Proxy:", response.json())
```

---

## 🎯 Checklist de Teste

### Backend
- [ ] Servidor inicia sem erros
- [ ] Endpoint `/api/health` retorna 200
- [ ] Endpoint `/api/proxy` aceita requisições
- [ ] Logs mostram requisições

### Extensão
- [ ] Carrega sem erros
- [ ] Popup abre corretamente
- [ ] Ativação de licença funciona
- [ ] Validação de licença funciona

### Integração
- [ ] Sidebar aparece no Lovable.dev
- [ ] Projeto é detectado
- [ ] Cookie é capturado
- [ ] Mensagem é enviada
- [ ] Resposta é recebida
- [ ] Tokens são contabilizados

---

## 📝 Notas Importantes

1. **Cookie de Sessão:** O cookie `lovable-session-id.id` expira após ~1 hora. Se receber erro 401, faça logout/login no Lovable.dev

2. **Resposta Assíncrona:** O Lovable retorna 202 Accepted, a resposta real vem via SSE (Server-Sent Events) no endpoint `/latest-message`

3. **Rate Limiting:** O Lovable pode ter rate limiting. Se receber erro 429, aguarde alguns segundos

4. **CORS:** A extensão precisa ter permissão para acessar `lovable.dev` e `api.lovable.dev`

5. **Projeto Ativo:** Só funciona em projetos que você tem acesso (colaborador ou owner)

---

## 🔄 Próximas Melhorias

1. **SSE Client:** Implementar listener para receber respostas em tempo real
2. **Session Management:** Renovar cookie automaticamente
3. **Error Handling:** Melhorar mensagens de erro
4. **Retry Logic:** Tentar novamente em caso de falha temporária
5. **Context Tracking:** Manter histórico de mensagens para `prev_session_id`

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do backend
2. Verifique o console do navegador (F12)
3. Verifique a aba Network do DevTools
4. Capture um novo arquivo HAR se necessário
