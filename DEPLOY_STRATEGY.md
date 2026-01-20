# 🎯 Estratégia de Deploy - ChatLove na Digital Ocean

## 📊 Recomendação: **Linux Puro com Systemd**

### ✅ Por que NÃO usar Docker neste caso?

**Contexto do Projeto:**
- Sistema único rodando na VPS
- Stack simples: FastAPI + React (estático) + SQLite
- Sem necessidade de múltiplos ambientes isolados
- Prioridade: facilidade de manutenção

**Desvantagens do Docker aqui:**
- ❌ Overhead desnecessário (camada extra de complexidade)
- ❌ Mais recursos consumidos (memória/CPU)
- ❌ Mais pontos de falha (Docker daemon, networks, volumes)
- ❌ Debugging mais complexo
- ❌ Atualizações mais trabalhosas (rebuild de imagens)

### ✅ Vantagens do Linux Puro + Systemd

**Simplicidade:**
- ✅ Deploy direto via Git pull ou SCP
- ✅ Restart rápido: `systemctl restart chatlove-backend`
- ✅ Logs centralizados: `journalctl -u chatlove-backend`
- ✅ Menos camadas = menos problemas

**Performance:**
- ✅ Sem overhead de containers
- ✅ Acesso direto ao sistema de arquivos
- ✅ Menos consumo de memória

**Manutenção:**
- ✅ Atualização simples: `git pull && systemctl restart`
- ✅ Backup direto do banco SQLite
- ✅ Debugging direto (sem entrar em containers)

---

## 🏗️ Arquitetura Recomendada

```
Digital Ocean Droplet (Ubuntu 22.04 LTS)
├── Nginx (Reverse Proxy + Servir Admin)
│   ├── :80 → Admin Panel (React build)
│   └── :80/api → Backend (FastAPI)
├── Systemd Service (Backend)
│   └── FastAPI rodando em :8000
└── SQLite Database
    └── /var/www/chatlove/backend/chatlove.db
```

### 🔄 Fluxo de Requisições

```
Extension → Nginx :80/api → FastAPI :8000 → SQLite
Admin Panel → Nginx :80 → Arquivos estáticos
```

---

## 🚀 Plano de Deploy Otimizado

### **1. Preparar Droplet na Digital Ocean**

**Especificações Mínimas:**
- **Plano:** Basic Droplet $6/mês (1GB RAM, 1 vCPU)
- **OS:** Ubuntu 22.04 LTS
- **Região:** São Paulo (melhor latência para Brasil)
- **SSH:** Adicionar sua chave pública

### **2. Configuração Inicial do Servidor**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-pip python3-venv nginx git ufw

# Configurar firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### **3. Configurar Git para Deploy Automático**

**Opção A: Git Pull (Recomendado)**
```bash
# No servidor
cd /var/www
sudo git clone https://github.com/Cardane/chatlove.git chatlove
sudo chown -R alan:alan /var/www/chatlove

# Para atualizar
cd /var/www/chatlove
git pull
sudo systemctl restart chatlove-backend
```

**Opção B: Git Hooks (Deploy Automático)**
```bash
# Criar repositório bare no servidor
mkdir -p /var/repos/chatlove.git
cd /var/repos/chatlove.git
git init --bare

# Criar hook post-receive
nano hooks/post-receive
```

**Hook Content:**
```bash
#!/bin/bash
GIT_WORK_TREE=/var/www/chatlove git checkout -f
cd /var/www/chatlove/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chatlove-backend
```

```bash
chmod +x hooks/post-receive
```

**No local (Windows):**
```powershell
git remote add production alan@209.38.79.211:/var/repos/chatlove.git
git push production main  # Deploy automático!
```

### **4. Setup Backend**

```bash
cd /var/www/chatlove/backend

# Criar venv
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Migrar banco
python migrate_db.py

# Criar .env (se necessário)
nano .env
```

**Systemd Service:**
```bash
sudo nano /etc/systemd/system/chatlove-backend.service
```

```ini
[Unit]
Description=ChatLove Backend API
After=network.target

[Service]
Type=simple
User=alan
WorkingDirectory=/var/www/chatlove/backend
Environment="PATH=/var/www/chatlove/backend/venv/bin"
ExecStart=/var/www/chatlove/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable chatlove-backend
sudo systemctl start chatlove-backend
```

