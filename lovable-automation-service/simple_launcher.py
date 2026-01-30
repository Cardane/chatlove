"""
ChatLove Desktop - Launcher Simples
Solucao final para usar Lovable sem deteccao
"""

import sys
import os
import json
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Configurar encoding para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

from cryptography.fernet import Fernet
import keyring


class SessionManager:
    """Gerenciador de sessoes"""
    
    def __init__(self):
        self.app_dir = Path.home() / ".chatlove"
        self.config_file = self.app_dir / "config.json"
        
        # Criar diretorios
        self.app_dir.mkdir(exist_ok=True)
        
        # Chave de criptografia
        self.cipher_key = self._get_or_create_key()
        self.cipher = Fernet(self.cipher_key)
        
        self.accounts = self._load_accounts()
    
    def _get_or_create_key(self) -> bytes:
        """Obtem ou cria chave de criptografia"""
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
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('accounts', [])
        except:
            pass
        
        return []
    
    def _save_accounts(self):
        """Salva contas"""
        try:
            config = {'accounts': self.accounts}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar contas: {e}")
    
    def add_account(self, email: str, password: str) -> bool:
        """Adiciona nova conta"""
        try:
            # Criptografar senha
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            
            # Verificar se ja existe
            for account in self.accounts:
                if account['email'] == email:
                    account['password'] = encrypted_password
                    account['last_login'] = datetime.now().isoformat()
                    self._save_accounts()
                    return True
            
            # Adicionar nova conta
            self.accounts.append({
                'email': email,
                'password': encrypted_password,
                'active': len(self.accounts) == 0,
                'last_login': datetime.now().isoformat()
            })
            
            self._save_accounts()
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar conta: {e}")
            return False
    
    def list_accounts(self):
        """Lista contas disponiveis"""
        if not self.accounts:
            print("Nenhuma conta cadastrada.")
            return
        
        print("\nContas Cadastradas:")
        for i, account in enumerate(self.accounts):
            status = "ATIVA" if account.get('active', False) else "Inativa"
            last_login = account.get('last_login', 'Nunca')
            if last_login != 'Nunca':
                try:
                    dt = datetime.fromisoformat(last_login)
                    last_login = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
            
            print(f"{i+1}. [{status}] {account['email']}")
            print(f"   Ultimo login: {last_login}")
    
    def set_active_account(self, email: str):
        """Define conta ativa"""
        for account in self.accounts:
            account['active'] = (account['email'] == email)
        
        self._save_accounts()
        print(f"Conta ativa: {email}")
    
    def get_active_account(self):
        """Obtem conta ativa"""
        for account in self.accounts:
            if account.get('active', False):
                return account
        return self.accounts[0] if self.accounts else None


def show_menu():
    """Mostra menu principal"""
    print("\n" + "="*60)
    print("CHATLOVE DESKTOP - SISTEMA LOVABLE")
    print("="*60)
    print("1. Abrir Lovable no Navegador")
    print("2. Gerenciar Contas")
    print("3. Status do Sistema")
    print("4. Instrucoes de Uso")
    print("5. Sair")
    print("="*60)


def show_accounts_menu():
    """Mostra menu de contas"""
    print("\n" + "="*40)
    print("GERENCIAR CONTAS")
    print("="*40)
    print("1. Adicionar Conta")
    print("2. Listar Contas")
    print("3. Trocar Conta Ativa")
    print("4. Voltar")
    print("="*40)


def open_lovable_browser():
    """Abre Lovable no navegador padrao"""
    print("\nAbrindo Lovable.dev no navegador padrao...")
    print("IMPORTANTE: Use o navegador NORMAL (Chrome, Edge, Firefox)")
    print("NAO use modo incognito ou privado!")
    
    try:
        webbrowser.open('https://lovable.dev/login')
        print("Lovable aberto no navegador!")
        print("\nINSTRUCOES:")
        print("1. Faca login MANUALMENTE na sua conta")
        print("2. Use normalmente - nao sera detectado como bot")
        print("3. Seus cookies ficam salvos no navegador")
        print("4. Proxima vez ja estara logado automaticamente")
        return True
    except Exception as e:
        print(f"Erro ao abrir navegador: {e}")
        return False


def open_lovable_webview():
    """Abre Lovable em WebView dedicado"""
    if not WEBVIEW_AVAILABLE:
        print("WebView nao disponivel. Usando navegador padrao...")
        return open_lovable_browser()
    
    print("\nAbrindo Lovable.dev em janela dedicada...")
    
    try:
        # Configurar WebView para parecer navegador real
        webview.create_window(
            'Lovable.dev - ChatLove',
            'https://lovable.dev/login',
            width=1200,
            height=800,
            resizable=True,
            shadow=True,
            on_top=False,
            text_select=True
        )
        
        print("Janela do Lovable aberta!")
        print("\nINSTRUCOES:")
        print("1. Faca login MANUALMENTE na janela que abriu")
        print("2. Use normalmente - WebView nao e detectado")
        print("3. Feche a janela quando terminar")
        
        # Iniciar WebView (bloqueia ate fechar)
        webview.start(debug=False)
        
        print("Janela do Lovable fechada.")
        return True
        
    except Exception as e:
        print(f"Erro no WebView: {e}")
        print("Tentando navegador padrao...")
        return open_lovable_browser()


