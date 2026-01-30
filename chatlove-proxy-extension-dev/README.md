# 🚀 ChatLove Proxy Extension DEV

**Versão de desenvolvimento** com recursos avançados: Plan vs Builder Mode, interceptação de respostas e resolução automática de "pendente de salvar".

## 🆕 Novos Recursos

### 1. **Plan vs Builder Mode**
- **🔨 Builder Mode**: Executa mudanças no código (padrão)
- **📋 Plan Mode**: Apenas planejamento, IA responde sem executar código

### 2. **Status de Salvamento Inteligente**
- **💾 Pronto**: Sistema aguardando
- **⏳ Enviando**: Mensagem sendo processada
- **✅ Salvo**: Alterações salvas com sucesso
- **❌ Erro**: Problema no salvamento

### 3. **Interceptação de Respostas**
- Captura requisições da Lovable em tempo real
- Monitora streaming de respostas
- Tenta resolver automaticamente o problema de "pendente"

### 4. **Salvamento Automático**
- Detecta quando mensagem fica "pendente"
- Tenta múltiplas estratégias para finalizar salvamento
- Simula cliques em botões de confirmação
- Usa atalhos de teclado (Ctrl+S)

## 🔧 Instalação

### 1. Carregar Extensão
```bash
# Abrir Chrome
chrome://extensions/

# Ativar modo desenvolvedor
# Clicar em "Carregar sem compactação"
# Selecionar pasta: chatlove-proxy-extension-dev/
```

### 2. Ativar Licença
1. Clicar no ícone da extensão
2. Inserir chave de licença
3. Clicar "Ativar"

### 3. Usar no Lovable
1. Abrir projeto no Lovable.dev
2. Sidebar aparece automaticamente
3. Escolher modo (Plan/Builder)
4. Enviar mensagens

## 🎯 Como Usar

### **Modo Builder (Padrão)**
```
1. Selecionar "🔨 Builder"
2. Digite: "Crie um componente de login"
3. Clique "Enviar"
4. ✅ Código é gerado e executado
5. 💾 Status mostra progresso do salvamento
```

### **Modo Plan**
```
1. Selecionar "📋 Plan"
2. Digite: "Como implementar autenticação?"
3. Clique "Enviar"
4. ✅ IA responde com planejamento
5. 💾 Não executa código
```

## 🔍 Debug e Monitoramento

### **Console do Navegador (F12)**
```javascript
// Ver interceptações em tempo real
window.debugInterceptor.start()

// Parar interceptação
window.debugInterceptor.stop()

// Ver requisições capturadas
window.debugInterceptor.requests()

// Exportar dados
window.debugInterceptor.export()

// Limpar dados
window.debugInterceptor.clear()
```

### **Logs Importantes**
```
[ChatLove] Modo alterado para: builder
[ChatLove] Enviando mensagem em modo: plan
[Interceptor] 📤 Request: POST /projects/.../chat
[Interceptor] 📥 Response: 202 Accepted
[ChatLove] Tentando finalizar salvamento...
[ChatLove] Encontrado indicador pendente: .text-orange-500
```

## 🆚 Diferenças da Versão Produção

| Recurso | Produção | DEV |
|---------|----------|-----|
| **Plan vs Builder** | ❌ | ✅ |
| **Status Salvamento** | ❌ | ✅ |
| **Interceptação** | ❌ | ✅ |
| **Auto-Save** | ❌ | ✅ |
| **Debug Tools** | ❌ | ✅ |
| **Permissões** | Básicas | Avançadas |

## 🔧 Configuração Avançada

### **Manifest.json**
```json
{
  "name": "ChatLove DEV",
  "version": "2.0.0",
  "permissions": [
    "cookies", "storage", "tabs",
    "webRequest", "webRequestBlocking"  // ← Novo
  ],
  "content_scripts": [
    {
      "js": ["interceptor.js", "content.js"]  // ← Interceptor
    }
  ]
}
```

