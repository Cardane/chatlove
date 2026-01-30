"""
Launcher simples para o ChatLove Desktop
Usa navegador do sistema para evitar detecção
"""

import sys
import os
import json
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("PyWebView não encontrado. Usando navegador padrão do sistema.")

from cryptography.fernet import Fernet
import keyring


class SimpleSessionManager:
    """Gerenciador simples de sessões"""
    
    def __init__(self):
        self.app_dir = Path.home() / ".chatlove"
        self.sessions_dir = self.app_dir / "sessions"
        self.config_file = self.app_dir / "config.json"
        
        # Criar diretórios
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
            safe_filename = email.replace('@', '_').replace('.', '_').replace('\n', '').replace('\r', '').strip()
            
            self.accounts.append({
                'email': email,
                'password': encrypted_password,
                'active': len(self.accounts) == 0,
                'last_login': None,
                'session_file': f"{safe_filename}.json"
            })
            
            self._save_accounts()
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar conta: {e}")
            return False
    
    def list_accounts(self):
        """Lista contas disponíveis"""
        if not self.accounts:
            print("Nenhuma conta cadastrada.")
            return
        
        print("\n📧 Contas Cadastradas:")
        for i, account in enumerate(self.accounts):
            status = "🟢 ATIVA" if account.get('active', False) else "⚪ Inativa"
            last_login = account.get('last_login', 'Nunca')
            if last_login != 'Nunca':
                try:
                    dt = datetime.fromisoformat(last_login)
                    last_login = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
            
            print(f"{i+1}. {status} {account['email']}")
            print(f"   Último login: {last_login}")
    
    def set_active_account(self, email: str):
        """Define conta ativa"""
        for account in self.accounts:
            account['active'] = (account['email'] == email)
        
        self._save_accounts()
        print(f"✅ Conta ativa: {email}")


def show_menu():
    """Mostra menu principal"""
    print("\n" + "="*60)
    print("🚀 CHATLOVE DESKTOP - SISTEMA LOVABLE")
    print("="*60)
    print("1. 🌐 Abrir Lovable no Navegador")
    print("2. 📧 Gerenciar Contas")
    print("3. 📊 Status do Sistema")
    print("4. ❌ Sair")
    print("="*60)


def show_accounts_menu():
    """Mostra menu de contas"""
    print("\n" + "="*40)
    print("📧 GERENCIAR CONTAS")
    print("="*40)
    print("1. ➕ Adicionar Conta")
    print("2. 📋 Listar Contas")
    print("3. 🔄 Trocar Conta Ativa")
    print("4. ⬅️ Voltar")
    print("="*40)


def open_lovable():
    """Abre Lovable no navegador"""
    print("\n🌐 Abrindo Lovable.dev...")
    
    if WEBVIEW_AVAILABLE:
        try:
            print("📱 Usando WebView (janela dedicada)...")
            webview.create_window(
                'ChatLove - Lovable.dev',
                'https://lovable.dev/login',
                width=1200,
                height=800,
                resizable=True,
                shadow=True,
                on_top=False
            )
            webview.start(debug=False)
        except Exception as e:
            print(f"❌ Erro no WebView: {e}")
            print("🌐 Abrindo no navegador padrão...")
            webbrowser.open('https://lovable.dev/login')
    else:
        print("🌐 Abrindo no navegador padrão do sistema...")
        webbrowser.open('https://lovable.dev/login')
    
    print("✅ Lovable aberto! Faça login manualmente.")
    print("💡 Dica: Seus cookies serão salvos automaticamente pelo navegador.")


def manage_accounts(session_manager):
    """Gerencia contas"""
    while True:
        show_accounts_menu()
        choice = input("\n👉 Escolha uma opção: ").strip()
        
        if choice == '1':
            # Adicionar conta
            print("\n➕ Adicionar Nova Conta")
            email = input("📧 Email: ").strip()
            if not email:
                print("❌ Email não pode estar vazio!")
                continue
            
            import getpass
            password = getpass.getpass("🔒 Senha: ")
            if not password:
                print("❌ Senha não pode estar vazia!")
                continue
            
            if session_manager.add_account(email, password):
                print(f"✅ Conta {email} adicionada com sucesso!")
            else:
                print("❌ Erro ao adicionar conta!")
        
        elif choice == '2':
            # Listar contas
            session_manager.list_accounts()
        
        elif choice == '3':
            # Trocar conta ativa
            if not session_manager.accounts:
                print("❌ Nenhuma conta cadastrada!")
                continue
            
            print("\n🔄 Trocar Conta Ativa")
            session_manager.list_accounts()
            
            try:
                index = int(input("\n👉 Número da conta: ")) - 1
                if 0 <= index < len(session_manager.accounts):
                    email = session_manager.accounts[index]['email']
                    session_manager.set_active_account(email)
                else:
                    print("❌ Número inválido!")
            except ValueError:
                print("❌ Digite um número válido!")
        
        elif choice == '4':
            break
        
        else:
            print("❌ Opção inválida!")


def show_status(session_manager):
    """Mostra status do sistema"""
    print("\n" + "="*50)
    print("📊 STATUS DO SISTEMA")
    print("="*50)
    
    # Contas
    print(f"📧 Contas cadastradas: {len(session_manager.accounts)}")
    
    active_account = None
    for account in session_manager.accounts:
        if account.get('active', False):
            active_account = account
            break
    
    if active_account:
        print(f"🟢 Conta ativa: {active_account['email']}")
        last_login = active_account.get('last_login', 'Nunca')
        if last_login != 'Nunca':
            try:
                dt = datetime.fromisoformat(last_login)
                last_login = dt.strftime("%d/%m/%Y %H:%M")
            except:
                pass
        print(f"⏰ Último login: {last_login}")
    else:
        print("⚪ Nenhuma conta ativa")
    
    # Diretórios
    print(f"📁 Dados salvos em: {session_manager.app_dir}")
    print(f"🍪 Sessões em: {session_manager.sessions_dir}")
    
    # WebView
    if WEBVIEW_AVAILABLE:
        print("📱 WebView: ✅ Disponível")
    else:
        print("📱 WebView: ❌ Não disponível (usando navegador padrão)")
    
    print("="*50)


def main():
    """Função principal"""
    print("🚀 Iniciando ChatLove Desktop...")
    
    # Verificar dependências
    try:
        session_manager = SimpleSessionManager()
        print("✅ Sistema iniciado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao iniciar sistema: {e}")
        return
    
    # Menu principal
    while True:
        show_menu()
        choice = input("\n👉 Escolha uma opção: ").strip()
        
        if choice == '1':
            # Abrir Lovable
            open_lovable()
        
        elif choice == '2':
            # Gerenciar contas
            manage_accounts(session_manager)
        
        elif choice == '3':
            # Status
            show_status(session_manager)
        
        elif choice == '4':
            # Sair
            print("\n👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida!")


if __name__ == "__main__":
    main()
