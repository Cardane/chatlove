# 🐛 Debug - ChatLove Extension

## Problema Atual
- Licença ativa no popup ✅
- Mas ao enviar mensagem: **"Erro: Failed to fetch"** ❌
- Licença não marca como "usado" no admin ❌

## 🔍 Como Debugar

### 1. Abrir DevTools do Chrome
1. Vá em `chrome://extensions`
2. Encontre "ChatLove"
3. Clique em **"Inspecionar visualizações: service worker"** (background)
4. Isso abre o DevTools do background script

### 2. Abrir Console da Página
1. Abra um projeto no Lovable: https://lovable.dev/projects/...
2. Pressione **F12** (abre DevTools)
3. Vá na aba **Console**

### 3. Testar Manualmente no Console

Cole este código no console da página do Lovable:

```javascript
// Testar se consegue fazer fetch
fetch('http://209.38.79.211/api/health')
  .then(r => r.json())
  .then(d => console.log('✅ Health check OK:', d))
  .catch(e => console.error('❌ Erro:', e));

// Testar validação de licença
fetch('http://209.38.79.211/api/validate-license', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({license_key: 'SUA_CHAVE_AQUI'})
})
  .then(r => r.json())
  .then(d => console.log('✅ Licença:', d))
  .catch(e => console.error('❌ Erro:', e));

// Testar master-proxy
chrome.storage.local.get(['licenseKey'], (result) => {
  fetch('http://209.38.79.211/api/master-proxy', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      project_id: 'test',
      message: 'test',
      session_token: 'test',
      license_key: result.licenseKey
    })
  })
    .then(r => r.json())
    .then(d => console.log('✅ Master proxy:', d))
    .catch(e => console.error('❌ Erro:', e));
});
```

### 4. Verificar Erros Comuns

**Se aparecer erro de CORS:**
```
Access to fetch at 'http://209.38.79.211/...' from origin 'chrome-extension://...' has been blocked by CORS policy
```
→ Backend precisa permitir chrome-extension://

**Se aparecer erro de permissão:**
```
Failed to fetch
```
→ Verificar manifest.json tem `"http://209.38.79.211/*"` em host_permissions

**Se aparecer erro 401/403:**
```
{"detail":"Token inválido ou expirado"}
```
→ Cookie do Lovable não foi capturado ou licença inválida

### 5. Verificar Cookie

No console da página do Lovable:
```javascript
// Ver se tem cookie
document.cookie.split(';').forEach(c => console.log(c.trim()));

// Testar captura de cookie via background
chrome.runtime.sendMessage(
  {action: 'getCookie'},
  (response) => console.log('Cookie:', response)
);
```

### 6. Verificar Licença Salva

No console:
```javascript
chrome.storage.local.get(['licenseKey', 'userName'], (result) => {
  console.log('Licença salva:', result);
});
```

## 📋 Checklist de Verificação

- [ ] Extension recarregada após atualizar manifest.json?
- [ ] Permissão para `http://209.38.79.211/*` aceita?
- [ ] Logado no Lovable (tem cookie)?
- [ ] Licença válida e ativa no admin?
- [ ] Console mostra algum erro específico?
- [ ] Background script mostra algum erro?

## 🔧 Possíveis Soluções

### Solução 1: Recarregar Extension Completamente
1. `chrome://extensions`
2. **Desativar** ChatLove
3. **Ativar** novamente
4. Aceitar permissões
5. Recarregar página do Lovable

### Solução 2: Limpar Storage
No console:
```javascript
chrome.storage.local.clear(() => {
  console.log('Storage limpo. Reative a licença.');
});
```

### Solução 3: Verificar Backend
```bash
ssh root@209.38.79.211
systemctl status chatlove-backend
journalctl -u chatlove-backend -f
```

## 📤 Me Envie

Depois de fazer os testes acima, me envie:

1. **Erro exato do console** (screenshot ou texto)
2. **Resultado do teste de fetch** (health check)
3. **Resultado do teste de licença**
4. **Logs do background script** (se houver)

Com essas informações consigo identificar o problema exato! 🎯
