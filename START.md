# 🚀 ChatLove - Guia de Inicialização

## 📁 Estrutura do Projeto

```
chatlove/
├── chatlove-backend/          # Backend unificado (porta 8000)
├── chatlove-admin/            # Frontend admin (porta 3000)
└── chatlove-proxy-extension/  # Extension Chrome
```

---

## ⚙️ Pré-requisitos

- **Python 3.8+**
- **Node.js 16+**
- **Chrome/Edge** (para extension)

---

## 🔧 Instalação

### 1. Backend

```bash
cd chatlove-backend
pip install -r requirements.txt
```

### 2. Admin Panel

```bash
cd chatlove-admin
npm install
```

### 3. Extension

Não precisa instalar nada, apenas carregar no Chrome.

---

## 🚀 Como Iniciar

### **Opção 1: Desenvolvimento Local**

#### Terminal 1 - Backend (porta 8000):
```bash
cd chatlove-backend
python main.py
```

#### Terminal 2 - Admin Panel (porta 3000):
```bash
cd chatlove-admin
npm run dev
```

#### Extension:
1. Abrir Chrome: `chrome://extensions/`
2. Ativar "Modo do desenvolvedor"
3. Clicar em "Carregar sem compactação"
4. Selecionar pasta `chatlove-proxy-extension/`

---

## 📊 Acessos

- **Backend API:** http://127.0.0.1:8000
- **API Docs:** http://127.0.0.1:8000/docs
- **Admin Panel:** http://127.0.0.1:3000

**Login padrão:**
- Usuário: `admin`
- Senha: `admin123`

⚠️ **IMPORTANTE:** Altere a senha após primeiro login!

---

## 🎯 Fluxo de Uso

### 1. Criar Licença (Admin Panel)

1. Acessar http://127.0.0.1:3000
2. Login com admin/admin123
3. Ir em "Licenças"
4. Clicar em "Nova Licença"
5. Copiar chave gerada

### 2. Ativar Extension

1. Abrir projeto no Lovable.dev
2. Clicar no ícone da extension
3. Digitar nome e colar chave de licença
4. Clicar em "Ativar"
5. Página recarrega automaticamente
6. Sidebar aparece na direita

### 3. Usar ChatLove

1. Digitar mensagem na sidebar
2. Clicar em "Enviar"
3. Mensagem é enviada ao Lovable
4. Créditos são economizados
5. Total aparece na sidebar

---

## 🔍 Endpoints Principais

### Backend (porta 8000)

**Admin:**
- `POST /api/admin/login` - Login admin
- `GET /api/admin/dashboard` - Estatísticas
- `GET /api/admin/users` - Listar usuários
- `GET /api/admin/licenses` - Listar licenças

**Licenças:**
- `POST /api/validate-license` - Validar licença (popup)
- `POST /api/master-proxy` - Enviar mensagem ao Lovable

**Créditos:**
- `POST /api/credits/log` - Registrar créditos
- `GET /api/credits/total/{license_key}` - Total de créditos

---

## 🐛 Troubleshooting

### Backend não inicia

```bash
# Verificar se porta 8000 está livre
netstat -ano | findstr :8000

# Matar processo se necessário
taskkill /PID <PID> /F

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Admin Panel não carrega

```bash
# Limpar cache e reinstalar
cd chatlove-admin
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Extension não aparece

1. Verificar se backend está rodando (porta 8000)
2. Recarregar extension em `chrome://extensions/`
3. Verificar console do navegador (F12)
4. Verificar se está em projeto do Lovable

### Licença inválida

1. Verificar se backend está rodando
2. Verificar se licença está ativa no admin panel
3. Verificar se chave foi copiada corretamente

---

## 📈 Monitoramento

### Logs do Backend

```bash
# Backend mostra logs no terminal
[INFO] Request received
[INFO] License validated
[INFO] Credits logged
```

### Logs da Extension

```bash
# Abrir console do navegador (F12)
[ChatLove Proxy] Cookie capturado
[ChatLove Proxy] Projeto detectado
[ChatLove Proxy] Mensagem enviada
```

---

## 🔒 Segurança

### Alterar Senha Admin

```python
# No admin panel ou via API
PUT /api/admin/change-password
{
  "old_password": "admin123",
  "new_password": "sua_senha_forte"
}
```

### Backup do Banco

```bash
# Copiar arquivo SQLite
cp chatlove-backend/chatlove.db chatlove-backend/chatlove.db.backup
```

---

## 🚀 Deploy em Produção

### Backend

```bash
# Usar Gunicorn
pip install gunicorn
gunicorn main:app --bind 0.0.0.0:8000 --workers 4
```

### Admin Panel

```bash
# Build de produção
cd chatlove-admin
npm run build

# Servir com nginx ou PM2
pm2 serve dist 3000 --name chatlove-admin
```

### Extension

1. Zipar pasta `chatlove-proxy-extension/`
2. Publicar na Chrome Web Store
3. Ou distribuir .zip para usuários

---

## 📞 Suporte

- **Documentação:** Ver arquivos .md no projeto
- **Logs:** Verificar terminal do backend
- **Console:** F12 no navegador para extension

---

## ✅ Checklist de Inicialização

- [ ] Backend rodando (porta 8000)
- [ ] Admin panel rodando (porta 3000)
- [ ] Extension carregada no Chrome
- [ ] Licença criada no admin
- [ ] Licença ativada na extension
- [ ] Teste de envio de mensagem
- [ ] Créditos sendo contabilizados

---

**Sistema pronto para uso! 🎉**