### **5. Setup Admin Panel**

**Build local:**
```powershell
cd chatlove-admin
npm run build
```

**Enviar para servidor:**
```powershell
scp -i "C:\Users\Alan Cardane\.ssh\id_ed25519" -r dist/* alan@209.38.79.211:/var/www/chatlove/admin/
```

### **6. Configurar Nginx**

```bash
sudo nano /etc/nginx/sites-available/chatlove
```

```nginx
server {
    listen 80;
    server_name 209.38.79.211;

    # Admin Panel
    location / {
        root /var/www/chatlove/admin;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/chatlove /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remover site padrão
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔄 Workflow de Atualização

### **Método 1: Git Pull Manual**
```bash
ssh alan@209.38.79.211
cd /var/www/chatlove
git pull
sudo systemctl restart chatlove-backend
```

### **Método 2: Script de Deploy**
```bash
# Criar script
nano /home/alan/deploy.sh
```

```bash
#!/bin/bash
cd /var/www/chatlove
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
python migrate_db.py
sudo systemctl restart chatlove-backend
echo "✅ Deploy concluído!"
```

```bash
chmod +x /home/alan/deploy.sh

# Usar
./deploy.sh
```

### **Método 3: Git Hook Automático** (já configurado acima)
```powershell
# No Windows
git push production main
# Deploy automático!
```

---

## 📊 Monitoramento Simplificado

### **Ver status**
```bash
sudo systemctl status chatlove-backend
```

### **Ver logs em tempo real**
```bash
sudo journalctl -u chatlove-backend -f
```

### **Ver últimos erros**
```bash
sudo journalctl -u chatlove-backend -n 50 --no-pager
```

### **Verificar uso de recursos**
```bash
htop  # ou top
```

---

## 🔒 Segurança Básica

### **1. Firewall**
```bash
sudo ufw status
# Deve mostrar apenas: 22 (SSH), 80 (HTTP), 443 (HTTPS se configurar)
```

### **2. Fail2Ban (Proteção SSH)**
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

### **3. Atualizações Automáticas**
```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🎯 Checklist de Deploy

- [ ] Criar Droplet na Digital Ocean
- [ ] Configurar SSH com chave
- [ ] Instalar dependências (Python, Nginx, Git)
- [ ] Configurar firewall (UFW)
- [ ] Clonar repositório
- [ ] Configurar backend (venv, dependências, migração)
- [ ] Criar serviço systemd
- [ ] Build e enviar admin panel
- [ ] Configurar Nginx
- [ ] Testar backend: `curl http://209.38.79.211/health`
- [ ] Testar admin: abrir `http://209.38.79.211`
- [ ] Testar extension
- [ ] Configurar backup do banco SQLite
- [ ] Documentar processo

---

## 🆚 Comparação Final

| Aspecto | Linux Puro | Docker |
|---------|-----------|--------|
| **Complexidade** | ⭐⭐ Baixa | ⭐⭐⭐⭐ Alta |
| **Performance** | ⭐⭐⭐⭐⭐ Máxima | ⭐⭐⭐ Boa |
| **Manutenção** | ⭐⭐⭐⭐⭐ Simples | ⭐⭐⭐ Média |
| **Deploy** | ⭐⭐⭐⭐⭐ Git pull | ⭐⭐⭐ Build + Push |
| **Debugging** | ⭐⭐⭐⭐⭐ Direto | ⭐⭐⭐ Via container |
| **Recursos** | ⭐⭐⭐⭐⭐ Mínimos | ⭐⭐⭐ Moderados |

---

## 🎉 Conclusão

**Para este projeto específico, Linux puro com Systemd é a melhor escolha:**

✅ Mais simples de configurar e manter
✅ Melhor performance
✅ Menos pontos de falha
✅ Deploy e atualização triviais
✅ Debugging direto
✅ Menor consumo de recursos

**Docker seria útil se:**
- Tivéssemos múltiplos serviços complexos
- Precisássemos de ambientes isolados
- Escalabilidade horizontal fosse necessária
- Múltiplos desenvolvedores com ambientes diferentes

**Mas não é o caso aqui! 🎯**
