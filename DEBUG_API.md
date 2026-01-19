# Debug - API Lovable.dev

## Problema
A extensão está retornando "Erro ao enviar: 404 page not found" mesmo com projeto real e usuário logado.

## Informações do Projeto
- **Project ID**: 9257217a...
- **Status Backend**: Online
- **Status Requisição**: 200 OK (backend responde corretamente)
- **Erro**: Vem da API do Lovable.dev, não do nosso backend

## Endpoints Testados
1. `/projects/{project_id}/messages` - 404
2. `/chat/{project_id}/message` - 404
3. `/v1/projects/{project_id}/messages` - 404

## Possíveis Causas

### 1. Token de Sessão Inválido
- O cookie `lovable-session-id.id` pode estar expirado
- Solução: Fazer logout e login novamente no Lovable.dev

### 2. Formato do Project ID
- O ID pode precisar ser completo, não truncado
- Verificar se é UUID completo

### 3. API Mudou
- A API do Lovable.dev pode ter mudado recentemente
- Precisamos descobrir o endpoint correto atual

### 4. Headers Incorretos
- Pode precisar de headers adicionais
- Cookie pode precisar ser enviado de forma diferente

## Próximos Passos para Debug

### Opção 1: Inspecionar Requisições Reais
1. Abrir DevTools no Lovable.dev (F12)
2. Ir para aba Network
3. Enviar uma mensagem pelo chat normal
4. Procurar pela requisição POST
5. Copiar:
   - URL exata
   - Headers
   - Payload

### Opção 2: Verificar Documentação
- Procurar se há documentação pública da API
- Verificar se há mudanças recentes

### Opção 3: Usar Cookie Diretamente
Em vez de Bearer token, pode precisar enviar o cookie:
```python
headers = {
    "Cookie": f"lovable-session-id.id={self.session_token}",
    ...
}
```

## Como Testar

### 1. Verificar Token
Abra o console do navegador no Lovable.dev:
```javascript
document.cookie
```

### 2. Testar Manualmente
```bash
curl -X POST https://api.lovable.dev/projects/SEU_PROJECT_ID/messages \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"test","messageId":"test123"}'
```

### 3. Verificar Logs do Backend
O backend está logando as requisições. Verificar se:
- O project_id está correto
- O session_token está sendo enviado
- A resposta da API Lovable

## Solução Temporária
Se a API mudou e não conseguimos descobrir o endpoint, podemos:
1. Usar a interface web do Lovable diretamente
2. Aguardar documentação oficial
3. Fazer engenharia reversa das requisições do site
