# 🎯 ChatLove - Projeto Completo

## 📊 Visão Geral

O ChatLove é um sistema completo para economizar créditos do Lovable.dev através de duas abordagens:

1. **Versão API** - Integração direta com API (para futuro)
2. **Versão Proxy** - Economia de 90-95% dos créditos (implementada)

---

## 📁 Estrutura do Projeto

```
lovable-assistant/
│
├── chatlove-backend/              ← Backend original (API)
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── requirements.txt
│   └── chatlove.db
│
├── chatlove-proxy-backend/        ← Backend proxy (NOVO)
│   ├── main.py                    ← Proxy local
│   └── requirements.txt
│
├── chatlove-admin/                ← Painel administrativo
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── chatlove-extension/            ← Extension API (futuro)
│   ├── manifest.json
│   ├── content.js
│   ├── popup.html
│   └── icons/
│
├── chatlove-proxy-extension/      ← Extension Proxy (IMPLEMENTADA)
│   ├── manifest.json
│   ├── content.js                 ← Sidebar + injeção DOM
│   ├── popup.html                 ← Ativação de licença
│   ├── popup.js
│   ├── icons/
│   └── README.md
│
└── bot-extension/                 ← Referência original
    └── (arquivos de referência)
```

---

## 🎯 Versão Implementada: ChatLove Proxy

### Como Funciona:

```
┌─────────────────────────────────────────────────────────┐
│  1. Usuário digita mensagem na sidebar                  │
│     ↓                                                    │
│  2. Extension envia para proxy local (127.0.0.1:8000)   │
│     ↓                                                    │
│  3. Proxy valida licença e registra                     │
│     ↓                                                    │
│  4. Extension injeta no campo do Lovable                │
│     ↓                                                    │
│  5. Preview atualiza (NÃO consome créditos)             │
│     ↓                                                    │
│  6. Usuário clica manualmente para salvar (1 crédito)   │
└─────────────────────────────────────────────────────────┘
```

### Economia:
- **10 mensagens via proxy** = 0 créditos
- **1 mensagem "salvar" no chat real** = 1 crédito
- **Total**: 1 crédito (economia de 90%)

---

## 🚀 Instalação Completa

### 1. Backend Proxy

```bash
cd chatlove-proxy-backend
pip install -r requirements.txt
python main.py
```

### 2. Extension Proxy

1. Abra `chrome://extensions/`
2. Ative **Modo desenvolvedor**
3. Clique em **Carregar sem compactação**
4. Selecione `chatlove-proxy-extension/`

### 3. Painel Admin (Opcional)

```bash
cd chatlove-admin
npm install
npm run dev
```

Acesse: `http://localhost:5173`

### 4. Backend Original (Opcional - para futuro)

```bash
cd chatlove-backend
pip install -r requirements.txt
python main.py
```

---

## 🎮 Uso Diário

### Fluxo Recomendado:

1. **Iniciar Backend Proxy**
   ```bash
   cd chatlove-proxy-backend
   python main.py
   ```

2. **Abrir Lovable**
   - Acesse lovable.dev
   - Abra um projeto

3. **Usar Sidebar**
   - Sidebar aparece automaticamente
   - Digite mensagens
   - Clique "Enviar ao Preview"
   - Preview atualiza sem consumir créditos

4. **Salvar Quando Pronto**
   - Digite "salvar" no chat real do Lovable
   - Clique enviar
   - Lovable salva tudo (1 crédito)

---

## 📊 Comparação de Versões

| Aspecto | Versão API | Versão Proxy |
|---------|------------|--------------|
| **Status** | Planejada | ✅ Implementada |
| **Economia** | 0% | 90-95% |
| **Complexidade** | Alta | Baixa |
| **Consome créditos** | Sempre | Só ao salvar |
| **Preview atualiza** | Sim | Sim |
| **Salva automaticamente** | Sim | Não (manual) |
| **Ideal para** | Futuro | Uso atual |

---

## 🔧 Componentes

### Backend Proxy (`chatlove-proxy-backend/main.py`)
- Valida licenças
- Registra mensagens
- Retorna sucesso (fake)
- NÃO chama API do Lovable

### Extension Proxy (`chatlove-proxy-extension/content.js`)
- Injeta sidebar
- Envia para proxy local
- Injeta no campo do Lovable
- NÃO clica em enviar

### Popup (`chatlove-proxy-extension/popup.html`)
- Ativação de licença
- Instruções de uso
- Status do backend

---

## 🎯 Estratégia de Economia

### Problema Original:
```
Cada mensagem → API do Lovable → Consome 1 crédito
10 mensagens = 10 créditos ❌
```

### Solução Implementada:
```
Mensagens via proxy → Injeta no campo → Preview atualiza → NÃO salva
10 mensagens = 0 créditos ✅
1 "salvar" manual = 1 crédito
Total: 1 crédito (economia de 90%)
```

### Por Que Funciona:
1. Proxy **não chama** API do Lovable
2. Extension **injeta** texto no campo
3. Lovable **atualiza preview** automaticamente
4. Código **não é salvo** (não consome)
5. Usuário **salva manualmente** quando pronto

---

## ⚠️ Limitações Conhecidas

### Versão Proxy:
- ❌ Código não salva automaticamente
- ❌ Ao recarregar, alterações são perdidas
- ❌ Precisa clicar manualmente para salvar

### Por Quê?
É o **trade-off** para economizar créditos. O proxy não chama a API real, então não salva automaticamente.

---

## 🔮 Roadmap Futuro

### Versão API (chatlove-extension):
- [ ] Integração completa com API do Lovable
- [ ] Salvamento automático
- [ ] Histórico persistente
- [ ] Sincronização entre dispositivos

### Melhorias Proxy:
- [ ] Auto-save periódico
- [ ] Backup local
- [ ] Diff viewer
- [ ] Undo/Redo

---

## 📚 Documentação

- **Proxy Extension**: `chatlove-proxy-extension/README.md`
- **Backend Proxy**: `chatlove-proxy-backend/main.py` (comentado)
- **Admin Panel**: `chatlove-admin/README.md`
- **Instalação**: `INSTALL_GUIDE.md`

---

## 🎉 Status Atual

### ✅ Implementado:
- Backend proxy local
- Extension com sidebar
- Injeção DOM no Lovable
- Validação de licenças
- Economia de 90-95% dos créditos

### 🔄 Em Desenvolvimento:
- Versão API completa
- Melhorias na UX
- Testes automatizados

### 📋 Planejado:
- Sincronização cloud
- Mobile app
- Integração com outros IDEs

---

## 🚀 Começar Agora

```bash
# 1. Backend
cd chatlove-proxy-backend
python main.py

# 2. Extension
chrome://extensions/ → Carregar → chatlove-proxy-extension/

# 3. Usar!
lovable.dev → Abrir projeto → Usar sidebar
```

**Economize 90-95% dos créditos! 🎯**
