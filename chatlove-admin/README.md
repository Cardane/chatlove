# ♥ ChatLove Admin Panel

Painel administrativo completo para gerenciar o sistema ChatLove.

---

## 🚀 Como Iniciar

### 1. Instalar Dependências

```bash
cd chatlove-admin
npm install
```

### 2. Iniciar Servidor de Desenvolvimento

```bash
npm run dev
```

O painel estará disponível em: **http://localhost:3000**

---

## 🔐 Login

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin123`

⚠️ **IMPORTANTE:** Altere a senha após o primeiro login!

---

## 📊 Funcionalidades

### Dashboard
- Estatísticas gerais do sistema
- Total de usuários
- Licenças ativas
- Tokens economizados
- Total de requisições

### Gerenciamento de Usuários
- Listar todos os usuários
- Criar novos usuários
- Ver estatísticas por usuário
- Licenças e tokens por usuário

### Gerenciamento de Licenças
- Listar todas as licenças
- Gerar novas licenças
- Copiar chaves com um clique
- Ativar/Desativar licenças
- Ver status de uso
- Tokens economizados por licença

---

## 🎨 Design

- Gradiente rosa/roxo moderno
- Interface responsiva
- Animações suaves
- Glassmorphism
- Ícones Lucide React

---

## 🔧 Tecnologias

- **React 18** - Framework
- **Vite** - Build tool
- **React Router** - Navegação
- **Axios** - HTTP client
- **Lucide React** - Ícones

---

## 📁 Estrutura

```
chatlove-admin/
├── src/
│   ├── components/
│   │   ├── Layout.jsx       # Layout principal
│   │   └── Layout.css
│   ├── pages/
│   │   ├── Login.jsx        # Tela de login
│   │   ├── Dashboard.jsx    # Dashboard
│   │   ├── Users.jsx        # Gerenciamento de usuários
│   │   └── Licenses.jsx     # Gerenciamento de licenças
│   ├── api.js               # Cliente API
│   ├── App.jsx              # Componente principal
│   └── main.jsx             # Entry point
├── package.json
└── vite.config.js
```

---

## 🚀 Build para Produção

```bash
npm run build
```

Os arquivos otimizados estarão em `dist/`

---

## 🔗 Integração com Backend

O painel se conecta automaticamente ao backend em:
```
http://127.0.0.1:8000
```

Certifique-se de que o backend está rodando antes de usar o painel!

---

## ✅ Checklist de Uso

- [ ] Backend rodando em http://127.0.0.1:8000
- [ ] Dependências instaladas (`npm install`)
- [ ] Servidor dev iniciado (`npm run dev`)
- [ ] Login realizado (admin/admin123)
- [ ] Senha alterada
- [ ] Licenças geradas
- [ ] Usuários criados

---

**Painel completo e funcional! ♥**
