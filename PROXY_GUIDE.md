# 🚀 Lovable Proxy - Guia Completo

Sistema que usa token de uma conta master para enviar mensagens ao Lovable, economizando créditos da sua conta principal.

---

## 📋 Como Funciona

```
┌─────────────────────────────────────────────────────────────┐
│  Seu Navegador (Extensão)                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 1. Você digita mensagem na sidebar                     ││
│  │         ↓                                               ││
│  │ 2. Extensão envia para PROXY LOCAL (localhost:8000)     ││
│  │         ↓                                               ││
│  │ 3. Proxy usa TOKEN MASTER (conta com créditos)          ││
│  │         ↓                                               ││
│  │ 4. Lovable processa usando créditos da CONTA MASTER     ││
│  │         ↓                                               ││
│  │ 5. Resposta volta para você                             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Status Atual

- [x] Backend proxy implementado
- [x] Token master configurado
- [x] Servidor rodando em `http://127.0.0.1:8000`
- [ ] Extensão atualizada para usar proxy
- [ ] Teste completo

---

## 🔧 Configuração

### 1. Token Master Configurado

O arquivo `.env` já contém:
```
LOVABLE_SESSION_ID=eyJhbGciOiJSUzI1NiIs...
LOVABLE_REFRESH_TOKEN=AMf-vBzMeuJisiGlW_Zbb...
```

### 2. Servidor Rodando

```bash
cd c:\projetos\lovable-assistant\backend
python main.py
```

**Saída esperada:**
```
============================================================
LOVABLE PROXY API
============================================================
Server: http://127.0.0.1:8000
Docs:   http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/api/health
Proxy:  http://127.0.0.1:8000/api/proxy
============================================================
Token configurado: [OK] Sim
============================================================
```

---

## 📡 Endpoints Disponíveis

### 1. Health Check
```
GET http://127.0.0.1:8000/api/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "proxy_configured": true
}
```

### 2. Enviar Mensagem (Proxy)
```
POST http://127.0.0.1:8000/api/proxy
```

**Body:**
```json
{
  "project_id": "3ee86a10-15a7-4721-be91-5af53dfe22d0",
  "message": "Crie um botão azul",
  "files": []
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Mensagem enviada com sucesso usando token master!",
  "data": { ... }
}
```

---

## 🧪 Testar Manualmente

### Usando cURL:

```bash
curl -X POST http://127.0.0.1:8000/api/proxy \
  -H "Content-Type: application/json" \
  -d "{\"project_id\":\"SEU_PROJECT_ID\",\"message\":\"Olá\"}"
```

### Usando Postman:

1. Método: `POST`
2. URL: `http://127.0.0.1:8000/api/proxy`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "project_id": "3ee86a10-15a7-4721-be91-5af53dfe22d0",
  "message": "Teste de mensagem"
}
```

---

## 🔄 Próximos Passos

### 1. Atualizar Extensão

A extensão precisa ser modificada para:
- Enviar para `http://127.0.0.1:8000/api/proxy`
- Não precisar mais do cookie do usuário
- Apenas enviar `project_id` e `message`

### 2. Testar Integração

1. Abrir Lovable.dev em um projeto
2. Usar a sidebar da extensão
3. Enviar mensagem
4. Verificar se usa créditos da conta master

---

## ⚠️ Importante

### Token Expira

O JWT do Lovable expira em algumas horas. Quando isso acontecer:

1. Abra o navegador com a conta master logada
2. Vá para `lovable.dev`
3. Pressione F12 → Application → Cookies
4. Copie o novo valor de `lovable-session-id.id`
5. Atualize no arquivo `.env`
6. Reinicie o servidor

### Refresh Automático (TODO)

Implementar refresh automático usando o `LOVABLE_REFRESH_TOKEN` para renovar o JWT sem precisar copiar manualmente.

---

## 📊 Logs

O servidor mostra logs de cada requisição:

```
[Lovable Proxy] Status: 200
[Lovable Proxy] Response: {"success":true...
```

---

## 🐛 Troubleshooting

### Erro: "Token master não configurado"
- Verifique se o arquivo `.env` existe
- Verifique se `LOVABLE_SESSION_ID` está preenchido

### Erro: "HTTP 401"
- Token expirou
- Copie um novo token da conta master

### Erro: "HTTP 404"
- `project_id` inválido
- Verifique se o projeto existe

---

## 📝 Arquivos Criados

```
backend/
├── .env                 # Tokens (NÃO COMMITAR!)
├── main.py              # Servidor FastAPI
├── lovable_proxy.py     # Lógica do proxy
└── requirements.txt     # Dependências
```

---

**Servidor está rodando! Próximo passo: atualizar a extensão para usar o proxy.**
