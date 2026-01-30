# 🚀 Stream Analyzer - Guia de Uso

## 📋 Visão Geral

O **Stream Analyzer** é uma ferramenta otimizada para processar arquivos grandes de captura (como o de 94MB) sem sobrecarregar a memória ou ultrapassar limites de tokens da IA.

## ✨ Características

- ✅ Processa arquivos de qualquer tamanho
- ✅ Gera múltiplos arquivos pequenos e organizados
- ✅ Análise em apenas ~2-3 segundos
- ✅ Arquivos prontos para análise pela IA
- ✅ Relatório completo em Markdown

## 🎯 Resultado da Análise

Do arquivo de **94MB** com **853 requisições** e **835 respostas**, o Stream Analyzer gerou:

- **343 endpoints únicos** descobertos
- **1 arquivo de payload** (estruturas de requisição)
- **347 arquivos de response** (respostas organizadas)
- **Tempo de processamento:** 2.45 segundos

## 📁 Estrutura de Saída

```
lovable-scraper/captures/streaming-analysis/
├── summary.json              # Visão geral com estatísticas
├── endpoints-list.json       # Lista completa de endpoints
├── authentication.json       # Tokens, cookies, headers de auth
├── report.md                 # Relatório completo em Markdown
├── payloads/
│   └── POST-endpoint.json   # Exemplos de payloads por endpoint
└── responses/
    ├── endpoint-200.json    # Responses organizadas por endpoint + status
    ├── endpoint-201.json
    └── ...                  # 347 arquivos no total
```

## 🚀 Como Usar

### 1. Executar Análise Completa

```bash
# Opção 1: Via npm
npm run stream-analyze

# Opção 2: Diretamente com Node
node stream-analyzer.js
```

### 2. Análise Seletiva

```bash
# Apenas requisições/payloads
node stream-analyzer.js --only=payloads

# Apenas respostas
node stream-analyzer.js --only=responses

# Apenas autenticação
node stream-analyzer.js --only=auth
```

### 3. Limitar Exemplos

```bash
# Máximo de 5 exemplos por endpoint (padrão: 3)
node stream-analyzer.js --max-examples=5

# Apenas 1 exemplo por endpoint
node stream-analyzer.js --max-examples=1
```

## 📊 Arquivos Gerados

### 1. `summary.json`

Visão geral com estatísticas e lista de endpoints:

```json
{
  "generatedAt": "2026-01-22T02:37:00.000Z",
  "stats": {
    "totalRequests": 853,
    "totalResponses": 835,
    "processedRequests": 853,
    "processedResponses": 835
  },
  "endpoints": [
    {
      "endpoint": "/api/projects/{uuid}/chat",
      "methods": ["POST"],
      "count": 45,
      "parameters": []
    }
  ]
}
```

**Tamanho:** ~50KB (analisável pela IA)

### 2. `endpoints-list.json`

Lista simplificada apenas com endpoints:

```json
[
  {
    "endpoint": "/api/projects/{uuid}/chat",
    "methods": ["POST"],
    "count": 45,
    "parameters": []
  }
]
```

**Tamanho:** ~30KB (analisável pela IA)

### 3. `authentication.json`

Dados de autenticação extraídos:

```json
{
  "type": "Bearer Token",
  "tokens": [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOi..."
  ],
  "cookies": [
    {
      "name": "sb-access-token",
      "domain": ".lovable.dev",
      "secure": true,
      "httpOnly": true
    }
  ],
  "headers": {
    "authorization": ["Bearer ..."],
    "x-client-git-sha": ["abc123..."]
  }
}
```

**Tamanho:** ~5KB (analisável pela IA)

### 4. `report.md`

Relatório completo em Markdown com:

- Estatísticas gerais
- Guia de autenticação
- Lista de endpoints com métodos e contadores
- Referências aos arquivos de payload/response

**Tamanho:** ~100KB (analisável pela IA)

### 5. `payloads/*.json`

Exemplos de payloads organizados por `MÉTODO-endpoint`:

```json
[
  {
    "timestamp": "2026-01-22T02:08:15.000Z",
    "headers": {
      "authorization": "Bearer ...",
      "content-type": "application/json"
    },
    "payload": {
      "message": "Create a hello world button",
      "id": "umsg_123",
      "mode": "instant"
    }
  }
]
```

**Tamanho:** 1-50KB cada (analisável pela IA)

### 6. `responses/*.json`

Exemplos de responses organizados por `endpoint-STATUS`:

```json
[
  {
    "timestamp": "2026-01-22T02:08:16.000Z",
    "status": 200,
    "headers": {
      "content-type": "application/json"
    },
    "body": {
      "id": "msg_123",
      "content": "...",
      "status": "completed"
    },
    "structure": {
      "id": "string",
      "content": "string",
      "status": "string"
    }
  }
]
```

**Tamanho:** 1-50KB cada (analisável pela IA)

## 🎯 Próximos Passos

### 1. Analisar Arquivos Individualmente

Agora você pode pedir para a IA analisar cada arquivo separadamente:

```
"Analise o arquivo summary.json e me diga quais são os endpoints mais usados"

"Leia o arquivo authentication.json e explique como funciona a autenticação"

"Analise os payloads em payloads/POST-api-projects-uuid-chat.json"

"Revise as responses em responses/api-projects-uuid-chat-200.json"
```

### 2. Identificar Recursos Importantes

Com os arquivos pequenos, você pode:

- Identificar endpoints críticos para o ChatLove
- Entender estruturas de payload necessárias
- Mapear responses esperadas
- Documentar fluxos de autenticação

### 3. Implementar no ChatLove

Use as informações extraídas para:

- Implementar modo PLAN/ACT
- Adicionar novos endpoints
- Melhorar payloads existentes
- Otimizar autenticação

## 📝 Notas Importantes

### Limitações de Tamanho

- **Payloads:** Limitados a 50KB cada
- **Responses:** Limitados a 50KB cada
- **Exemplos:** Máximo de 3 por endpoint (configurável)

### Responses Grandes

Para responses maiores que 50KB, apenas a **estrutura** é salva:

```json
{
  "timestamp": "...",
  "status": 200,
  "structure": {
    "data": {
      "items": ["..."]
    }
  },
  "note": "Body too large - only structure included"
}
```

### Normalização de Endpoints

IDs dinâmicos são substituídos por placeholders:

- UUIDs: `/projects/abc-123-def` → `/projects/{uuid}`
- IDs numéricos: `/users/123` → `/users/{id}`
- Hashes longos: `/files/abc123...` → `/files/{id}`

## 🔧 Troubleshooting

### Erro: "Diretório de capturas não encontrado"

```bash
# Certifique-se de estar no diretório correto
cd lovable-scraper
node stream-analyzer.js
```

### Erro: "Nenhum arquivo de captura encontrado"

```bash
# Execute o scraper primeiro
npm run scrape
```

### Arquivo muito grande

O Stream Analyzer foi projetado para lidar com arquivos grandes. Se ainda assim houver problemas:

```bash
# Reduza o número de exemplos
node stream-analyzer.js --max-examples=1
```

## 🎉 Sucesso!

Você agora tem **349 arquivos pequenos e organizados** prontos para análise pela IA, em vez de um único arquivo de 94MB impossível de processar!

---

**Desenvolvido para o projeto ChatLove** 💜
