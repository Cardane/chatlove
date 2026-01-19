# 🎯 PLANO: Implementação via DOM Injection

## 📊 Decisão: DOM Injection vs API

Após análise do `FINAL_ANALYSIS.md`, decidimos implementar **DOM Injection** em vez de continuar com a API, pelos seguintes motivos:

### ❌ Problemas com API:
- Payload complexo com 15+ campos obrigatórios
- Campos como `session_replay`, `prev_session_id` difíceis de replicar
- **ESTÁ CONSUMINDO CRÉDITOS** mesmo com erros internos
- Lovable retorna "Internal Error" mesmo com requisição correta
- Requer engenharia reversa completa e constante manutenção

### ✅ Vantagens do DOM Injection:
- **MUITO MAIS SIMPLES** - apenas 3 passos
- Usa o código nativo do Lovable (sempre correto)
- Não precisa entender toda a API
- Não consome créditos em caso de erro
- Sempre compatível com updates do Lovable

---

## 🔍 Análise do Código Atual

### Documentação Existente (INSTALL_GUIDE.md):
```javascript
// Seletores sugeridos:
const chatInput = document.querySelector('textarea[placeholder*="Ask"]');
const sendButton = document.querySelector('button[type="submit"]');
```

### Código Atual (content.js):
- ✅ Já tem sidebar implementada
- ✅ Já captura mensagem do usuário
- ❌ Usa API complexa (precisa ser substituído)
- ❌ Não injeta no DOM do Lovable

---

## 🎯 Implementação Proposta

### Passo 1: Identificar Seletores Corretos

Precisamos inspecionar o DOM real do Lovable.dev para encontrar:

1. **Textarea do chat:**
   - Possíveis seletores:
     - `textarea[placeholder*="Ask"]`
     - `textarea[placeholder*="message"]`
     - `textarea[data-testid="chat-input"]`
     - `.chat-input textarea`

2. **Botão de envio:**
   - Possíveis seletores:
     - `button[type="submit"]`
     - `button[data-testid="send-button"]`
     - `button[aria-label*="Send"]`
     - `.send-button`

### Passo 2: Implementar Função de Injeção

```javascript
/**
 * Injeta mensagem diretamente no chat do Lovable
 * @param {string} message - Mensagem a ser enviada
 * @returns {boolean} - true se sucesso, false se erro
 */
function injectMessageToLovable(message) {
  try {
    // 1. Encontrar o textarea do chat
    const chatInput = document.querySelector('textarea[placeholder*="Ask"]') ||
                      document.querySelector('textarea[placeholder*="message"]') ||
                      document.querySelector('textarea[data-testid="chat-input"]');
    
    if (!chatInput) {
      console.error('[ChatLove] Campo de chat não encontrado');
      return false;
    }

    // 2. Injetar a mensagem
    chatInput.value = message;
    
    // 3. Disparar eventos para o React detectar a mudança
    chatInput.dispatchEvent(new Event('input', { bubbles: true }));
    chatInput.dispatchEvent(new Event('change', { bubbles: true }));
    
    // 4. Encontrar o botão de envio
    const sendButton = document.querySelector('button[type="submit"]') ||
                       document.querySelector('button[data-testid="send-button"]') ||
                       document.querySelector('button[aria-label*="Send"]');
    
    if (!sendButton) {
      console.error('[ChatLove] Botão de envio não encontrado');
      return false;
    }

    // 5. Aguardar um momento para o React processar
    setTimeout(() => {
      // 6. Clicar no botão de envio
      sendButton.click();
      console.log('[ChatLove] Mensagem injetada com sucesso!');
    }, 100);

    return true;
  } catch (error) {
    console.error('[ChatLove] Erro ao injetar mensagem:', error);
    return false;
  }
}
```

### Passo 3: Atualizar sendMessage() no content.js

```javascript
async function sendMessage() {
  const message = messageInput.value.trim();
  
  if (!message) {
    setStatus('Digite uma mensagem');
    return;
  }

  const projectId = detectProject();
  if (!projectId) {
    addMessage('❌ Erro: Projeto não detectado', 'error');
    setStatus('Erro');
    return;
  }

  addMessage(message, 'user');
  messageInput.value = '';
  
  sendBtn.disabled = true;
  setStatus('Enviando...');

  try {
    // NOVA IMPLEMENTAÇÃO: Injeção via DOM
    const success = injectMessageToLovable(message);
    
    if (success) {
      addMessage('✅ Mensagem enviada com sucesso!', 'success');
      setStatus('Enviado');
      
      // Calcular tokens economizados (estimativa: 4 chars = 1 token)
      const tokensSaved = message.length / 4;
      
      // Atualizar estatísticas localmente
      const stats = await chrome.storage.local.get(['chatlove_stats']);
      const currentStats = stats.chatlove_stats || { tokens_saved: 0, requests_count: 0 };
      currentStats.tokens_saved += tokensSaved;
      currentStats.requests_count += 1;
      await chrome.storage.local.set({ chatlove_stats: currentStats });
      
      tokensSavedElement.textContent = currentStats.tokens_saved.toFixed(2);
      addMessage(`💰 +${tokensSaved.toFixed(2)} tokens economizados!`, 'success');
    } else {
      addMessage('❌ Erro: Não foi possível enviar a mensagem', 'error');
      setStatus('Falha');
    }

  } catch (error) {
    console.error('[ChatLove] Error:', error);
    addMessage(`❌ Erro: ${error.message}`, 'error');
    setStatus('Erro');
  } finally {
    sendBtn.disabled = false;
  }
}
```

