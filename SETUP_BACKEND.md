# 🚀 Lovable Assistant - Setup do Backend

## Objetivo
Configurar e executar o backend FastAPI do Lovable Assistant em ambiente local.

## Estrutura do Projeto
```
lovable-assistant/
├── backend/
│   ├── main.py             # Aplicação FastAPI principal
│   ├── lovable_client.py   # Cliente HTTP para API do Lovable
│   ├── config.py           # Configurações
│   ├── requirements.txt    # Dependências Python
│   └── .env.example        # Exemplo de variáveis de ambiente
└── extension/              # Extensão Chrome (não precisa configurar aqui)
```

## Tarefas para Executar

### 1. Navegar até o diretório do backend
```bash
cd backend
```

### 2. Criar ambiente virtual Python
```bash
python -m venv venv
```

### 3. Ativar ambiente virtual
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependências
```bash
pip install -r requirements.txt
```

### 5. Criar arquivo .env (opcional)
```bash
cp .env.example .env
```

### 6. Iniciar o servidor
```bash
python main.py
```

## Resultado Esperado

O servidor deve iniciar e exibir:
```
╔══════════════════════════════════════════════════════════════╗
║                   LOVABLE ASSISTANT API                      ║
╠══════════════════════════════════════════════════════════════╣
║  Server: http://127.0.0.1:8000                              ║
║  Docs:   http://127.0.0.1:8000/docs                         ║
║  Health: http://127.0.0.1:8000/api/health                   ║
╚══════════════════════════════════════════════════════════════╝
```

## Verificar se está funcionando

Testar o health check:
```bash
curl http://localhost:8000/api/health
```

Resposta esperada:
```json
{"status":"ok","timestamp":1234567890}
```

## Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/health` | GET | Verifica se o servidor está online |
| `/api/send` | POST | Envia mensagem para o Lovable |
| `/api/upload` | POST | Faz upload de arquivo |
| `/api/projects` | GET | Lista projetos do usuário |
| `/docs` | GET | Documentação Swagger interativa |

## Dependências (requirements.txt)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
python-multipart==0.0.6
python-dotenv==1.0.0
```

## Configurações Padrão (config.py)

- **Host:** 127.0.0.1
- **Port:** 8000
- **Debug:** true (hot-reload ativado)

## Troubleshooting

### Porta 8000 já em uso
Altere a porta no `.env`:
```
PORT=8001
```

### Erro de importação de módulos
Certifique-se de que o ambiente virtual está ativado:
```bash
which python  # Deve apontar para venv/bin/python
```

### Erro de CORS
O backend já está configurado para aceitar requisições de qualquer origem em localhost.

## Comando Único (Copy & Paste)

**Windows (PowerShell):**
```powershell
cd backend; python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt; python main.py
```

**Linux/Mac:**
```bash
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python main.py
```
