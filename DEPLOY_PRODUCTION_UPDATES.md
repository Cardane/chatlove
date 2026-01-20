# 🔧 Atualizações Necessárias para Produção

## 📋 Resumo

Para deploy em produção na Digital Ocean, precisamos atualizar as URLs de desenvolvimento (`127.0.0.1:8000`) para usar o Nginx como reverse proxy. Isso permite:

- ✅ Acesso via porta 80 (HTTP padrão)
- ✅ Backend e Admin no mesmo domínio (sem CORS complexo)
- ✅ Possibilidade futura de HTTPS
- ✅ Arquitetura profissional e escalável

---

## 🎯 Arquitetura de Produção

```
Extension/Admin → http://209.38.79.211/api/* → Nginx → Backend :8000
Admin Panel → http://209.38.79.211/* → Nginx → Arquivos estáticos
```

**Mudanças de URL:**

| Componente | Desenvolvimento | Produção |
|------------|----------------|----------|
| Backend API | `http://127.0.0.1:8000/api/*` | `http://209.38.79.211/api/*` |
| Admin Panel | `http://127.0.0.1:3000` | `http://209.38.79.211` |
| Health Check | `http://127.0.0.1:8000/health` | `http://209.38.79.211/health` |

---

## 📝 Arquivos que Precisam ser Atualizados

### 1. **Backend: `chatlove-backend/main.py`**

**Mudança:** Atualizar CORS para aceitar requisições do IP da VPS

```python
# ANTES (desenvolvimento)
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://209.38.79.211:3000",  # ← Remover porta
    "http://209.38.79.211:8000",  # ← Remover porta
    "https://lovable.dev"
],

# DEPOIS (produção)
allow_origins=[
    "http://localhost:3000",           # Dev local
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://209.38.79.211",            # ← Produção (sem porta)
    "https://lovable.dev"              # Extension
],
```

**Motivo:** Nginx vai servir tudo na porta 80, então não precisamos especificar portas.

---

### 2. **Admin Panel: `chatlove-admin/src/api.js`**

**Mudança:** Criar variável de ambiente para URL da API

```javascript
// ANTES
const API_URL = 'http://127.0.0.1:8000'

// DEPOIS
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
```

**Criar arquivo `.env.production`:**
```env
VITE_API_URL=http://209.38.79.211
```

**Motivo:** Permite build de produção com URL correta, mantendo desenvolvimento local funcionando.

---

### 3. **Extension: `chatlove-proxy-extension/content.js`**

**Mudança:** Atualizar URLs do proxy

```javascript
// ANTES
const PROXY_URL = 'http://127.0.0.1:8000/api/master-proxy';

// DEPOIS
const PROXY_URL = 'http://209.38.79.211/api/master-proxy';
```

**E também:**
```javascript
// Linha ~500 (loadStats)
const response = await fetch(
  `http://209.38.79.211/api/credits/total/${licenseKey}`  // ← Atualizar
);

// Linha ~600 (checkLicenseStatus)
const response = await fetch('http://209.38.79.211/api/validate-license', {
  // ← Atualizar
```

**Motivo:** Extension precisa acessar o backend via IP público da VPS.

---

### 4. **Extension: `chatlove-proxy-extension/popup.js`**

**Mudança:** Atualizar URL de validação

```javascript
// Procurar por fetch com validate-license e atualizar
const response = await fetch('http://209.38.79.211/api/validate-license', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ license_key: licenseKey })
});
```

---

## 🔄 Estratégia de Deploy Híbrido

Para facilitar desenvolvimento E produção, vamos criar **dois ambientes**:

### **Opção 1: Variáveis de Ambiente (Recomendado)**

**Backend (`main.py`):**
```python
import os

# Detectar ambiente
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"

# CORS dinâmico
if IS_PRODUCTION:
    allow_origins = [
        "http://209.38.79.211",
        "https://lovable.dev"
    ]
else:
    allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://lovable.dev"
    ]
```

**Systemd Service:**
```ini
[Service]
Environment="ENVIRONMENT=production"
Environment="PATH=/var/www/chatlove/backend/venv/bin"
ExecStart=/var/www/chatlove/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

---

### **Opção 2: Branches Git (Alternativa)**

```bash
# Branch main = desenvolvimento
git checkout main

# Branch production = produção
git checkout -b production
# Fazer mudanças de URL
git commit -m "Production URLs"

# Deploy
git push production
```

---

## 🚀 Plano de Ação Recomendado

### **Fase 1: Preparar Código**

1. ✅ Criar branch `production`
2. ✅ Atualizar URLs no backend (CORS)
3. ✅ Criar `.env.production` no admin
4. ✅ Atualizar URLs na extension
5. ✅ Testar localmente (se possível)
6. ✅ Commit e push

### **Fase 2: Deploy no Servidor**

1. ✅ Conectar na VPS
2. ✅ Clonar repositório (branch production)
3. ✅ Configurar backend (venv, dependências, migração)
4. ✅ Criar serviço systemd
5. ✅ Build admin panel com env de produção
6. ✅ Configurar Nginx
7. ✅ Testar endpoints

### **Fase 3: Validação**

1. ✅ Testar backend: `curl http://209.38.79.211/health`
2. ✅ Testar admin: abrir `http://209.38.79.211`
3. ✅ Carregar extension com URLs atualizadas
4. ✅ Testar fluxo completo

---

## 📦 Configuração Nginx Detalhada

```nginx
server {
    listen 80;
    server_name 209.38.79.211;

    # Logs
    access_log /var/log/nginx/chatlove-access.log;
    error_log /var/log/nginx/chatlove-error.log;

    # Admin Panel (React SPA)
    location / {
        root /var/www/chatlove/admin;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache para assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        
        # Headers importantes
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS (se necessário)
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        # Timeout
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

---

## ⚠️ Checklist Pré-Deploy

- [ ] Backup do código atual
- [ ] Testar URLs localmente (se possível)
- [ ] Verificar se todas as URLs foram atualizadas
- [ ] Confirmar que CORS está correto
- [ ] Preparar rollback (branch main)
- [ ] Documentar mudanças

---

## 🔧 Comandos Úteis

### **Build Admin com Produção**
```powershell
cd chatlove-admin
npm run build  # Vai usar .env.production automaticamente
```

### **Testar Backend Localmente**
```powershell
cd chatlove-backend
.\.venv\Scripts\activate
$env:ENVIRONMENT="production"
python main.py
```

### **Deploy Rápido**
```bash
# No servidor
cd /var/www/chatlove
git pull origin production
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chatlove-backend
sudo systemctl reload nginx
```

---

## 🎯 Próximos Passos

1. **Decidir estratégia:** Variáveis de ambiente OU branch separada?
2. **Fazer mudanças** nos arquivos listados acima
3. **Testar localmente** (opcional mas recomendado)
4. **Fazer deploy** seguindo o DEPLOY_STRATEGY.md
5. **Validar** sistema em produção

---

**Recomendação Final:** Use **variáveis de ambiente** para manter um único código-base e facilitar manutenção futura. 🚀