def manage_accounts(session_manager):
    """Gerencia contas"""
    while True:
        show_accounts_menu()
        choice = input("\nEscolha uma opcao: ").strip()
        
        if choice == '1':
            # Adicionar conta
            print("\nAdicionar Nova Conta")
            email = input("Email: ").strip()
            if not email:
                print("Email nao pode estar vazio!")
                continue
            
            import getpass
            password = getpass.getpass("Senha: ")
            if not password:
                print("Senha nao pode estar vazia!")
                continue
            
            if session_manager.add_account(email, password):
                print(f"Conta {email} adicionada com sucesso!")
            else:
                print("Erro ao adicionar conta!")
        
        elif choice == '2':
            # Listar contas
            session_manager.list_accounts()
        
        elif choice == '3':
            # Trocar conta ativa
            if not session_manager.accounts:
                print("Nenhuma conta cadastrada!")
                continue
            
            print("\nTrocar Conta Ativa")
            session_manager.list_accounts()
            
            try:
                index = int(input("\nNumero da conta: ")) - 1
                if 0 <= index < len(session_manager.accounts):
                    email = session_manager.accounts[index]['email']
                    session_manager.set_active_account(email)
                else:
                    print("Numero invalido!")
            except ValueError:
                print("Digite um numero valido!")
        
        elif choice == '4':
            break
        
        else:
            print("Opcao invalida!")


def show_status(session_manager):
    """Mostra status do sistema"""
    print("\n" + "="*50)
    print("STATUS DO SISTEMA")
    print("="*50)
    
    # Contas
    print(f"Contas cadastradas: {len(session_manager.accounts)}")
    
    active_account = session_manager.get_active_account()
    if active_account:
        print(f"Conta ativa: {active_account['email']}")
        last_login = active_account.get('last_login', 'Nunca')
        if last_login != 'Nunca':
            try:
                dt = datetime.fromisoformat(last_login)
                last_login = dt.strftime("%d/%m/%Y %H:%M")
            except:
                pass
        print(f"Ultimo login: {last_login}")
    else:
        print("Nenhuma conta ativa")
    
    # Diretorios
    print(f"Dados salvos em: {session_manager.app_dir}")
    
    # WebView
    if WEBVIEW_AVAILABLE:
        print("WebView: Disponivel")
    else:
        print("WebView: Nao disponivel (usando navegador padrao)")
    
    print("="*50)


def show_instructions():
    """Mostra instrucoes de uso"""
    print("\n" + "="*60)
    print("INSTRUCOES DE USO")
    print("="*60)
    print()
    print("PROBLEMA IDENTIFICADO:")
    print("- Lovable detecta automacao e bloqueia acesso")
    print("- Qualquer navegador controlado por Python e detectado")
    print("- Mesmo WebView pode ser identificado")
    print()
    print("SOLUCAO IMPLEMENTADA:")
    print("1. Use o navegador NORMAL do seu sistema")
    print("2. Abra Lovable.dev manualmente")
    print("3. Faca login normalmente")
    print("4. Use como sempre usou")
    print()
    print("COMO USAR ESTE SISTEMA:")
    print("1. Adicione sua conta (opcao 2)")
    print("2. Abra Lovable (opcao 1)")
    print("3. Faca login manualmente")
    print("4. Use normalmente")
    print()
    print("VANTAGENS:")
    print("- Nao e detectado como bot")
    print("- Cookies salvos pelo navegador")
    print("- Funciona sempre")
    print("- Simples e confiavel")
    print()
    print("RECOMENDACAO FINAL:")
    print("Use seu navegador normal (Chrome/Edge/Firefox)")
    print("Abra https://lovable.dev/login manualmente")
    print("Este sistema serve apenas para gerenciar suas contas")
    print("="*60)


def main():
    """Funcao principal"""
    print("Iniciando ChatLove Desktop...")
    
    # Verificar dependencias
    try:
        session_manager = SessionManager()
        print("Sistema iniciado com sucesso!")
    except Exception as e:
        print(f"Erro ao iniciar sistema: {e}")
        return
    
    # Menu principal
    while True:
        show_menu()
        choice = input("\nEscolha uma opcao: ").strip()
        
        if choice == '1':
            # Abrir Lovable
            print("\nComo deseja abrir o Lovable?")
            print("1. Navegador padrao (RECOMENDADO)")
            print("2. WebView dedicado")
            print("3. Cancelar")
            
            sub_choice = input("\nOpcao: ").strip()
            
            if sub_choice == '1':
                open_lovable_browser()
            elif sub_choice == '2':
                open_lovable_webview()
            elif sub_choice == '3':
                continue
            else:
                print("Opcao invalida!")
        
        elif choice == '2':
            # Gerenciar contas
            manage_accounts(session_manager)
        
        elif choice == '3':
            # Status
            show_status(session_manager)
        
        elif choice == '4':
            # Instrucoes
            show_instructions()
        
        elif choice == '5':
            # Sair
            print("\nAte logo!")
            break
        
        else:
            print("Opcao invalida!")


if __name__ == "__main__":
    main()
