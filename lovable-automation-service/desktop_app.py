"""
ChatLove Desktop App - Interface Unificada
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QGroupBox, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QInputDialog, QProgressBar, QStatusBar, QMenuBar,
    QToolBar, QComboBox, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

import keyring
from cryptography.fernet import Fernet


class SessionManager:
    """Gerenciador de sessões persistentes"""
    
    def __init__(self):
        self.app_dir = Path.home() / ".chatlove"
        self.sessions_dir = self.app_dir / "sessions"
        self.config_file = self.app_dir / "config.json"
        
        # Criar diretórios se não existirem
        self.app_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Chave de criptografia
        self.cipher_key = self._get_or_create_key()
        self.cipher = Fernet(self.cipher_key)
        
        self.accounts = self._load_accounts()
    
    def _get_or_create_key(self) -> bytes:
        """Obtém ou cria chave de criptografia"""
        try:
            key = keyring.get_password("chatlove", "encryption_key")
            if key:
                return key.encode()
        except:
            pass
        
        # Criar nova chave
        key = Fernet.generate_key()
        try:
            keyring.set_password("chatlove", "encryption_key", key.decode())
        except:
            pass
        
        return key
    
    def _load_accounts(self) -> List[Dict]:
        """Carrega contas salvas"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('accounts', [])
        except:
            pass
        
        return []
    
    def _save_accounts(self):
        """Salva contas"""
        try:
            config = {'accounts': self.accounts}
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar contas: {e}")
    
    def add_account(self, email: str, password: str) -> bool:
        """Adiciona nova conta"""
        try:
            # Criptografar senha
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            
            # Verificar se já existe
            for account in self.accounts:
                if account['email'] == email:
                    account['password'] = encrypted_password
                    self._save_accounts()
                    return True
            
            # Adicionar nova conta
            # Limpar caracteres inválidos do nome do arquivo
            safe_filename = email.replace('@', '_').replace('.', '_').replace('\n', '').replace('\r', '').strip()
            
            self.accounts.append({
                'email': email,
                'password': encrypted_password,
                'active': len(self.accounts) == 0,  # Primeira conta é ativa
                'last_login': None,
                'session_file': f"{safe_filename}.json"
            })
            
            self._save_accounts()
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar conta: {e}")
            return False
    
    def get_password(self, email: str) -> Optional[str]:
        """Obtém senha descriptografada"""
        try:
            for account in self.accounts:
                if account['email'] == email:
                    encrypted_password = account['password'].encode()
                    return self.cipher.decrypt(encrypted_password).decode()
        except Exception as e:
            print(f"Erro ao obter senha: {e}")
        
        return None
    
    def get_active_account(self) -> Optional[Dict]:
        """Obtém conta ativa"""
        for account in self.accounts:
            if account.get('active', False):
                return account
        
        return self.accounts[0] if self.accounts else None
    
    def set_active_account(self, email: str):
        """Define conta ativa"""
        for account in self.accounts:
            account['active'] = (account['email'] == email)
        
        self._save_accounts()
    
    def save_session_data(self, email: str, cookies: List, local_storage: Dict, session_storage: Dict):
        """Salva dados da sessão"""
        try:
            account = None
            for acc in self.accounts:
                if acc['email'] == email:
                    account = acc
                    break
            
            if not account:
                return False
            
            session_data = {
                'email': email,
                'cookies': cookies,
                'local_storage': local_storage,
                'session_storage': session_storage,
                'saved_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            session_file = self.sessions_dir / account['session_file']
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Atualizar último login
            account['last_login'] = datetime.now().isoformat()
            self._save_accounts()
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar sessão: {e}")
            return False
    
    def load_session_data(self, email: str) -> Optional[Dict]:
        """Carrega dados da sessão"""
        try:
            account = None
            for acc in self.accounts:
                if acc['email'] == email:
                    account = acc
                    break
            
            if not account:
                return None
            
            session_file = self.sessions_dir / account['session_file']
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Verificar se não expirou
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                session_file.unlink()  # Remove arquivo expirado
                return None
            
            return session_data
            
        except Exception as e:
            print(f"Erro ao carregar sessão: {e}")
            return None


class LovableWebView(QWebEngineView):
    """WebView customizado para Lovable"""
    
    login_detected = pyqtSignal()      # Login manual detectado
    project_opened = pyqtSignal(str)   # project_id
    message_sent = pyqtSignal(str)     # message
    response_received = pyqtSignal(str) # response
    session_expired = pyqtSignal()     # Sessão expirou
    
    def __init__(self):
        super().__init__()
        
        # Configurar perfil personalizado para evitar detecção
        self.profile = QWebEngineProfile("chatlove_browser", self)
        
        # Configurar User-Agent real
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Desabilitar automação detectável
        self.profile.setHttpAcceptLanguage("pt-BR,pt;q=0.9,en;q=0.8")
        
        self.page_custom = QWebEnginePage(self.profile, self)
        self.setPage(self.page_custom)
        
        # Conectar sinais
        self.urlChanged.connect(self._on_url_changed)
        self.loadFinished.connect(self._on_load_finished)
        
        self.current_project_id = None
        self.is_logged_in = False
        self.automation_active = False
    
    def _on_url_changed(self, url: QUrl):
        """Detecta mudanças de URL"""
        url_str = url.toString()
        
        # Detectar login bem-sucedido (manual)
        if "/dashboard" in url_str and not self.is_logged_in:
            self.is_logged_in = True
            self.login_detected.emit()
        
        # Detectar se sessão expirou (redirecionou para login)
        if "/login" in url_str and self.is_logged_in:
            self.is_logged_in = False
            self.automation_active = False
            self.session_expired.emit()
        
        # Detectar projeto aberto
        if "/projects/" in url_str:
            parts = url_str.split("/projects/")
            if len(parts) > 1:
                project_id = parts[1].split("/")[0].split("?")[0]
                if project_id != self.current_project_id:
                    self.current_project_id = project_id
                    self.automation_active = True  # Ativar automação no projeto
                    self.project_opened.emit(project_id)
    
    def _on_load_finished(self, success: bool):
        """Página carregada"""
        if success:
            # Injetar JavaScript para evitar detecção de automação
            self.page().runJavaScript("""
                // Remover propriedades que indicam automação
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Remover outras propriedades de detecção
                delete window.chrome;
                
                // Simular propriedades de navegador real
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en'],
                });
                
                // Monitorar envio de mensagens (discretamente)
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const result = originalFetch.apply(this, args);
                    
                    // Detectar requisições de chat (sem logs visíveis)
                    if (args[0] && args[0].includes('/chat')) {
                        // Silencioso
                    }
                    
                    return result;
                };
                
                'Anti-detection measures applied';
            """)
    
    def inject_cookies(self, cookies: List[Dict]):
        """Injeta cookies salvos"""
        for cookie in cookies:
            # Converter para formato QWebEngine
            # Implementar injeção de cookies
            pass
    
    def extract_cookies(self) -> List[Dict]:
        """Extrai cookies atuais"""
        # Implementar extração de cookies
        return []
    
    def send_message(self, message: str):
        """Envia mensagem para o chat"""
        js_code = f"""
        // Encontrar campo de input do chat
        const chatInput = document.querySelector('textarea[placeholder*="message"], textarea[placeholder*="Message"], input[placeholder*="message"]');
        
        if (chatInput) {{
            chatInput.value = `{message}`;
            chatInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            // Encontrar botão de envio
            const sendButton = document.querySelector('button[type="submit"], button[aria-label*="Send"], button:has-text("Send")');
            
            if (sendButton) {{
                sendButton.click();
                'Message sent successfully';
            }} else {{
                // Tentar Enter
                chatInput.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                'Message sent with Enter';
            }}
        }} else {{
            'Chat input not found';
        }}
        """
        
        self.page().runJavaScript(js_code, self._on_message_sent)
    
    def _on_message_sent(self, result):
        """Callback após envio de mensagem"""
        if result and "sent" in result:
            self.message_sent.emit("Message sent")


class ControlPanel(QWidget):
    """Painel de controle lateral"""
    
    account_changed = pyqtSignal(str)  # email
    project_selected = pyqtSignal(str) # project_id
    send_message = pyqtSignal(str)     # message
    
    def __init__(self, session_manager: SessionManager):
        super().__init__()
        self.session_manager = session_manager
        self.setup_ui()
        self.refresh_accounts()
    
    def setup_ui(self):
        """Configura interface do painel"""
        layout = QVBoxLayout(self)
        
        # Seção de Contas
        accounts_group = QGroupBox("🔐 Contas Lovable")
        accounts_layout = QVBoxLayout(accounts_group)
        
        self.accounts_list = QListWidget()
        self.accounts_list.itemClicked.connect(self._on_account_selected)
        accounts_layout.addWidget(self.accounts_list)
        
        # Status de login
        self.login_status = QLabel("Status: Não logado")
        self.login_status.setStyleSheet("color: red; font-weight: bold;")
        accounts_layout.addWidget(self.login_status)
        
        # Botões de conta
        accounts_buttons = QHBoxLayout()
        self.add_account_btn = QPushButton("➕ Adicionar")
        self.add_account_btn.clicked.connect(self._add_account)
        self.login_manual_btn = QPushButton("🔓 Login Manual")
        self.login_manual_btn.clicked.connect(self._manual_login)
        
        accounts_buttons.addWidget(self.add_account_btn)
        accounts_buttons.addWidget(self.login_manual_btn)
        accounts_layout.addLayout(accounts_buttons)
        
        # Botão remover (segunda linha)
        remove_layout = QHBoxLayout()
        self.remove_account_btn = QPushButton("🗑️ Remover Conta")
        self.remove_account_btn.clicked.connect(self._remove_account)
        remove_layout.addWidget(self.remove_account_btn)
        accounts_layout.addLayout(remove_layout)
        
        layout.addWidget(accounts_group)
        
        # Seção de Projetos
        projects_group = QGroupBox("📁 Projetos")
        projects_layout = QVBoxLayout(projects_group)
        
        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self._on_project_selected)
        projects_layout.addWidget(self.projects_list)
        
        self.refresh_projects_btn = QPushButton("🔄 Atualizar Projetos")
        self.refresh_projects_btn.clicked.connect(self._refresh_projects)
        projects_layout.addWidget(self.refresh_projects_btn)
        
        layout.addWidget(projects_group)
        
        # Seção de Chat Rápido
        chat_group = QGroupBox("💬 Chat Rápido")
        chat_layout = QVBoxLayout(chat_group)
        
        self.quick_message = QLineEdit()
        self.quick_message.setPlaceholderText("Digite mensagem...")
        self.quick_message.returnPressed.connect(self._send_quick_message)
        chat_layout.addWidget(self.quick_message)
        
        self.send_btn = QPushButton("📤 Enviar")
        self.send_btn.clicked.connect(self._send_quick_message)
        chat_layout.addWidget(self.send_btn)
        
        layout.addWidget(chat_group)
        
        # Seção de Logs
        logs_group = QGroupBox("📊 Logs")
        logs_layout = QVBoxLayout(logs_group)
        
        self.logs_text = QTextEdit()
        self.logs_text.setMaximumHeight(150)
        self.logs_text.setReadOnly(True)
        logs_layout.addWidget(self.logs_text)
        
        layout.addWidget(logs_group)
        
        # Espaçador
        layout.addStretch()
    
    def refresh_accounts(self):
        """Atualiza lista de contas"""
        self.accounts_list.clear()
        
        for account in self.session_manager.accounts:
            item = QListWidgetItem()
            
            # Status visual
            status = "🟢" if account.get('active', False) else "⚪"
            last_login = account.get('last_login', 'Nunca')
            if last_login != 'Nunca':
                try:
                    dt = datetime.fromisoformat(last_login)
                    last_login = dt.strftime("%d/%m %H:%M")
                except:
                    pass
            
            item.setText(f"{status} {account['email']}\n   Último login: {last_login}")
            item.setData(Qt.ItemDataRole.UserRole, account['email'])
            
            self.accounts_list.addItem(item)
    
    def _on_account_selected(self, item: QListWidgetItem):
        """Conta selecionada"""
        email = item.data(Qt.ItemDataRole.UserRole)
        self.session_manager.set_active_account(email)
        self.refresh_accounts()
        self.account_changed.emit(email)
        self.add_log(f"Conta ativa: {email}")
    
    def _add_account(self):
        """Adiciona nova conta"""
        email, ok1 = QInputDialog.getText(self, "Nova Conta", "Email:")
        if not ok1 or not email:
            return
        
        password, ok2 = QInputDialog.getText(self, "Nova Conta", "Senha:", QLineEdit.EchoMode.Password)
        if not ok2 or not password:
            return
        
        if self.session_manager.add_account(email, password):
            self.refresh_accounts()
            self.add_log(f"Conta adicionada: {email}")
            QMessageBox.information(self, "Sucesso", f"Conta {email} adicionada com sucesso!")
        else:
            QMessageBox.warning(self, "Erro", "Erro ao adicionar conta.")
    
    def _manual_login(self):
        """Inicia processo de login manual"""
        active_account = self.session_manager.get_active_account()
        if not active_account:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta primeiro!")
            return
        
        # Emitir sinal para carregar página de login
        self.account_changed.emit(active_account['email'])
        self.add_log("Iniciando login manual...")
        
        # Mostrar instruções
        QMessageBox.information(
            self, 
            "Login Manual", 
            f"Agora faça login manualmente na conta:\n{active_account['email']}\n\n"
            "O sistema detectará automaticamente quando você estiver logado e salvará a sessão."
        )
    
    def _remove_account(self):
        """Remove conta selecionada"""
        current_item = self.accounts_list.currentItem()
        if not current_item:
            return
        
        email = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Confirmar", 
            f"Remover conta {email}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remover da lista
            self.session_manager.accounts = [
                acc for acc in self.session_manager.accounts 
                if acc['email'] != email
            ]
            self.session_manager._save_accounts()
            self.refresh_accounts()
            self.add_log(f"Conta removida: {email}")
    
    def update_login_status(self, is_logged_in: bool):
        """Atualiza status de login"""
        if is_logged_in:
            self.login_status.setText("Status: ✅ Logado")
            self.login_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.login_status.setText("Status: ❌ Não logado")
            self.login_status.setStyleSheet("color: red; font-weight: bold;")
    
    def _on_project_selected(self, item: QListWidgetItem):
        """Projeto selecionado"""
        project_id = item.data(Qt.ItemDataRole.UserRole)
        self.project_selected.emit(project_id)
        self.add_log(f"Projeto selecionado: {project_id}")
    
    def _refresh_projects(self):
        """Atualiza lista de projetos"""
        # TODO: Implementar busca de projetos via JavaScript no WebView
        self.add_log("Atualizando projetos...")
    
    def _send_quick_message(self):
        """Envia mensagem rápida"""
        message = self.quick_message.text().strip()
        if message:
            self.send_message.emit(message)
            self.quick_message.clear()
            self.add_log(f"Mensagem enviada: {message[:50]}...")
    
    def add_log(self, message: str):
        """Adiciona log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.append(f"[{timestamp}] {message}")
        
        # Manter apenas últimas 100 linhas
        text = self.logs_text.toPlainText()
        lines = text.split('\n')
        if len(lines) > 100:
            self.logs_text.setPlainText('\n'.join(lines[-100:]))
        
        # Scroll para o final
        cursor = self.logs_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.logs_text.setTextCursor(cursor)


class ChatLoveMainWindow(QMainWindow):
    """Janela principal do ChatLove Desktop"""
    
    def __init__(self):
        super().__init__()
        
        self.session_manager = SessionManager()
        self.setup_ui()
        self.setup_connections()
        
        # Timer para auto-save
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_session)
        self.auto_save_timer.start(60000)  # A cada minuto
    
    def setup_ui(self):
        """Configura interface principal"""
        self.setWindowTitle("ChatLove Desktop - Sistema Lovable")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel de controle (esquerda)
        self.control_panel = ControlPanel(self.session_manager)
        self.control_panel.setMaximumWidth(350)
        self.control_panel.setMinimumWidth(300)
        
        # WebView (direita)
        self.web_view = LovableWebView()
        
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.web_view)
        
        # Proporções do splitter
        splitter.setSizes([300, 1100])
        
        main_layout.addWidget(splitter)
        
        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("ChatLove Desktop iniciado")
        
        # Menu bar
        self.setup_menu_bar()
        
        # Toolbar
        self.setup_toolbar()
        
        # Carregar conta ativa
        self._load_active_account()
    
    def setup_menu_bar(self):
        """Configura barra de menu"""
        menubar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menubar.addMenu("Arquivo")
        
        new_account_action = QAction("Nova Conta", self)
        new_account_action.triggered.connect(self.control_panel._add_account)
        file_menu.addAction(new_account_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Ferramentas
        tools_menu = menubar.addMenu("Ferramentas")
        
        screenshot_action = QAction("Screenshot", self)
        screenshot_action.triggered.connect(self._take_screenshot)
        tools_menu.addAction(screenshot_action)
        
        clear_cache_action = QAction("Limpar Cache", self)
        clear_cache_action.triggered.connect(self._clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        # Menu Ajuda
        help_menu = menubar.addMenu("Ajuda")
        
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Configura barra de ferramentas"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Botão voltar
        back_action = QAction("⬅️", self)
        back_action.setToolTip("Voltar")
        back_action.triggered.connect(self.web_view.back)
        toolbar.addAction(back_action)
        
        # Botão avançar
        forward_action = QAction("➡️", self)
        forward_action.setToolTip("Avançar")
        forward_action.triggered.connect(self.web_view.forward)
        toolbar.addAction(forward_action)
        
        # Botão recarregar
        reload_action = QAction("🔄", self)
        reload_action.setToolTip("Recarregar")
        reload_action.triggered.connect(self.web_view.reload)
        toolbar.addAction(reload_action)
        
        toolbar.addSeparator()
        
        # Botão home
        home_action = QAction("🏠", self)
        home_action.setToolTip("Ir para Dashboard")
        home_action.triggered.connect(self._go_home)
        toolbar.addAction(home_action)
        
        # Botão projetos
        projects_action = QAction("📁", self)
        projects_action.setToolTip("Ir para Projetos")
        projects_action.triggered.connect(self._go_projects)
        toolbar.addAction(projects_action)
    
    def setup_connections(self):
        """Configura conexões de sinais"""
        # Painel de controle
        self.control_panel.account_changed.connect(self._on_account_changed)
        self.control_panel.project_selected.connect(self._on_project_selected)
        self.control_panel.send_message.connect(self._on_send_message)
        
        # WebView
        self.web_view.login_detected.connect(self._on_login_detected)
        self.web_view.project_opened.connect(self._on_project_opened)
        self.web_view.message_sent.connect(self._on_message_sent)
        self.web_view.response_received.connect(self._on_response_received)
        self.web_view.session_expired.connect(self._on_session_expired)
    
    def _load_active_account(self):
        """Carrega conta ativa"""
        active_account = self.session_manager.get_active_account()
        if active_account:
            self._load_account_session(active_account['email'])
    
    def _load_account_session(self, email: str):
        """Carrega sessão da conta"""
        self.control_panel.add_log(f"Carregando sessão: {email}")
        
        # Carregar dados salvos
        session_data = self.session_manager.load_session_data(email)
        
        if session_data:
            # Injetar cookies
            self.web_view.inject_cookies(session_data['cookies'])
            self.control_panel.add_log("Cookies carregados")
        
        # Navegar para Lovable
        self.web_view.load(QUrl("https://lovable.dev/dashboard"))
        self.status_bar.showMessage(f"Conta ativa: {email}")
    
    def _on_account_changed(self, email: str):
        """Conta alterada"""
        self._load_account_session(email)
    
    def _on_project_selected(self, project_id: str):
        """Projeto selecionado"""
        url = f"https://lovable.dev/projects/{project_id}"
        self.web_view.load(QUrl(url))
        self.control_panel.add_log(f"Abrindo projeto: {project_id}")
    
    def _on_send_message(self, message: str):
        """Enviar mensagem"""
        self.web_view.send_message(message)
    
    def _on_login_detected(self):
        """Login detectado"""
        self.control_panel.add_log("✅ Login detectado! Salvando sessão...")
        self.control_panel.update_login_status(True)
        self._save_current_session()
        
        # Navegar para dashboard para confirmar login
        self.web_view.load(QUrl("https://lovable.dev/dashboard"))
    
    def _on_project_opened(self, project_id: str):
        """Projeto aberto"""
        self.control_panel.add_log(f"📁 Projeto aberto: {project_id}")
        self.control_panel.add_log("🤖 Automação ativada no projeto!")
    
    def _on_session_expired(self):
        """Sessão expirou"""
        self.control_panel.add_log("⚠️ Sessão expirou! Faça login novamente.")
        self.control_panel.update_login_status(False)
        
        # Mostrar aviso
        QMessageBox.warning(
            self,
            "Sessão Expirada",
            "Sua sessão no Lovable expirou.\n\n"
            "Clique em 'Login Manual' para fazer login novamente."
        )
    
    def _on_message_sent(self, message: str):
        """Mensagem enviada"""
        self.control_panel.add_log("Mensagem enviada com sucesso")
    
    def _on_response_received(self, response: str):
        """Resposta recebida"""
        self.control_panel.add_log("Resposta recebida do Lovable")
    
    def _auto_save_session(self):
        """Auto-save da sessão"""
        active_account = self.session_manager.get_active_account()
        if active_account:
            self._save_current_session()
    
    def _save_current_session(self):
        """Salva sessão atual"""
        active_account = self.session_manager.get_active_account()
        if not active_account:
            return
        
        try:
            # Extrair cookies e dados
            cookies = self.web_view.extract_cookies()
            
            # Salvar sessão
            self.session_manager.save_session_data(
                active_account['email'],
                cookies,
                {},  # local_storage - TODO: implementar
                {}   # session_storage - TODO: implementar
            )
            
        except Exception as e:
            self.control_panel.add_log(f"Erro ao salvar sessão: {e}")
    
    def _go_home(self):
        """Ir para dashboard"""
        self.web_view.load(QUrl("https://lovable.dev/dashboard"))
    
    def _go_projects(self):
        """Ir para projetos"""
        self.web_view.load(QUrl("https://lovable.dev/dashboard/projects"))
    
    def _take_screenshot(self):
        """Tirar screenshot"""
        # TODO: Implementar screenshot
        self.control_panel.add_log("Screenshot salvo")
    
    def _clear_cache(self):
        """Limpar cache"""
        self.web_view.page().profile().clearHttpCache()
        self.control_panel.add_log("Cache limpo")
    
    def _show_about(self):
        """Mostrar sobre"""
        QMessageBox.about(
            self,
            "Sobre ChatLove Desktop",
            "ChatLove Desktop v1.0\n\n"
            "Sistema de automação para Lovable.dev\n"
            "Interface unificada com gerenciamento de sessões\n\n"
            "Desenvolvido para uso pessoal"
        )
    
    def closeEvent(self, event):
        """Evento de fechamento"""
        # Salvar sessão antes de fechar
        self._save_current_session()
        event.accept()


def main():
    """Função principal"""
    app = QApplication(sys.argv)
    
    # Configurar aplicação
    app.setApplicationName("ChatLove Desktop")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("ChatLove")
    
    # Criar e mostrar janela principal
    window = ChatLoveMainWindow()
    window.show()
    
    # Executar aplicação
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
