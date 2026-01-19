# 🚀 Guia Completo de Teste - ChatLove Proxy

## 📊 Arquitetura Simplificada

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  TERMINAL 1: BACKEND ADMIN (chatlove-backend)           │
│  Porta: 8000                                            │
│  Função: API para gerenciar licenças                    │
│  Banco: chatlove.db                                     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TERMINAL 2: ADMIN PANEL (chatlove-admin)               │
│  Porta: 5173                                            │
│  Função: Interface web para criar licenças              │
│  Conecta: Backend Admin (porta 8000)                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TERMINAL 3: BACKEND PROXY (chatlove-proxy-backend)     │
│  Porta: 8001                                            │
│  Função: Validar licenças + registrar mensagens         │
│  Banco: ../chatlove.db (mesmo banco!)                   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  EXTENSION PROXY (chatlove-proxy-extension)             │
│  Função: Sidebar no Lovable.dev                         │
│  Conecta: Backend Proxy (porta 8001)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 🎯 Resumo dos 3 Terminais:

| Terminal | Comando | Porta | Função |
|----------|---------|-------|--------|
| **Terminal 1** | `cd chatlove-backend && python main.py` | 8000 | Backend Admin (API) |
| **Terminal 2** | `cd chatlove-admin && npm run dev` | 5173 | Admin Panel (Frontend) |
| **Terminal 3** | `cd chatlove-proxy-backend && python main.py` | 8001 | Backend Proxy |

---

## ✅ Passo 1: Iniciar Backend Admin

### 1.1 Abrir Terminal 1

```bash
cd chatlove-backend
python main.py
```

### 1.2 Verificar Saída

Deve mostrar:
```
============================================================
CHATLOVE API
============================================================
Server: http://127.0.0.1:8000
Docs:   http://127.0.0.1:8000/docs
============================================================
[OK] Database initialized successfully!
[INFO] Admin already exists
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 1.3 Testar Backend Admin

Abra no navegador:
```
http://127.0.0.1:8000
```

Deve mostrar:
```json
{
  "name": "ChatLove API",
  "version": "1.0.0",
  "status": "running"
}
```

✅ **Backend Admin OK!**

---

## ✅ Passo 2: Iniciar Admin Panel (Frontend)

### 2.1 Abrir Terminal 2 (NOVO)

```bash
cd chatlove-admin
npm run dev
```

### 2.2 Verificar Saída

Deve mostrar:
```
VITE v5.0.8  ready in XXX ms
➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### 2.3 Acessar Admin Panel

Abra no navegador:
```
http://localhost:5173
```

### 2.4 Fazer Login

- **Usuário:** admin
- **Senha:** admin123

### 2.5 Criar Licença

1. Vá em **"Licenças"**
2. Clique em **"Nova Licença"**
3. Copie a chave gerada (ex: `LOVE-XXXX-XXXX-XXXX-XXXX`)

✅ **Licença criada!**

---

## ✅ Passo 3: Iniciar Backend Proxy

### 3.1 Abrir Terminal 3 (NOVO)

```bash
cd chatlove-proxy-backend
python main.py
```

### 3.2 Verificar Saída

Deve mostrar:
```
============================================================
CHATLOVE PROXY API
============================================================
Server: http://127.0.0.1:8001
Função: Validar licenças e registrar mensagens
NÃO consome créditos do Lovable!
============================================================
INFO:     Uvicorn running on http://127.0.0.1:8001
```

### 3.3 Testar Backend Proxy

Abra no navegador:
```
http://127.0.0.1:8001
```

Deve mostrar:
```json
{
  "name": "ChatLove Proxy API",
  "version": "1.0.0",
  "status": "running"
}
```

✅ **Backend Proxy OK!**

---

## ✅ Passo 4: Instalar Extension no Chrome

### 4.1 Abrir Chrome Extensions

```
chrome://extensions/
```

### 4.2 Ativar Modo Desenvolvedor

Clique no toggle **"Modo desenvolvedor"** (canto superior direito)

### 4.3 Carregar Extension

1. Clique em **"Carregar sem compactação"**
2. Navegue até: `c:\projetos\lovable-assistant\chatlove-proxy-extension`
3. Selecione a pasta
4. Clique em **"Selecionar pasta"**

### 4.4 Verificar Instalação

Deve aparecer:
```
ChatLove Proxy
v1.0.0
Economize 95% dos créditos do Lovable...
```

✅ **Extension instalada!**

---

## ✅ Passo 5: Ativar Licença na Extension

### 5.1 Clicar no Ícone da Extension

Clique no ícone ♥ do ChatLove Proxy na barra do Chrome

### 5.2 Inserir Licença

Cole a chave de licença criada no Passo 2.3

### 5.3 Clicar em "Ativar Licença"

