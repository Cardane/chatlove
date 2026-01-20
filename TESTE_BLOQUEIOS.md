# 🧪 Guia de Testes - Bloqueios de Licença

## 📋 Cenários de Teste

### ✅ Teste 1: Licença Desativada

**Objetivo:** Verificar se licença desativada pelo admin bloqueia o uso

**Passos:**
1. Admin Panel → Licenças
2. Criar nova licença (tipo: Full)
3. Copiar chave da licença
4. Extension → Ativar licença
5. Verificar que funciona (enviar mensagem)
6. Admin Panel → Desativar licença (botão "Desativar")
7. Extension → Tentar enviar mensagem

**Resultado Esperado:**
```
❌ Erro: "Licença desativada pelo administrador. Entre em contato com o suporte."
```

**Status:** ✅ Bloqueio implementado em:
- `/api/validate-license` (popup)
- `/api/master-proxy` (envio de mensagens)

---

### ✅ Teste 2: Licença Trial Expirada

**Objetivo:** Verificar se licença trial expira após 15 minutos

**Passos:**
1. Admin Panel → Licenças → Nova Licença
2. Selecionar "Licença de Teste (15 minutos)"
3. Gerar licença
4. Copiar chave
5. Extension → Ativar licença
6. Enviar 1 mensagem (inicia contagem de 15 min)
7. Admin Panel → Ver contador "14m 59s restantes"
8. Aguardar 15 minutos
9. Extension → Tentar enviar mensagem

**Resultado Esperado:**
```
❌ Erro: "Licença de teste expirada (15 minutos). Adquira uma licença completa para continuar."
```

**Status:** ✅ Bloqueio implementado em:
- `/api/validate-license` (popup)
- `/api/master-proxy` (envio de mensagens)

---

### ✅ Teste 3: Licença Trial Não Ativada

**Objetivo:** Verificar que trial não expira se não for ativada

**Passos:**
1. Admin Panel → Criar licença trial
2. NÃO ativar na extension
3. Aguardar 20 minutos
4. Ativar licença na extension
5. Enviar mensagem

**Resultado Esperado:**
```
✅ Mensagem enviada com sucesso
✅ Contador inicia: "14m 59s restantes"
```

**Status:** ✅ Expiração só inicia após primeira ativação

---

### ✅ Teste 4: Licença Full Nunca Expira

**Objetivo:** Verificar que licença completa não tem expiração

**Passos:**
1. Admin Panel → Criar licença (tipo: Full)
2. Ativar na extension
3. Usar por vários dias
4. Verificar que continua funcionando

**Resultado Esperado:**
```
✅ Funciona indefinidamente
✅ Sem contador de tempo
✅ Badge: "Full" (não "Trial")
```

**Status:** ✅ Licenças full não têm `expires_at`

---

### ✅ Teste 5: Reativar Licença Desativada

**Objetivo:** Verificar que licença pode ser reativada

**Passos:**
1. Admin Panel → Desativar licença
2. Extension → Tentar usar (deve bloquear)
3. Admin Panel → Reativar licença
4. Extension → Recarregar página
5. Tentar enviar mensagem

**Resultado Esperado:**
```
✅ Mensagem enviada com sucesso
✅ Licença volta a funcionar
```

**Status:** ✅ Botão "Ativar/Desativar" no admin

---

## 🔍 Pontos de Validação

### **1. Popup da Extension** (`/api/validate-license`)

**Valida:**
- ✅ Licença existe
- ✅ Licença está ativa (`is_active = True`)
- ✅ Trial não expirou (`expires_at > now`)

**Retorna:**
```json
{
  "success": false,
  "valid": false,
  "message": "Licença desativada pelo administrador"
}
```

---

### **2. Envio de Mensagens** (`/api/master-proxy`)

**Valida:**
- ✅ Licença existe
- ✅ Licença está ativa
- ✅ Trial não expirou

**Retorna:**
```json
{
  "status_code": 403,
  "detail": "Licença de teste expirada (15 minutos). Adquira uma licença completa para continuar."
}
```

---

## 📊 Fluxo de Validação

```
Extension Popup
    ↓
POST /api/validate-license
    ↓
Verifica:
  1. Licença existe?
  2. is_active = True?
  3. Trial expirou?
    ↓
  ✅ Válida → Permite ativar
  ❌ Inválida → Mostra erro
```

```
Extension Sidebar (Enviar Mensagem)
    ↓
POST /api/master-proxy
    ↓
Verifica:
  1. Licença existe?
  2. is_active = True?
  3. Trial expirou?
    ↓
  ✅ Válida → Envia para Lovable
  ❌ Inválida → Retorna erro 403
```

---

## 🧪 Como Testar Rapidamente

### **Teste Rápido de Desativação:**

```bash
# 1. Criar e ativar licença
# 2. No admin, desativar
# 3. Na extension, tentar enviar mensagem
# Deve bloquear imediatamente
```

### **Teste Rápido de Trial (SEM aguardar 15 min):**

```python
# Modificar temporariamente para 1 minuto:
# chatlove-backend/main.py linha ~520

# Antes:
license.expires_at = datetime.utcnow() + timedelta(minutes=15)

# Depois (APENAS PARA TESTE):
license.expires_at = datetime.utcnow() + timedelta(minutes=1)

# Reiniciar backend
# Criar licença trial
# Ativar
# Aguardar 1 minuto
# Tentar enviar mensagem
# Deve bloquear

# IMPORTANTE: Reverter para 15 minutos após teste!
```

---

## ✅ Checklist de Validação

- [ ] Licença desativada bloqueia no popup
- [ ] Licença desativada bloqueia no envio
- [ ] Trial expirada bloqueia no popup
- [ ] Trial expirada bloqueia no envio
- [ ] Trial não ativada não expira
- [ ] Licença full nunca expira
- [ ] Reativar licença funciona
- [ ] Mensagens de erro são claras
- [ ] Admin mostra status correto
- [ ] Contador de tempo funciona

---

## 🐛 Troubleshooting

### **Licença não bloqueia após desativar:**

```bash
# Verificar se backend foi reiniciado
sudo systemctl restart chatlove-backend

# Verificar logs
sudo journalctl -u chatlove-backend -f

# Recarregar página da extension
```

### **Trial não expira:**

```bash
# Verificar se expires_at foi definido
sqlite3 chatlove-backend/chatlove.db
SELECT license_key, license_type, expires_at FROM licenses;

# Se NULL, ativar licença novamente
```

### **Erro persiste após reativar:**

```bash
# Limpar cache da extension
# Chrome → Extension → Remover e recarregar
# Ou recarregar página do Lovable (F5)
```

---

**Sistema de bloqueios implementado e pronto para testes! 🎉**
