# Instruções Customizadas para IA - Sistema ChatLove
## 🌐 Configurações de Idioma e Ambiente
- **Idioma:** Sempre usar português brasileiro em todas as interações
- **Ambiente Virtual:** Sempre ativar a venv antes de executar o sistema
- **Terminal:** Usar sintaxe do PowerShell para todos os comandos no terminal
- **Personalidade:** Ser técnico, direto e objetivo. Evitar conversas desnecessárias

- **Evitar:** Arquivos soltos na raiz do projeto

## ⚠️ POLÍTICA CRÍTICA DE EDIÇÃO DE ARQUIVOS
- **NUNCA criar arquivos genéricos para correções** (ex: `view_corrigida.py`, `model_fix.py`)
- **SEMPRE editar o arquivo original/atual** em vez de criar novos
- **Manter integridade:** Preservar a estrutura e funcionalidade existente
- **Exemplo INCORRETO:** Criar `views_nova.py` para corrigir `views.py`
- **Exemplo CORRETO:** Editar diretamente o arquivo `views.py` existente

## 🖥️ Configurações do Servidor VPS
### Dados de Acesso
- **IP:** 209.38.79.211
- **Usuário SSH:** root
- **Chave SSH:** `C:\Users\Alan Cardane\.ssh\id_ed25519`
- **Diretório do Projeto:** `/var/www/chatlove`

### Comandos SSH Essenciais
```powershell
# Acesso SSH
ssh -i "C:\Users\Alan Cardane\.ssh\id_ed25519" root@209.38.79.211