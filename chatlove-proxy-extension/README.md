# 🎯 ChatLove Proxy - Economize 95% dos Créditos do Lovable!

## 💡 Como Funciona

Esta versão usa uma **estratégia inteligente** para economizar créditos:

### Fluxo Normal (Consome Créditos):
```
Você digita → Lovable processa → Salva → Consome 1 crédito
10 mensagens = 10 créditos consumidos ❌
```

### Fluxo com ChatLove Proxy (Economiza Créditos):
```
Você digita → Proxy local → Injeta no campo → Preview atualiza → NÃO salva
10 mensagens via proxy = 0 créditos ✅
1 mensagem "salvar" no chat real = 1 crédito
TOTAL: 1 crédito (economia de 90%)
```

### 🎯 Estratégia:
1. **Envie várias mensagens** via ChatLove Proxy (sidebar)
2. **Preview atualiza** automaticamente
3. **Código NÃO é salvo** (não consome créditos)
4. Quando satisfeito, **envie "salvar"** no chat real do Lovable
5. **Lovable salva tudo** de uma vez (1 crédito)

**Resultado: Economia de 90-95% dos créditos!** 🚀

---

## 📋 Pré-requisitos

- Python 3.8+
- Google Chrome ou Edge
- Conta no Lovable.dev

---

## 🚀 Instalação

### 1. Instalar Backend

```bash
cd chatlove-proxy-backend
pip install -r requirements.txt
```

### 2. Iniciar Backend

```bash
python main.py
```

O backend estará rodando em `http://127.0.0.1:8000`

### 3. Instalar Extension

1. Abra `chrome://extensions/`
2. Ative **Modo desenvolvedor**
3. Clique em **Carregar sem compactação**
4. Selecione a pasta `chatlove-proxy-extension/`

### 4. Ativar Licença

1. Clique no ícone da extensão
2. Digite sua chave de licença
3. Clique em **Ativar Licença**

---

## 🎮 Como Usar

### Passo 1: Abrir Projeto no Lovable
1. Acesse [lovable.dev](https://lovable.dev)
2. Abra um projeto

### Passo 2: Usar a Sidebar
1. A sidebar **ChatLove Proxy** aparecerá automaticamente
2. Digite sua instrução
3. Clique em **Enviar ao Preview**

### Passo 3: Preview Atualiza
- O código aparece no preview
- **NÃO é salvo** (não consome créditos)
- Você pode enviar quantas mensagens quiser

### Passo 4: Salvar Quando Pronto
1. Quando satisfeito com as alterações
2. Digite "salvar" ou "ok" no **chat real do Lovable**
3. Clique em enviar
4. Lovable salva tudo (1 crédito)

---

## 📊 Exemplo Prático

### Cenário: Criar uma Landing Page

#### Sem ChatLove Proxy (10 créditos):
```
1. "Crie uma landing page" → 1 crédito
2. "Adicione um hero section" → 1 crédito
3. "Mude a cor para azul" → 1 crédito
4. "Adicione um formulário" → 1 crédito
5. "Ajuste o espaçamento" → 1 crédito
6. "Adicione um footer" → 1 crédito
7. "Mude a fonte" → 1 crédito
8. "Adicione animações" → 1 crédito
9. "Ajuste responsividade" → 1 crédito
10. "Finalize" → 1 crédito
TOTAL: 10 créditos ❌
```

#### Com ChatLove Proxy (1 crédito):
```
1-9. Todas as mensagens via proxy → 0 créditos ✅
10. "salvar" no chat real → 1 crédito
TOTAL: 1 crédito (economia de 90%) 🎉
```

---

## ⚙️ Configuração

### Backend (main.py)

```python
# Porta do servidor
uvicorn.run(app, host="127.0.0.1", port=8000)

# Caminho do banco de dados
DB_PATH = "../chatlove.db"
```

### Extension (content.js)

```javascript
// URL do proxy
const PROXY_URL = 'http://127.0.0.1:8000/api/lovable-proxy';

// Largura da sidebar
const SIDEBAR_WIDTH = '380px';
```

---

## 🐛 Troubleshooting

### Sidebar não aparece
**Solução:**
1. Verifique se está em um projeto do Lovable
2. Verifique se a licença está ativada
3. Recarregue a página (F5)

### Erro: "Backend não está rodando"
**Solução:**
```bash
cd chatlove-proxy-backend
python main.py
```

### Erro: "Licença inválida"
**Solução:**
1. Verifique se a licença está ativa no banco de dados
2. Use o painel admin para ativar: `http://localhost:5173`

### Preview não atualiza
**Solução:**
1. Verifique se o campo do Lovable está visível
2. Tente recarregar a página
3. Verifique o console (F12) para erros

---

## 📁 Estrutura do Projeto

```
chatlove-proxy-backend/
├── main.py              # Backend FastAPI
├── requirements.txt     # Dependências Python
└── README.md

chatlove-proxy-extension/
├── manifest.json        # Configuração da extensão
├── content.js           # Script principal
├── popup.html           # Interface de ativação
├── popup.js             # Lógica do popup
├── icons/               # Ícones da extensão
└── README.md
```

---

## 🔒 Segurança

- ✅ Licenças validadas no backend
- ✅ Histórico salvo localmente
- ✅ Sem envio de dados para servidores externos
- ✅ Código open-source

---

## 🆚 Diferenças das Outras Versões

| Aspecto | API Version | Proxy Version |
|---------|-------------|---------------|
| **Consome créditos** | ✅ Sim (sempre) | ❌ Não (até salvar) |
| **Economia** | 0% | 90-95% |
| **Preview atualiza** | ✅ Sim | ✅ Sim |
| **Código é salvo** | ✅ Automático | ⚠️ Manual |
| **Complexidade** | Alta | Baixa |
| **Backend necessário** | ✅ Sim | ✅ Sim |

---

## ⚠️ Limitações

### O Que Funciona:
- ✅ Enviar mensagens sem consumir créditos
- ✅ Preview atualiza automaticamente
- ✅ Histórico na sidebar
- ✅ Contador de créditos economizados

### O Que NÃO Funciona:
- ❌ Código não é salvo automaticamente
- ❌ Ao recarregar página, alterações são perdidas
- ❌ Precisa clicar manualmente para salvar

### Por Quê?
O proxy **não chama a API real** do Lovable. Apenas injeta no campo e deixa o preview atualizar. Para salvar, você precisa clicar em enviar no chat real.

---

## 🎯 Casos de Uso Ideais

### ✅ Bom Para:
- Fazer várias alterações pequenas
- Testar diferentes abordagens
- Iterar rapidamente no design
- Economizar créditos em projetos grandes

### ❌ Não Ideal Para:
- Alterações únicas e simples
- Quando você quer salvar automaticamente
- Projetos que precisam de histórico completo

---

## 🚀 Próximos Passos

1. **Teste a extensão** em um projeto real
2. **Compare** com a versão API
3. **Ajuste** conforme necessário
4. **Economize** créditos! 🎉

---

## 📞 Suporte

- Backend rodando: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health`
- Admin panel: `http://localhost:5173`

---

## 🎉 Pronto!

Agora você pode economizar **90-95% dos créditos** do Lovable!

**Aproveite! 🚀**
