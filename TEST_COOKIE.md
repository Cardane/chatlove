# 🍪 Teste de Captura de Cookie

## Problema
- Backend funcionando ✅
- Usuário logado no Lovable ✅
- Mas ainda "Failed to fetch" ❌

## 🧪 Teste Manual

### 1. Abra o Console do Background Script

1. Vá em `chrome://extensions`
2. Encontre "ChatLove"
3. Clique em **"Inspecionar visualizações: service worker"**
4. Isso abre o DevTools do background script

### 2. Cole este código no console do background:

```javascript
// Testar captura de cookie
chrome.cookies.get(
  {
    url: "https://lovable.dev",
    name: "lovable-session-id.id"
  },
  (cookie) => {
    if (cookie && cookie.value) {
      console.log('✅ Cookie encontrado:', cookie.value.substring(0, 50) + '...');
      console.log('Cookie completo:', cookie);
    } else {
      console.error('❌ Cookie NÃO encontrado!');
      console.log('Tentando listar todos os cookies do Lovable...');
      
      chrome.cookies.getAll(
        { url: "https://lovable.dev" },
        (cookies) => {
          console.log('Cookies disponíveis:', cookies);
        }
      );
    }
  }
);
```

### 3. Verifique o resultado:

**Se aparecer "Cookie encontrado":**
→ Cookie está sendo capturado corretamente
→ Problema é outro (veja próximos passos)

**Se aparecer "Cookie NÃO encontrado":**
→ Nome do cookie pode estar errado
→ Veja a lista de cookies disponíveis
→ Me envie os nomes dos cookies

### 4. Teste a requisição completa:

Cole no console do background:

```javascript
// Capturar cookie e testar requisição
chrome.cookies.get(
  {
    url: "https://lovable.dev",
    name: "lovable-session-id.id"
  },
  async (cookie) => {
    if (!cookie) {
      console.error('❌ Cookie não encontrado');
      return;
    }
    
    console.log('✅ Cookie:', cookie.value.substring(0, 50));
    
    // Testar requisição
    try {
      const response = await fetch('http://209.38.79.211/api/master-proxy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          project_id: 'test',
          message: 'test message',
          session_token: cookie.value,
          license_key: 'SUA_CHAVE_AQUI'  // ← COLOQUE SUA CHAVE
        })
      });
      
      const data = await response.json();
      console.log('📡 Resposta:', data);
      console.log('Status:', response.status);
      
    } catch (error) {
      console.error('❌ Erro na requisição:', error);
    }
  }
);
```

### 5. Teste alternativo - Console da página do Lovable:

Abra um projeto no Lovable, pressione F12, e cole:

```javascript
// Ver todos os cookies
document.cookie.split(';').forEach(c => console.log(c.trim()));

// Testar se extension consegue capturar
chrome.runtime.sendMessage(
  { action: 'getCookie' },
  (response) => {
    if (response && response.cookie) {
      console.log('✅ Extension capturou cookie:', response.cookie.substring(0, 50));
    } else {
      console.error('❌ Extension NÃO capturou cookie');
    }
  }
);
```

## 📤 Me envie:

1. **Resultado do teste de captura de cookie** (encontrado ou não?)
2. **Lista de cookies disponíveis** (se não encontrou)
3. **Resposta da requisição de teste** (status e mensagem)
4. **Qualquer erro que aparecer no console**

Com essas informações vou saber exatamente qual é o problema! 🎯