### **Interceptor Ativo**
- Monitora todas as requisições para `*.lovable.dev`
- Captura respostas de chat e streaming
- Envia dados para extensão via `postMessage`

### **Estratégias de Auto-Save**
1. **Detectar Pendente**: Procura indicadores visuais
2. **Botões Save**: Clica em botões de confirmação
3. **Atalhos**: Simula Ctrl+S
4. **Submit**: Clica no último botão submit visível

## 🧪 Testes

### **Teste 1: Plan Mode**
```
1. Selecionar modo Plan
2. Enviar: "Explique como funciona React hooks"
3. Verificar: IA responde sem executar código
4. Status: "Resposta recebida"
```

### **Teste 2: Builder Mode**
```
1. Selecionar modo Builder
2. Enviar: "Adicione um botão vermelho"
3. Verificar: Código é gerado
4. Status: "Salvo automaticamente" ou "Pendente"
```

### **Teste 3: Interceptação**
```
1. Abrir F12 > Console
2. Executar: window.debugInterceptor.start()
3. Enviar mensagem
4. Verificar logs de requisições
```

### **Teste 4: Auto-Save**
```
1. Enviar mensagem que gera código
2. Observar status mudando:
   - "Enviando..." → "Aguardando resposta..." → "Salvo"
3. Se ficar "Pendente", aguardar tentativa automática
```

## 🐛 Troubleshooting

### **Problema: Modo não muda**
```javascript
// Verificar se botões estão funcionando
document.querySelectorAll('.cl-mode-btn').forEach(btn => {
  console.log(btn.dataset.mode, btn.classList.contains('active'));
});
```

### **Problema: Interceptação não funciona**
```javascript
// Verificar se interceptor está ativo
console.log(window.lovableInterceptor);
window.lovableInterceptor.startRecording();
```

### **Problema: Auto-save falha**
```javascript
// Verificar indicadores pendentes
document.querySelectorAll('[class*="pending"], .text-orange-500').forEach(el => {
  console.log('Pendente encontrado:', el);
});
```

### **Problema: Permissões negadas**
1. Ir em `chrome://extensions/`
2. Encontrar "ChatLove DEV"
3. Clicar "Detalhes"
4. Verificar se todas as permissões estão ativadas

## 📊 Métricas e Analytics

### **Status Tracking**
- Mensagens enviadas por modo
- Taxa de sucesso de auto-save
- Tempo médio de processamento
- Erros interceptados

### **Performance**
- Interceptação: ~5ms overhead
- Auto-save: 2-5 segundos
- Detecção de modo: Instantânea

## 🔄 Próximas Features

### **Em Desenvolvimento**
- [ ] Interceptação de respostas em tempo real na sidebar
- [ ] Histórico persistente por projeto
- [ ] Configurações avançadas de auto-save
- [ ] Métricas detalhadas de uso

### **Planejado**
- [ ] Suporte a múltiplas contas master
- [ ] Sincronização entre projetos
- [ ] Backup automático de código
- [ ] Integração com Git

## 🚀 Deploy para Produção

Quando todas as features estiverem testadas:

```bash
# 1. Testar extensão DEV completamente
# 2. Copiar arquivos para extensão produção
cp chatlove-proxy-extension-dev/* chatlove-proxy-extension/

# 3. Atualizar manifest da produção
# 4. Testar em ambiente de produção
# 5. Deploy na VPS
```

## 📝 Changelog

### **v2.0.0 (DEV)**
- ✅ Adicionado Plan vs Builder Mode
- ✅ Implementado status de salvamento
- ✅ Criado sistema de interceptação
- ✅ Desenvolvido auto-save inteligente
- ✅ Adicionadas ferramentas de debug

### **v1.0.0 (Produção)**
- ✅ Sistema básico de proxy
- ✅ Captura de cookies
- ✅ Controle de licenças
- ✅ Interface sidebar

---

**🎯 Objetivo**: Criar a extensão mais avançada para economizar créditos do Lovable, com controle total sobre o processo e resolução automática de problemas.

**🔧 Status**: Em desenvolvimento ativo - pronta para testes!