# 🚀 Guia de Instalação - Lovable Assistant v2.0

## ✨ Nova Versão com Sidebar Fixa!

A extensão agora funciona de forma completamente diferente:
- ✅ **Sidebar fixa** ao lado do Lovable (não some ao clicar)
- ✅ **Injeta comandos diretamente** no chat do Lovable
- ✅ **Não depende de backend** ou API externa
- ✅ **100% local e instantâneo**

---

## 📋 Pré-requisitos

- Google Chrome ou Edge (navegadores baseados em Chromium)
- Estar logado no [Lovable.dev](https://lovable.dev)

---

## 🔧 Instalação

### 1. Remover Versão Antiga (se instalada)

1. Abra `chrome://extensions/`
2. Encontre **Lovable Assistant** (versão antiga)
3. Clique em **Remover**

### 2. Instalar Nova Versão

1. Abra `chrome://extensions/`
2. Ative o **Modo desenvolvedor** (canto superior direito)
3. Clique em **Carregar sem compactação**
4. Selecione a pasta `extension/` deste projeto
5. A extensão será instalada

### 3. Recarregar a Extensão (após mudanças)

Se você fizer alterações no código:
1. Vá para `chrome://extensions/`
2. Encontre **Lovable Assistant**
3. Clique no ícone de **recarregar** (🔄)
4. Recarregue a página do Lovable.dev (F5)

---

## 🎯 Como Usar

### 1. Abrir o Lovable.dev

1. Acesse [lovable.dev](https://lovable.dev)
2. Faça login (se necessário)
3. Abra um projeto

### 2. A Sidebar Aparecerá Automaticamente

Quando você abrir um projeto no Lovable, a sidebar **Lovable Assistant** aparecerá automaticamente no lado direito da tela.

### 3. Enviar Comandos

1. Digite sua instrução no campo de texto da sidebar
2. Clique em **📤 Enviar** (ou pressione Enter)
3. A mensagem será injetada no chat do Lovable
4. O Lovable processará como se você tivesse digitado manualmente

### 4. Minimizar/Expandir

- Clique no botão **−** no canto superior direito da sidebar para minimizar
- Clique novamente para expandir

### 5. Limpar Histórico

- Clique em **🗑️ Limpar** no rodapé da sidebar

---

## 🔍 Como Funciona

### Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  Lovable.dev                              │ Sidebar Fixa    │
│  ┌─────────────────────────────────────┐  │ ┌─────────────┐ │
│  │                                     │  │ │ Lovable     │ │
│  │     Preview do Projeto              │  │ │ Assistant   │ │
│  │                                     │  │ │             │ │
│  │                                     │  │ │ [Histórico] │ │
│  │                                     │  │ │             │ │
│  └─────────────────────────────────────┘  │ │ [Input]     │ │
│  ┌─────────────────────────────────────┐  │ │ [Enviar]    │ │
│  │  Chat do Lovable (original)         │  │ └─────────────┘ │
│  └─────────────────────────────────────┘  │                 │
└─────────────────────────────────────────────────────────────┘
```

### Processo de Envio

1. **Você digita** na sidebar
2. **Content script** encontra o textarea do chat do Lovable
3. **Injeta a mensagem** no textarea
4. **Simula o clique** no botão de enviar
5. **Lovable processa** como se fosse digitado manualmente

---

## 🐛 Troubleshooting

### Sidebar não aparece

**Solução:**
1. Verifique se está em um projeto do Lovable (URL: `lovable.dev/projects/...`)
2. Recarregue a página (F5)
3. Verifique se a extensão está ativada em `chrome://extensions/`

### Erro: "Campo de chat não encontrado"

**Causa:** O Lovable mudou a estrutura do HTML

**Solução:**
1. Abra o DevTools (F12) na página do Lovable
2. Inspecione o textarea do chat
3. Anote o seletor CSS correto
4. Edite `content.js` e atualize os seletores:
```javascript
const chatInput = document.querySelector('textarea[placeholder*="Ask"]');
```

### Erro: "Botão de enviar não encontrado"

**Causa:** O Lovable mudou o botão de enviar

**Solução:**
1. Inspecione o botão de enviar no DevTools
2. Atualize o seletor em `content.js`:
```javascript
const sendButton = document.querySelector('button[type="submit"]');
```

### Sidebar sobrepõe o conteúdo

**Solução:**
A sidebar adiciona automaticamente `margin-right` ao body. Se não funcionar:
1. Clique no botão **−** para minimizar
2. Ou edite `SIDEBAR_WIDTH` em `content.js`

---

## ⚙️ Personalização

### Alterar Largura da Sidebar

Edite `content.js`:
```javascript
const SIDEBAR_WIDTH = '380px'; // Altere para o valor desejado
```

### Alterar Cores

Edite a função `injectStyles()` em `content.js`:
```javascript
background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
border-left: 2px solid #0f3460;
```

### Alterar Posição

Para mover para o lado esquerdo, edite em `injectStyles()`:
```javascript
right: 0;  // Mude para: left: 0;
```

E ajuste o margin:
```javascript
body.la-sidebar-active {
  margin-right: ${SIDEBAR_WIDTH};  // Mude para: margin-left
}
```

---

## 📝 Notas Importantes

### Diferenças da Versão Anterior

| Aspecto | v1.0 (Popup) | v2.0 (Sidebar) |
|---------|--------------|----------------|
| Interface | Popup que some | Sidebar fixa |
| Backend | Necessário | Não necessário |
| API Externa | Sim (Lovable API) | Não |
| Velocidade | Lenta | Instantânea |
| Confiabilidade | Depende de API | 100% local |

### Limitações

- **Depende da estrutura HTML do Lovable**: Se o Lovable mudar o HTML, pode ser necessário atualizar os seletores
- **Não funciona offline**: Precisa estar conectado ao Lovable.dev
- **Apenas Chrome/Edge**: Não funciona em Firefox (usa Manifest V3)

---

## 🎉 Pronto!

Agora você tem uma sidebar fixa que injeta comandos diretamente no chat do Lovable, sem depender de backend ou API externa!

**Aproveite! 🚀**