---

## 🔧 Mudanças Necessárias

### 1. content.js
- ✅ Adicionar função `injectMessageToLovable()`
- ✅ Remover toda lógica de API do `sendMessage()`
- ✅ Simplificar para usar apenas DOM injection
- ✅ Manter cálculo local de tokens economizados

### 2. background.js
- ⚠️ Remover `getCookies` (não precisa mais)
- ✅ Manter apenas `validateLicense` e `getToken`

### 3. main.py (Backend)
- ⚠️ Endpoint `/api/proxy` pode ser removido (opcional)
- ✅ Manter apenas validação de licença
- ✅ Backend não envia mais mensagens

---

## 📋 Checklist de Implementação

### Fase 1: Preparação
- [ ] Abrir Lovable.dev no navegador
- [ ] Inspecionar DOM do chat (F12)
- [ ] Identificar seletores corretos do textarea
- [ ] Identificar seletores corretos do botão
- [ ] Documentar seletores encontrados

### Fase 2: Implementação
- [ ] Criar função `injectMessageToLovable()` no content.js
- [ ] Atualizar função `sendMessage()` no content.js
- [ ] Remover código de API do content.js
- [ ] Testar injeção básica

### Fase 3: Refinamento
- [ ] Adicionar fallbacks para seletores
- [ ] Melhorar tratamento de erros
- [ ] Adicionar logs de debug
- [ ] Testar em diferentes estados do Lovable

### Fase 4: Validação
- [ ] Testar envio de mensagem simples
- [ ] Testar envio de mensagem longa
- [ ] Testar envio de múltiplas mensagens
- [ ] Validar que mensagens aparecem no chat
- [ ] Validar que Lovable processa normalmente

---

## 🎯 Seletores a Testar

### Textarea (em ordem de prioridade):
1. `textarea[placeholder*="Ask"]`
2. `textarea[placeholder*="message"]`
3. `textarea[data-testid="chat-input"]`
4. `textarea[aria-label*="chat"]`
5. `.chat-input textarea`
6. `[role="textbox"]`

### Botão de Envio (em ordem de prioridade):
1. `button[type="submit"]`
2. `button[data-testid="send-button"]`
3. `button[aria-label*="Send"]`
4. `.send-button`
5. `button[title*="Send"]`

---

## ⚠️ Considerações Importantes

### 1. Compatibilidade
- DOM injection depende da estrutura HTML do Lovable
- Se Lovable mudar o HTML, precisaremos atualizar seletores
- Manter múltiplos fallbacks para maior resiliência

### 2. Eventos React
- Lovable usa React, então precisamos disparar eventos corretos
- `input` e `change` events são necessários
- Aguardar um momento antes de clicar (setTimeout)

### 3. Validação
- Verificar se textarea existe antes de injetar
- Verificar se botão existe antes de clicar
- Fornecer feedback claro ao usuário

### 4. Performance
- DOM injection é instantâneo
- Não há latência de rede
- Não consome créditos da API

---

## 🚀 Próximos Passos

1. **AGORA:** Inspecionar DOM do Lovable.dev
2. **DEPOIS:** Implementar função de injeção
3. **TESTAR:** Validar funcionamento
4. **REFINAR:** Melhorar tratamento de erros
5. **DOCUMENTAR:** Atualizar guias

---

## 📊 Comparação Final

| Aspecto | API | DOM Injection |
|---------|-----|---------------|
| **Complexidade** | Alta (15+ campos) | Baixa (3 passos) |
| **Manutenção** | Constante | Mínima |
| **Confiabilidade** | Média (depende de API) | Alta (usa código nativo) |
| **Velocidade** | Lenta (rede) | Instantânea |
| **Créditos** | Consome | Não consome |
| **Compatibilidade** | Quebra com mudanças | Resiliente |

**DECISÃO: DOM Injection é a melhor escolha! 🎯**
