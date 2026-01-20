# 🎉 ChatLove Proxy - Cookie Automático Implementado!

## ✅ Status: FUNCIONANDO COM COOKIE DINÂMICO

Data: 19/01/2026 20:58

---

## 🎯 O Que Mudou:

### ❌ Antes (Token Fixo):
- Token configurado manualmente no `.env`
- Token expirava a cada ~1 hora
- Precisava atualizar manualmente
- **Só funcionava em projetos da conta do token**

### ✅ Agora (Cookie Automático):
- **Extension captura cookie automaticamente**
- Token sempre atualizado (em tempo real)
- Sem configuração manual
- **Funciona em QUALQUER projeto do usuário logado**

---

## 🔑 Como Funciona:

### Fluxo Completo:

```
1. Usuário faz login no Lovable (qualquer conta)
   ↓
2. Usuário abre qualquer projeto
   ↓
3. Usuário digita mensagem no ChatLove Proxy
   ↓
4. Extension captura cookie automaticamente
   chrome.cookies.get({
     url: "https://lovable.dev",
     name: "lovable-session-id.id"
   })
   ↓
5. Extension envia para servidor:
   {
     project_id: "xxx",
     message: "xxx",
     session_token: "cookie_capturado"  ← AUTOMÁTICO!
   }
   ↓
6. Servidor usa session_token recebido
   headers: {
     "Authorization": f"Bearer {session_token}"
   }
   ↓
7. Envia para API do Lovable
   ↓
8. Lovable processa (202 Accepted)
   ↓
9. Preview atualiza
   ↓
10. Créditos do usuário LOGADO consumidos
```

---

## 📋 Mudanças Implementadas:

### 1. **Extension (manifest.json)**

```json
{
  "permissions": [
    "cookies",   // ← ADICIONADO
    "storage",
    "tabs"
  ]
}
```

### 2. **Extension (content.js)**

#### Função de Captura de Cookie:

```javascript
async function getCookieToken() {
  try {
    const cookie = await chrome.cookies.get({
      url: "https://lovable.dev",
      name: "lovable-session-id.id"
    });
    
    if (cookie && cookie.value) {
      console.log('[ChatLove Proxy] Cookie capturado com sucesso');
      return cookie.value;
    }
    
    return null;
  } catch (error) {
    console.error('[ChatLove Proxy] Erro ao capturar cookie:', error);
    return null;
  }
}
```

#### Modificação no Envio:

```javascript
async function sendMessage() {
  // ... código existente ...
  
  // Capturar cookie automaticamente
  setStatus('Capturando cookie...');
  const sessionToken = await getCookieToken();
  
  if (!sessionToken) {
    addMessage('❌ Erro: Não foi possível capturar o cookie. Faça login no Lovable.', 'error');
    return;
  }
  
  // Enviar para servidor com session_token
  const response = await fetch(PROXY_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      license_key: licenseKey,
      project_id: projectId,
      message: message,
      session_token: sessionToken  // ← Cookie capturado!
    })
  });
}
```

### 3. **Servidor (main.py)**

#### Modelo Atualizado:

```python
class MasterProxyRequest(BaseModel):
    project_id: str
    message: str
    session_token: str  # ← NOVO (obrigatório)
    license_key: Optional[str] = None
```

#### Uso do Token Dinâmico:

```python
@app.post("/api/master-proxy")
async def master_proxy(request: MasterProxyRequest):
    # Usar token recebido da extension (dinâmico)
    session_token = request.session_token
    
    # Preparar requisição
    headers = {
        "Authorization": f"Bearer {session_token}",  # ← Token dinâmico!
        "Content-Type": "application/json"
    }
    
    # Enviar para Lovable
    response = await client.post(lovable_url, headers=headers, json=payload)
```

---

## ✅ Vantagens:

1. ✅ **Funciona em qualquer projeto** (do usuário logado)
2. ✅ **Token sempre atualizado** (capturado em tempo real)
3. ✅ **Sem configuração manual** (não precisa copiar token)
4. ✅ **Multi-usuário** (cada usuário usa seu próprio cookie)
5. ✅ **Sem expiração** (sempre pega o cookie atual)
6. ✅ **Simples de usar** (apenas fazer login no Lovable)

