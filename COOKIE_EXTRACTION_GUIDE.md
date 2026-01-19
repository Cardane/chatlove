# 🍪 Guia de Extração de Cookies do Lovable.dev

Este guia explica como extrair os cookies de sessão necessários para usar o cliente API aperfeiçoado.

---

## 📋 Cookies Necessários

O cliente precisa de **3 cookies** de sessão:

| Cookie | Descrição |
|--------|-----------|
| `lovable-session-id.id` | Token JWT do Firebase (autenticação principal) |
| `lovable-session-id.refresh` | Token de refresh para renovar sessão |
| `lovable-session-id.sig` | Assinatura de segurança |

---

## 🔧 Método 1: DevTools do Chrome/Edge

### Passo a Passo:

1. **Abra o Lovable.dev e faça login**
   - Acesse: https://lovable.dev
   - Faça login com sua conta

2. **Abra o DevTools**
   - Pressione `F12` ou `Ctrl+Shift+I`
   - Ou clique com botão direito → "Inspecionar"

3. **Vá para a aba Application**
   - No DevTools, clique em "Application" (ou "Aplicativo")
   - No menu lateral esquerdo, expanda "Cookies"
   - Clique em "https://lovable.dev"

4. **Copie os cookies**
   - Procure pelos cookies que começam com `lovable-session-id`
   - Copie os valores de:
     - `lovable-session-id.id`
     - `lovable-session-id.refresh`
     - `lovable-session-id.sig`

### Exemplo Visual:
```
Name                          | Value
------------------------------|----------------------------------
lovable-session-id.id         | eyJhbGciOiJSUzI1NiIsImtpZCI6...
lovable-session-id.refresh    | AMf-vBwHIQfyRzfuZGzZ4TSruWJ...
lovable-session-id.sig        | ygQPX_yRSOmV-QmLwkYnGeRVefq...
```

---

## 🔧 Método 2: Extensão EditThisCookie

### Instalação:
1. Instale a extensão [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
2. Acesse https://lovable.dev e faça login
3. Clique no ícone da extensão
4. Procure pelos cookies `lovable-session-id.*`
5. Copie os valores

---

## 🔧 Método 3: Console do Navegador

### Código JavaScript:

```javascript
// Cole este código no Console do DevTools (F12 → Console)
const cookies = document.cookie.split(';').reduce((acc, cookie) => {
  const [name, value] = cookie.trim().split('=');
  if (name.startsWith('lovable-session-id')) {
    acc[name] = value;
  }
  return acc;
}, {});

console.log(JSON.stringify(cookies, null, 2));
```

### Resultado:
```json
{
  "lovable-session-id.id": "eyJhbGciOiJSUzI1NiIs...",
  "lovable-session-id.refresh": "AMf-vBwHIQfyRzfuZGzZ4T...",
  "lovable-session-id.sig": "ygQPX_yRSOmV-QmLwkYnGeRVefq..."
}
```

---

## 🔧 Método 4: Python Script Automático

### Script para extrair cookies:

```python
"""
Script para extrair cookies do Chrome/Edge automaticamente
Requer: pip install browser-cookie3
"""
import browser_cookie3
import json

def extract_lovable_cookies():
    """Extrai cookies do Lovable.dev do navegador"""
    try:
        # Tenta Chrome primeiro
        cj = browser_cookie3.chrome(domain_name='lovable.dev')
    except:
        try:
            # Tenta Edge
            cj = browser_cookie3.edge(domain_name='lovable.dev')
        except:
            print("❌ Erro: Não foi possível acessar os cookies do navegador")
            return None
    
    cookies = {}
    for cookie in cj:
        if cookie.name.startswith('lovable-session-id'):
            cookies[cookie.name] = cookie.value
    
    return cookies

if __name__ == "__main__":
    cookies = extract_lovable_cookies()
    
    if cookies:
        print("✅ Cookies extraídos com sucesso!\n")
        print(json.dumps(cookies, indent=2))
        
        # Salvar em arquivo
        with open('lovable_cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        print("\n💾 Cookies salvos em: lovable_cookies.json")
    else:
        print("❌ Nenhum cookie encontrado. Faça login no Lovable.dev primeiro.")
```

---

## 📝 Usando os Cookies no Cliente

### Exemplo em Python:

```python
import json
from lovable_client import LovableClient

# Carregar cookies do arquivo
with open('lovable_cookies.json', 'r') as f:
    cookies = json.load(f)

# Ou definir manualmente
cookies = {
    "lovable-session-id.id": "seu_token_aqui",
    "lovable-session-id.refresh": "seu_refresh_token_aqui",
    "lovable-session-id.sig": "sua_assinatura_aqui"
}

# Usar o cliente
async with LovableClient(cookies) as client:
    result = await client.send_message(
        project_id="seu_project_id",
        message="Olá, Lovable!"
    )
    print(result)
```

---

## ⚠️ Segurança

### ⚠️ IMPORTANTE:

1. **Nunca compartilhe seus cookies!**
   - Cookies de sessão dão acesso total à sua conta
   - Trate-os como senhas

2. **Não commite cookies no Git**
   - Adicione `lovable_cookies.json` ao `.gitignore`
   - Use variáveis de ambiente em produção

3. **Cookies expiram**
   - Token JWT expira em ~1 hora
   - Use o `refresh` token para renovar
   - Implemente lógica de refresh automático

4. **Use HTTPS sempre**
   - Cookies são marcados como `Secure`
   - Só funcionam em conexões HTTPS

---

## 🔄 Renovação Automática de Tokens

### Exemplo de implementação:

```python
import time
import jwt

def is_token_expired(token: str) -> bool:
    """Verifica se o token JWT expirou"""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get('exp', 0)
        return time.time() > exp
    except:
        return True

async def refresh_session(client: LovableClient):
    """Renova a sessão usando o refresh token"""
    # TODO: Implementar lógica de refresh
    # Endpoint ainda não mapeado completamente
    pass
```

---

## 🐛 Troubleshooting

### Problema: "Cookies não encontrados"
**Solução:** Certifique-se de estar logado no Lovable.dev no navegador

### Problema: "Token expirado"
**Solução:** Extraia os cookies novamente após fazer login

### Problema: "Acesso negado"
**Solução:** Verifique se copiou todos os 3 cookies corretamente

### Problema: "Browser-cookie3 não funciona"
**Solução:** 
- Feche o navegador antes de executar o script
- Ou use os métodos manuais (DevTools)

---

## 📚 Referências

- [Chrome DevTools - Cookies](https://developer.chrome.com/docs/devtools/storage/cookies/)
- [EditThisCookie Extension](https://www.editthiscookie.com/)
- [browser-cookie3 Documentation](https://github.com/borisbabic/browser_cookie3)

---

## ✅ Checklist

- [ ] Fiz login no Lovable.dev
- [ ] Abri o DevTools (F12)
- [ ] Copiei os 3 cookies necessários
- [ ] Testei os cookies no cliente
- [ ] Adicionei `lovable_cookies.json` ao `.gitignore`
