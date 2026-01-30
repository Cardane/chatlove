# 🔍 Lovable API Scraper

Script automatizado para capturar, analisar e documentar a API do Lovable.dev usando Puppeteer.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Instalação](#instalação)
- [Uso](#uso)
- [Como Funciona](#como-funciona)
- [Arquivos Gerados](#arquivos-gerados)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este scraper captura automaticamente:

✅ **Requisições HTTP** - Todos os endpoints da API
✅ **Respostas** - Status codes, headers, payloads
✅ **Cookies** - Sessões e autenticação
✅ **Storage** - localStorage e sessionStorage
✅ **Estruturas de Dados** - Payloads e responses

**Abordagem Híbrida:**
- Você navega manualmente (mais natural)
- Script captura tudo automaticamente
- Análise e documentação geradas

---

## 🚀 Instalação

### Pré-requisitos

- Node.js 16+ instalado
- Chrome/Chromium disponível
- Conta no Lovable.dev

### Instalar Dependências

```bash
cd lovable-scraper
npm install
```

Isso instalará:
- `puppeteer` - Automação do navegador
- `chalk` - Cores no console

---

## 📖 Uso

### 1. Executar Scraper

```bash
npm run scrape
```

ou

```bash
node lovable-scraper.js
```

### 2. Seguir Instruções

O script abrirá o Chrome e guiará você através de 4 etapas:

#### **ETAPA 1: Login**
```
⏸️  ETAPA 1: LOGIN
Por favor, faça login manualmente no navegador.
⏸️  Pressione ENTER para continuar...
```

- Faça login no Lovable
- Pressione ENTER

#### **ETAPA 2: Criar Projeto**
```
⏸️  ETAPA 2: CRIAR PROJETO DE TESTE
Por favor, crie um novo projeto de teste.
⏸️  Pressione ENTER para continuar...
```

- Crie um projeto simples
- Pressione ENTER

#### **ETAPA 3: Enviar Mensagens**
```
⏸️  ETAPA 3: ENVIAR MENSAGENS DE TESTE
Por favor, envie algumas mensagens de teste:
  1. "Create a hello world button"
  2. "Change button color to red"
  3. "Add a counter that increments on click"
⏸️  Pressione ENTER para continuar...
```

- Envie as mensagens sugeridas
- Aguarde respostas da IA
- Pressione ENTER

#### **ETAPA 4: Explorar (Opcional)**
```
⏸️  ETAPA 4: EXPLORAR RECURSOS (OPCIONAL)
Explore outros recursos se desejar:
  - Upload de arquivos
  - Configurações do projeto
  - Preview/Deploy
⏸️  Pressione ENTER para continuar...
```

- Explore recursos adicionais
- Pressione ENTER quando terminar

### 3. Analisar Dados Capturados

```bash
npm run analyze
```

ou

```bash
node analyze-capture.js
```

---

## 🔍 Como Funciona

### Captura Automática

```javascript
// O script intercepta TODAS as requisições
page.on('request', request => {
  // Captura URL, método, headers, payload
});

page.on('response', response => {
  // Captura status, headers, body
});
```

### Filtragem Inteligente

Apenas requisições relevantes são capturadas:
- `lovable.dev/*`
- `api.lovable.dev/*`
- `supabase.co/*` (se usado)

### Análise Automática

O analisador:
1. Agrupa requisições por endpoint
2. Identifica padrões de payload
3. Extrai estruturas de dados
4. Detecta autenticação
5. Gera documentação

---

## 📁 Arquivos Gerados

### `captures/capture-TIMESTAMP.json`

Dados brutos capturados:

```json
{
  "requests": [
    {
      "timestamp": "2026-01-21T22:00:00.000Z",
      "url": "https://api.lovable.dev/projects/abc/chat",
      "method": "POST",
      "headers": {...},
      "postData": "{...}"
    }
  ],
  "responses": [...],
  "cookies": [...],
  "localStorage": [...],
  "sessionStorage": [...]
}
```

### `captures/lovable-api-docs.md`

Documentação completa gerada:

```markdown
# 📚 LOVABLE API - DOCUMENTAÇÃO COMPLETA

## 🔐 AUTENTICAÇÃO
**Tipo:** Bearer Token
**Header:** Authorization: Bearer {token}

## 🌐 ENDPOINTS DESCOBERTOS
### `/projects/{id}/chat`
**Métodos:** POST
**Payload:**
{
  "message": "string",
  "id": "umsg_...",
  "mode": "instant"
}
```

### `captures/analysis.json`

Análise estruturada em JSON:

```json
{
  "endpoints": [
    {
      "endpoint": "/projects/{id}/chat",
      "methods": ["POST"],
      "parameters": [],
      "examples": [...]
    }
  ],
  "authentication": {
    "type": "Bearer Token",
    "tokens": [...]
  },
  "payloadStructures": [...],
  "responseStructures": [...]
}
```

---

## 🎯 Saída do Scraper

```
═══════════════════════════════════════════════════════
🔍 LOVABLE API SCRAPER
═══════════════════════════════════════════════════════

📍 Iniciando navegador...
📡 Configurando interceptação de rede...
📍 Acessando Lovable.dev...

═══════════════════════════════════════════════════════
⏸️  ETAPA 1: LOGIN
═══════════════════════════════════════════════════════
Por favor, faça login manualmente no navegador.
⏸️  Pressione ENTER para continuar...

[Você faz login e pressiona ENTER]

✅ Login detectado!
📍 Navegando para lista de projetos...

[... continua ...]

═══════════════════════════════════════════════════════
✅ CAPTURA COMPLETA!
═══════════════════════════════════════════════════════
📊 Estatísticas:
   - Requisições capturadas: 47
   - Respostas capturadas: 45
   - Cookies capturados: 3 snapshots
   - Arquivo salvo: ./captures/capture-2026-01-21T22-00-00-000Z.json

📝 Próximo passo: Execute "npm run analyze" para analisar os dados
```

---

## 🎯 Saída do Analisador

```
═══════════════════════════════════════════════════════
📊 LOVABLE API ANALYZER
═══════════════════════════════════════════════════════

📂 Analisando: ./captures/capture-2026-01-21T22-00-00-000Z.json

📊 Dados carregados:
   - Requisições: 47
   - Respostas: 45
   - Cookies: 3 snapshots

🔍 Analisando dados...

✅ Análise completa!

═══════════════════════════════════════════════════════
📊 RESUMO DA ANÁLISE
═══════════════════════════════════════════════════════

🌐 Endpoints descobertos: 12
📋 Métodos HTTP: GET, POST, PUT, DELETE
🔐 Autenticação: Bearer Token
🍪 Cookies importantes: 2
📦 Estruturas de payload: 8
📥 Estruturas de resposta: 10

🌐 ENDPOINTS:
   POST                 /projects/{id}/chat
   GET                  /projects/{id}
   GET                  /projects
   POST                 /projects
   ...

✅ Documentação salva em: ./captures/lovable-api-docs.md
✅ Análise JSON salva em: ./captures/analysis.json

═══════════════════════════════════════════════════════
✅ ANÁLISE COMPLETA!
═══════════════════════════════════════════════════════

📖 Próximos passos:
   1. Revisar a documentação gerada
   2. Identificar recursos para implementar no ChatLove
   3. Testar endpoints descobertos
```

---

## 🐛 Troubleshooting

### Erro: "Chromium not found"

```bash
# Reinstalar Puppeteer
npm install puppeteer --force
```

### Erro: "Cannot find module"

```bash
# Reinstalar dependências
rm -rf node_modules
npm install
```

### Navegador não abre

Verifique se o Chrome está instalado:

```bash
# Windows
where chrome

# Linux/Mac
which google-chrome
```

### Captura vazia

Certifique-se de:
1. Fazer login corretamente
2. Criar um projeto
3. Enviar mensagens no chat
4. Aguardar respostas da IA

### DevTools não abre automaticamente

Edite `lovable-scraper.js`:

```javascript
const CONFIG = {
  headless: false,
  devtools: true,  // ← Certifique-se que está true
  ...
};
```

---

## 📊 Estrutura de Diretórios

```
lovable-scraper/
├── package.json              # Dependências
├── lovable-scraper.js        # Script principal
├── analyze-capture.js        # Analisador
├── README.md                 # Este arquivo
└── captures/                 # Dados capturados
    ├── .gitignore
    ├── capture-*.json        # Capturas brutas
    ├── lovable-api-docs.md   # Documentação
    └── analysis.json         # Análise estruturada
```

---

## 🎯 Próximos Passos

Após capturar e analisar:

1. **Revisar Documentação**
   - Abrir `captures/lovable-api-docs.md`
   - Identificar endpoints interessantes
   - Anotar parâmetros importantes

2. **Implementar no ChatLove**
   - Adicionar modo PLAN/ACT
   - Implementar recursos descobertos
   - Melhorar payloads

3. **Testar Endpoints**
   - Usar Postman/Insomnia
   - Validar estruturas
   - Documentar comportamentos

---

## 📝 Notas Importantes

⚠️ **Privacidade:**
- Dados capturados contêm tokens de sessão
- NÃO compartilhe arquivos de captura
- `.gitignore` já está configurado

⚠️ **Uso Responsável:**
- Use apenas para fins educacionais
- Respeite os termos de serviço do Lovable
- Não abuse da API

⚠️ **Segurança:**
- Tokens expiram após algum tempo
- Não commite arquivos de captura
- Mantenha credenciais seguras

---

## 🤝 Contribuindo

Melhorias são bem-vindas! Sugestões:

- Captura de WebSocket messages
- Análise de timing/performance
- Detecção de rate limits
- Geração de código de exemplo

---

## 📄 Licença

MIT License - Use livremente para fins educacionais.

---

**Desenvolvido para o projeto ChatLove** 💜