---

## ⚠️ Importante:

### Créditos Consumidos:

Os **créditos do usuário LOGADO** no navegador serão consumidos.

**Por quê?**
- O cookie capturado é do usuário logado
- A API do Lovable identifica o usuário pelo cookie
- Créditos são debitados da conta do cookie

### Para Economizar Créditos:

O usuário precisa estar **logado com a conta master** no navegador:

1. Fazer **logout** da conta pessoal
2. Fazer **login** com a conta master
3. Abrir projeto (qualquer projeto da master)
4. Usar ChatLove Proxy
5. **Créditos da master consumidos!**

---

## 📊 Comparação:

| Aspecto | Token Fixo (.env) | Cookie Automático |
|---------|-------------------|-------------------|
| **Configuração** | Manual (copiar token) | Automática |
| **Expiração** | Precisa atualizar | Sempre atualizado |
| **Projetos** | Só da conta do token | Qualquer do usuário logado |
| **Multi-usuário** | Não | Sim |
| **Créditos** | Conta do token fixo | Conta do usuário logado |
| **Facilidade** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🚀 Como Usar:

### Passo 1: Recarregar Extension

1. Vá em `chrome://extensions/`
2. Encontre **ChatLove Proxy**
3. Clique no ícone de **reload** (🔄)

### Passo 2: Fazer Login no Lovable

1. Acesse https://lovable.dev
2. Faça **login** com a conta que você quer usar
   - **Conta master:** Economiza créditos da master
   - **Sua conta:** Usa seus créditos

### Passo 3: Abrir Projeto

1. Abra **qualquer projeto** da conta logada
2. A sidebar do ChatLove aparece automaticamente

### Passo 4: Usar Normalmente

1. Digite sua mensagem
2. Clique **"Enviar"**
3. Extension captura cookie automaticamente
4. Mensagem enviada!
5. Preview atualiza

---

## 🐛 Troubleshooting:

### Erro: "Não foi possível capturar o cookie"

**Causa:** Você não está logado no Lovable.

**Solução:**
1. Faça login em https://lovable.dev
2. Recarregue a página do projeto
3. Tente novamente

### Erro: "403 Forbidden"

**Causa:** Você está em um projeto que não pertence à conta logada.

**Solução:**
1. Verifique se você está logado com a conta correta
2. Abra um projeto da conta logada
3. Tente novamente

### Cookie não é capturado

**Causa:** Extension não tem permissão de cookies.

**Solução:**
1. Vá em `chrome://extensions/`
2. Clique em **Detalhes** na extension
3. Verifique se tem permissão para **cookies**
4. Recarregue a extension

---

## 📝 Logs do Servidor:

### Sucesso:

```
[MASTER PROXY] Requisição recebida:
  Project ID: 7f85d5e9-6a22-4e39-bd58-13945836d77a
  Message: Teste...
  License Key: CCA3-39CD-7734-6CD6
  Session Token: eyJhbGciOiJSUzI1NiIsImtpZCI6IjFjMzIxOTgzNGRhNT...

[MASTER PROXY] Enviando para Lovable:
  URL: https://api.lovable.dev/projects/.../chat
  Payload: {'message': 'Teste', 'timestamp': '...'}

[MASTER PROXY] Resposta do Lovable:
  Status: 202
  Body: (vazio)

[MASTER PROXY] ✅ Sucesso! Mensagem aceita pelo Lovable.
```

---

## ✅ Checklist de Uso:

- [ ] Extension recarregada
- [ ] Login feito no Lovable (conta desejada)
- [ ] Projeto aberto
- [ ] Sidebar apareceu
- [ ] Mensagem digitada
- [ ] Cookie capturado automaticamente
- [ ] Mensagem enviada (202)
- [ ] Preview atualizou
- [ ] Créditos da conta logada consumidos

---

## 🎉 Resultado Final:

**Sistema 100% automático!**

- ✅ Cookie capturado automaticamente
- ✅ Funciona em qualquer projeto
- ✅ Sem configuração manual
- ✅ Token sempre atualizado
- ✅ Multi-usuário

**Aproveite! 🚀**
