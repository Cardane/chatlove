# 🚀 Guia de Deploy - ChatLove VPS

## 📋 Informações da VPS

- **IP:** 209.38.79.211
- **Usuário:** alan
- **Chave SSH:** `C:\Users\Alan Cardane\.ssh\id_ed25519`
- **Diretório:** `/var/www/chatlove`

---

## 🔧 Mudanças Implementadas

### ✅ Extension (Pronta para Deploy)

**Arquivos Modificados:**
- `content.js` - URLs atualizadas para VPS
- `popup.js` - URL de validação atualizada

**URLs Atualizadas:**
```javascript
// Antes
http://127.0.0.1:8000

// Depois
http://209.38.79.211:8000
```

### ✅ Backend (Pronto para Deploy)

**Arquivo Modificado:**
- `main.py` - CORS atualizado

**CORS Configurado:**
```python
allow_origins=[
    "http://localhost:3000",           # Dev local
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://209.38.79.211:3000",       # VPS Admin
    "http://209.38.79.211:8000",       # VPS Backend
    "https://lovable.dev"              # Extension
],
allow_methods=["GET", "POST", "PUT", "DELETE"],
allow_headers=["Content-Type", "Authorization"],
```

---

## 📁 Estrutura de Pastas na VPS

```
/var/www/chatlove/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── auth.py
│   ├── migrate_db.py
│   ├── chatlove.db
│   ├── requirements.txt
│   └── .env (criar)
├── admin/
│   ├── dist/
│   │   ├── index.html
│   │   ├── assets/
│   │   └── ...
└── extension/
    └── chatlove-proxy-extension/
        ├── manifest.json
        ├── content.js
        ├── popup.js
        ├── background.js
        ├── popup.html
        └── icons/
```

---

## 🚀 Passo a Passo do Deploy

### **1. Conectar na VPS**

```powershell
ssh -i "C:\Users\Alan Cardane\.ssh\id_ed25519" alan@209.38.79.211
```

### **2. Criar Estrutura de Diretórios**

```bash
sudo mkdir -p /var/www/chatlove/{backend,admin,extension}
sudo chown -R alan:alan /var/www/chatlove
```

### **3. Deploy Backend**

#### **3.1. Enviar Arquivos**

```powershell
# No Windows (PowerShell)
scp -i "C:\Users\Alan Cardane\.ssh\id_ed25519" -r chatlove-backend/* alan@209.38.79.211:/var/www/chatlove/backend/
```

#### **3.2. Instalar Dependências**

```bash
# Na VPS
cd /var/www/chatlove/backend

# Criar venv
python3 -m venv venv
source venv/bin/activate

# Instalar
pip install -r requirements.txt
```

#### **3.3. Migrar Banco de Dados**

```bash
# Executar migração
python migrate_db.py
```

#### **3.4. Criar Serviço Systemd**

```bash
sudo nano /etc/systemd/system/chatlove-backend.service
```

**Conteúdo:**
```ini
[Unit]
Description=ChatLove Backend API
After=network.target

[Service]
Type=simple
User=alan
WorkingDirectory=/var/www/chatlove/backend
Environment="PATH=/var/www/chatlove/backend/venv/bin"
ExecStart=/var/www/chatlove/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Ativar:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable chatlove-backend
sudo systemctl start chatlove-backend
sudo systemctl status chatlove-backend
```

### **4. Deploy Admin Panel**

#### **4.1. Build Local**

```powershell
# No Windows
cd chatlove-admin
npm run build
```

#### **4.2. Enviar para VPS**

```powershell
scp -i "C:\Users\Alan Cardane\.ssh\id_ed25519" -r dist/* alan@209.38.79.211:/var/www/chatlove/admin/
```

#### **4.3. Configurar Nginx**

```bash
# Na VPS
sudo nano /etc/nginx/sites-available/chatlove-admin
```

**Conteúdo:**
```nginx
server {
    listen 3000;
    server_name 209.38.79.211;

    root /var/www/chatlove/admin;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Ativar:**
```bash
sudo ln -s /etc/nginx/sites-available/chatlove-admin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### **5. Configurar Firewall**

```bash
sudo ufw allow 8000/tcp  # Backend
sudo ufw allow 3000/tcp  # Admin
sudo ufw reload
```

---

## ✅ Testar Sistema

### **1. Testar Backend**

```bash
curl http://209.38.79.211:8000/health
# Deve retornar: {"status":"healthy"}
```

### **2. Testar Admin Panel**

```
Abrir: http://209.38.79.211:3000
Login: admin / admin123
```

### **3. Testar Extension**

```
1. Carregar extension no Chrome
2. Abrir Lovable.dev
3. Ativar licença
4. Enviar mensagem
5. Verificar se funciona
```

---

## 📊 Monitoramento

### **Ver Logs Backend**

```bash
sudo journalctl -u chatlove-backend -f
```

### **Ver Logs Nginx**

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Status dos Serviços**

```bash
sudo systemctl status chatlove-backend
sudo systemctl status nginx
```

---

## 🔄 Atualizar Sistema

### **Atualizar Backend**

```bash
cd /var/www/chatlove/backend
source venv/bin/activate
git pull  # ou scp novos arquivos
sudo systemctl restart chatlove-backend
```

### **Atualizar Admin**

```bash
# Build local + enviar
npm run build
scp -r dist/* alan@209.38.79.211:/var/www/chatlove/admin/
```

### **Atualizar Extension**

```
1. Modificar arquivos localmente
2. Recarregar extension no Chrome
3. Testar
4. Distribuir nova versão
```

---

## ⚠️ Troubleshooting

### **Backend não inicia**

```bash
# Ver erro
sudo journalctl -u chatlove-backend -n 50

# Testar manualmente
cd /var/www/chatlove/backend
source venv/bin/activate
python main.py
```

### **Admin não carrega**

```bash
# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Ver logs
sudo tail -f /var/log/nginx/error.log
```

### **Extension não conecta**

```
1. Verificar se backend está rodando
2. Verificar firewall (porta 8000)
3. Verificar CORS no backend
4. Ver console do Chrome (F12)
```

---

## 🔒 Segurança

### **Implementado:**
- ✅ CORS restrito
- ✅ URLs específicas (sem wildcard)
- ✅ Métodos HTTP limitados
- ✅ Headers específicos

### **Próximos Passos (Opcional):**
- [ ] HTTPS com Let's Encrypt
- [ ] Rate Limiting
- [ ] Firewall mais restritivo
- [ ] Backup automático do banco

---

## 📝 Checklist Final

- [ ] Backend rodando na VPS
- [ ] Admin Panel acessível
- [ ] Extension conectando
- [ ] Licenças funcionando
- [ ] Mensagens sendo enviadas
- [ ] Créditos sendo contabilizados
- [ ] Logs sem erros

---

**Sistema pronto para produção! 🎉**
