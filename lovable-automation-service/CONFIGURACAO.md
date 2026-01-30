# 🔧 Configuração do Sistema de Automação Lovable

## 📍 **Localização do Arquivo .env**

O arquivo de configuração `.env` está localizado em:
```
lovable-automation-service/.env
```

## 🔑 **Como Configurar suas Credenciais Lovable**

### **1. Abra o arquivo `.env`**
```bash
# Navegue até a pasta
cd lovable-automation-service

# Abra o arquivo .env no seu editor
notepad .env
# ou
code .env
```

### **2. Configure suas credenciais do Lovable.dev**

**Formato para UMA conta:**
```bash
LOVABLE_ACCOUNTS=[{"email":"seu-email@exemplo.com","password":"sua-senha"}]
```

**Exemplo real:**
```bash
LOVABLE_ACCOUNTS=[{"email":"joao@gmail.com","password":"minhasenha123"}]
```

**Formato para MÚLTIPLAS contas:**
```bash
LOVABLE_ACCOUNTS=[{"email":"conta1@gmail.com","password":"senha1"},{"email":"conta2@outlook.com","password":"senha2"}]
```

### **3. Exemplo Completo do arquivo .env**

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/chatlove
REDIS_URL=redis://localhost:6379/0

# Lovable Accounts - SUBSTITUA PELOS SEUS DADOS
LOVABLE_ACCOUNTS=[{"email":"seu-email@lovable.com","password":"sua-senha-aqui"}]

# Security
ENCRYPTION_KEY=dev-32-byte-encryption-key-here
JWT_SECRET=dev-jwt-secret-key-here

# Rate Limiting
MAX_MESSAGES_PER_MINUTE=10
MAX_CONCURRENT_SESSIONS=3

# Browser Settings
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30

# Monitoring
LOG_LEVEL=INFO

# API Settings
API_HOST=0.0.0.0
API_PORT=8001

# Lovable API
LOVABLE_API_URL=https://api.lovable.dev
LOVABLE_WEB_URL=https://lovable.dev
```

## ⚠️ **IMPORTANTE - Formato JSON**

O campo `LOVABLE_ACCOUNTS` deve estar em formato JSON válido:

### ✅ **CORRETO:**
```bash
LOVABLE_ACCOUNTS=[{"email":"user@example.com","password":"password123"}]
```

### ❌ **INCORRETO:**
```bash
# Sem aspas
LOVABLE_ACCOUNTS=[{email:user@example.com,password:password123}]

# Aspas simples (deve ser aspas duplas)
LOVABLE_ACCOUNTS=[{'email':'user@example.com','password':'password123'}]

# Sem colchetes
LOVABLE_ACCOUNTS={"email":"user@example.com","password":"password123"}
```

## 🚀 **Como Testar a Configuração**

### **1. Pare o sistema atual (se estiver rodando):**
```bash
# Pressione Ctrl+C no terminal onde o sistema está rodando
```

### **2. Reinicie o sistema:**
```bash
cd lovable-automation-service
python main.py
```

### **3. Verifique os logs:**
Se configurado corretamente, você verá:
```
{"accounts_count": 1, "max_sessions": 3, "event": "Session manager started"}
```

Se houver erro, você verá:
```
{"event": "No Lovable accounts configured", "logger": "LovableSessionManager", "level": "warning"}
```

### **4. Teste uma mensagem:**
```bash
curl -X POST http://localhost:8001/process-message \
  -H "Content-Type: application/json" \
  -d '{"id":"test-123","user_id":"test-user","project_id":"test-project","content":"Create a hello world component"}'
```

## 🔐 **Segurança**

- **NUNCA** compartilhe suas credenciais do Lovable
- **NUNCA** faça commit do arquivo `.env` no Git
- O arquivo `.env` já está no `.gitignore` para sua proteção
- Use senhas fortes para suas contas Lovable

## 🆘 **Solução de Problemas**

### **Erro: "No Lovable accounts configured"**
- Verifique se o arquivo `.env` existe na pasta `lovable-automation-service/`
- Verifique se `LOVABLE_ACCOUNTS` está configurado corretamente
- Verifique o formato JSON (aspas duplas, colchetes, vírgulas)

### **Erro: "Invalid JSON format for lovable_accounts"**
- Verifique se está usando aspas duplas (`"`) e não simples (`'`)
- Verifique se há vírgulas entre múltiplas contas
- Use um validador JSON online para verificar o formato

### **Erro: "Authentication failed"**
- Verifique se email e senha estão corretos
- Teste fazendo login manual no https://lovable.dev
- Verifique se a conta não tem 2FA ativado

## 📞 **Suporte**

Se ainda tiver problemas:
1. Verifique os logs do sistema
2. Teste suas credenciais no site do Lovable
3. Verifique se o formato JSON está correto
4. Reinicie o sistema após fazer alterações