Deve mostrar:
```
✅ Licença ativada! Abra um projeto no Lovable.
```

✅ **Licença ativada!**

---

## ✅ Passo 6: Testar no Lovable.dev

### 6.1 Acessar Lovable

```
https://lovable.dev
```

### 6.2 Fazer Login

Use suas credenciais do Lovable

### 6.3 Abrir um Projeto

Abra qualquer projeto existente ou crie um novo

### 6.4 Verificar Sidebar

Deve aparecer uma **sidebar roxa** no lado direito com:
- Logo ♥
- "ChatLove Proxy"
- "Créditos Economizados: 0"
- Campo de texto
- Botão "Enviar ao Preview"

✅ **Sidebar apareceu!**

---

## ✅ Passo 7: Enviar Mensagem de Teste

### 7.1 Digitar Mensagem

Na sidebar, digite:
```
Crie um botão azul com texto "Clique aqui"
```

### 7.2 Clicar em "Enviar ao Preview"

Aguarde alguns segundos...

### 7.3 Verificar Resultado

Deve mostrar na sidebar:
```
✅ Enviado ao preview (não salvo)
💡 Para salvar, clique em enviar no chat real do Lovable
```

### 7.4 Verificar Campo do Lovable

O campo de chat do Lovable deve ter a mensagem:
```
Crie um botão azul com texto "Clique aqui"
```

### 7.5 Verificar Preview

O preview do Lovable deve atualizar automaticamente!

✅ **Mensagem enviada sem consumir créditos!**

---

## ✅ Passo 8: Salvar Alterações (Opcional)

### 8.1 Quando Satisfeito

Quando estiver satisfeito com as alterações no preview...

### 8.2 Enviar no Chat Real

No **chat real do Lovable** (não na sidebar), digite:
```
salvar
```

### 8.3 Clicar em Enviar

Clique no botão de enviar do Lovable

### 8.4 Resultado

O Lovable vai salvar todas as alterações (consome 1 crédito)

✅ **Alterações salvas!**

---

## 📊 Verificar Estatísticas

### Sidebar

- **Créditos Economizados:** Deve aumentar a cada mensagem enviada

### Backend Proxy (Terminal 2)

Deve mostrar logs:
```
INFO:     127.0.0.1:xxxxx - "POST /api/lovable-proxy HTTP/1.1" 200 OK
```

### Banco de Dados

```bash
sqlite3 chatlove-backend/chatlove.db "SELECT * FROM proxy_messages;"
```

Deve mostrar as mensagens registradas

---

## 🐛 Troubleshooting

### Sidebar não aparece

**Causa:** Licença não ativada ou backend proxy não está rodando

**Solução:**
1. Verifique se backend proxy está rodando (porta 8001)
2. Verifique se licença está ativada na extension
3. Recarregue a página do Lovable (F5)

### Erro: "Licença inválida"

**Causa:** Licença não existe no banco de dados

**Solução:**
1. Verifique se backend admin está rodando (porta 8000)
2. Crie uma nova licença no admin panel
3. Ative novamente na extension

### Erro: "Backend não está rodando"

**Causa:** Backend proxy não está rodando

**Solução:**
```bash
cd chatlove-proxy-backend
python main.py
```

### Preview não atualiza

**Causa:** Campo do Lovable não foi encontrado

**Solução:**
1. Verifique se está em um projeto do Lovable
2. Verifique se o campo de chat está visível
3. Abra o console (F12) e veja os logs

### Mensagem não injeta

**Causa:** Seletor do campo mudou

**Solução:**
1. Abra o console (F12)
2. Veja os logs do ChatLove Proxy
3. Reporte o problema

---

## 📈 Economia de Créditos

### Exemplo Prático:

#### Sem ChatLove Proxy:
```
1. "Crie um botão azul" → 1 crédito
2. "Mude para vermelho" → 1 crédito
3. "Adicione um ícone" → 1 crédito
4. "Ajuste o tamanho" → 1 crédito
5. "Centralize" → 1 crédito
TOTAL: 5 créditos ❌
```

#### Com ChatLove Proxy:
```
1-4. Todas via proxy → 0 créditos ✅
5. "salvar" no chat real → 1 crédito
TOTAL: 1 crédito (economia de 80%) 🎉
```

---

## ✅ Checklist Final

- [ ] Backend Admin rodando (porta 8000)
- [ ] Licença criada no admin panel
- [ ] Backend Proxy rodando (porta 8001)
- [ ] Extension instalada no Chrome
- [ ] Licença ativada na extension
- [ ] Sidebar aparece no Lovable
- [ ] Mensagem enviada com sucesso
- [ ] Preview atualiza automaticamente
- [ ] Créditos economizados aumentam

---

## 🎉 Pronto!

Agora você pode economizar **90-95% dos créditos** do Lovable!

**Aproveite! 🚀**
