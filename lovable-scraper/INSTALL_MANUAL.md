# 🔧 INSTALAÇÃO MANUAL - Lovable Scraper

## ⚠️ Problema Detectado

O npm está tentando criar diretórios em `c:\` (raiz) devido a uma configuração incorreta.

## ✅ SOLUÇÃO - Execute estes comandos manualmente

### **Opção 1: PowerShell como Administrador (RECOMENDADO)**

1. **Abra PowerShell como Administrador**
   - Pressione `Win + X`
   - Selecione "Windows PowerShell (Admin)" ou "Terminal (Admin)"

2. **Execute os comandos:**

```powershell
# Navegar para o diretório
cd "c:\projetos\lovable-assistant\lovable-scraper"

# Limpar cache do npm
npm cache clean --force

# Instalar dependências
npm install
```

---

### **Opção 2: Corrigir configuração do npm**

Se a Opção 1 não funcionar, execute:

```powershell
# Verificar configuração atual
npm config list

# Corrigir prefix (se necessário)
npm config delete prefix
npm config set prefix "%APPDATA%\npm"

# Tentar instalar novamente
cd "c:\projetos\lovable-assistant\lovable-scraper"
npm install
```

---

### **Opção 3: Usar yarn (alternativa)**

Se o npm continuar com problemas:

```powershell
# Instalar yarn globalmente (se não tiver)
npm install -g yarn

# Usar yarn para instalar
cd "c:\projetos\lovable-assistant\lovable-scraper"
yarn install
```

---

## 🎯 Após Instalação Bem-Sucedida

Você verá algo como:

```
added 2 packages, and audited 3 packages in 45s

found 0 vulnerabilities
```

Então pode executar:

```powershell
# Executar scraper
npm run scrape

# OU
node lovable-scraper.js
```

---

## 🐛 Troubleshooting Adicional

### Erro de Permissão Persistente

1. **Desabilitar antivírus temporariamente**
2. **Executar como Administrador**
3. **Verificar se algum processo está usando a pasta:**

```powershell
# Verificar processos
Get-Process | Where-Object {$_.Path -like "*lovable-scraper*"}
```

### Erro "Cannot find module"

```powershell
# Reinstalar do zero
cd "c:\projetos\lovable-assistant\lovable-scraper"
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item package-lock.json -Force -ErrorAction SilentlyContinue
npm install
```

### Puppeteer não baixa Chromium

```powershell
# Forçar download do Chromium
$env:PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="false"
npm install puppeteer --force
```

---

## ✅ Verificar Instalação

Após instalar, verifique:

```powershell
# Verificar se node_modules existe
Test-Path ".\node_modules"

# Verificar se puppeteer foi instalado
Test-Path ".\node_modules\puppeteer"

# Listar pacotes instalados
npm list --depth=0
```

Deve mostrar:
```
lovable-scraper@1.0.0
├── chalk@4.1.2
└── puppeteer@21.7.0
```

---

## 🚀 Executar Scraper

Quando tudo estiver instalado:

```powershell
# Método 1
npm run scrape

# Método 2
node lovable-scraper.js

# Método 3 (com debug)
node --trace-warnings lovable-scraper.js
```

---

## 📞 Ainda com Problemas?

Se nada funcionar, tente:

1. **Reinstalar Node.js** (versão LTS mais recente)
2. **Usar WSL** (Windows Subsystem for Linux)
3. **Executar em outro diretório** (ex: `C:\temp\lovable-scraper`)

---

**Boa sorte! 🚀**
