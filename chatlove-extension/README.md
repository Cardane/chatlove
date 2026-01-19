# ♥ ChatLove - Extensão Chrome

Economize tokens usando ChatLove - Seu assistente inteligente para Lovable.dev

---

## 🚀 Como Testar Localmente

### 1. Iniciar o Backend

```bash
cd chatlove-backend
python database.py  # Inicializar database
python main.py      # Iniciar API
```

O backend estará rodando em: `http://127.0.0.1:8000`

### 2. Gerar uma Licença de Teste

Acesse: `http://127.0.0.1:8000/docs`

1. **Login Admin:**
   - Endpoint: `POST /api/admin/login`
   - Body:
     ```json
     {
       "username": "admin",
       "password": "admin123"
     }
     ```
   - Copie o `token` retornado

2. **Gerar Licença:**
   - Endpoint: `POST /api/admin/licenses`
   - Headers: `Authorization: Bearer SEU_TOKEN_AQUI`
   - Body:
     ```json
     {}
     ```
   - Copie a `license_key` retornada (formato: `XXXX-XXXX-XXXX-XXXX`)

### 3. Instalar a Extensão no Chrome

1. Abra o Chrome
2. Vá em `chrome://extensions/`
3. Ative o **Modo do desenvolvedor** (canto superior direito)
4. Clique em **Carregar sem compactação**
5. Selecione a pasta `chatlove-extension`

### 4. Ativar a Licença

1. Clique no ícone da extensão ChatLove
2. Digite seu nome de usuário
3. Cole a chave de licença gerada
4. Clique em **Ativar Licença**

### 5. Usar no Lovable.dev

1. Acesse https://lovable.dev
2. Faça login
3. Abra um projeto
4. A sidebar ChatLove aparecerá automaticamente
5. Digite suas instruções e envie!

---

## 📊 Funcionalidades

- ✅ **Ativação de Licença** - Sistema seguro com hardware ID
- ✅ **Contador de Tokens** - Veja quanto você economizou
- ✅ **Sidebar Integrada** - Interface moderna e intuitiva
- ✅ **Uso Ilimitado** - Enquanto a licença estiver ativa
- ✅ **Estatísticas** - Acompanhe seu uso

---

## 🔐 Segurança

- Hardware ID único por instalação
- Licença vinculada ao dispositivo
- JWT tokens com 30 dias de validade
- Validação contínua

---

## 🎨 Design

- Gradiente rosa/roxo
- Animações suaves
- Interface responsiva
- Ícone ♥ (coração)

---

## 🐛 Troubleshooting

### Erro: "License not activated"
- Abra o popup da extensão
- Ative sua licença

### Erro: "Token não encontrado"
- Faça logout e login novamente

### Erro: "Projeto não detectado"
- Certifique-se de estar em um projeto do Lovable
- URL deve ser: `https://lovable.dev/projects/...`

### Erro de conexão
- Verifique se o backend está rodando
- URL: `http://127.0.0.1:8000`

---

## 📝 Estrutura de Arquivos

```
chatlove-extension/
├── manifest.json       # Configuração da extensão
├── background.js       # Service worker (auth)
├── content.js          # Script injetado (sidebar)
├── popup.html          # Interface de ativação
├── popup.js            # Lógica do popup
└── icons/              # Ícones da extensão
```

---

## ✅ Checklist de Teste

- [ ] Backend rodando
- [ ] Licença gerada
- [ ] Extensão instalada
- [ ] Licença ativada
- [ ] Sidebar aparece no Lovable
- [ ] Mensagem enviada com sucesso
- [ ] Tokens contabilizados
- [ ] Estatísticas atualizadas

---

**Pronto para testar! ♥**
