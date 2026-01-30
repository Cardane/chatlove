"""
ChatLove Terminal Commander - Solução Híbrida Final
Combina extensão existente + servidor Python + terminal interativo
"""

import sys
import os
import json
import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Configurar encoding para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

import requests
from cryptography.fernet import Fernet
import keyring


class LovableTerminalCommander:
    """Terminal interativo para enviar comandos via extensão"""
    
    def __init__(self):
        self.app_dir = Path.home() / ".chatlove"
        self.config_file = self.app_dir / "config.json"
        self.commands_file = self.app_dir / "commands_history.json"
        
        # Criar diretórios
        self.app_dir.mkdir(exist_ok=True)
        
        # Configurações
        self.backend_url = "http://127.0.0.1:8000"
        self.extension_proxy_url = f"{self.backend_url}/api/lovable-proxy"
        
        # Chave de criptografia
        self.cipher_key = self._get_or_create_key()
        self.cipher = Fernet(self.cipher_key)
        
        # Dados
        self.accounts = self._load_accounts()
        self.commands_history = self._load_commands_history()
        
        # Estado
        self.current_project_id = None
        self.current_account = None
        self.session_token = None
        
        print("ChatLove Terminal Commander iniciado!")
        print("Solução híbrida: Terminal + Extensão + Backend")
    
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
    
    def _load_commands_history(self) -> List[Dict]:
        """Carrega histórico de comandos"""
        try:
            if self.commands_file.exists():
                with open(self.commands_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        
        return []
    
    def _save_commands_history(self):
        """Salva histórico de comandos"""
        try:
            with open(self.commands_file, 'w', encoding='utf-8') as f:
                json.dump(self.commands_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def add_account(self, email: str, password: str, license_key: str) -> bool:
        """Adiciona nova conta"""
        try:
            # Criptografar senha
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            
            # Verificar se já existe
            for account in self.accounts:
                if account['email'] == email:
                    account['password'] = encrypted_password
                    account['license_key'] = license_key
                    account['last_login'] = datetime.now().isoformat()
                    self._save_accounts()
                    return True
            
            # Adicionar nova conta
            self.accounts.append({
                'email': email,
                'password': encrypted_password,
                'license_key': license_key,
                'active': len(self.accounts) == 0,
                'last_login': datetime.now().isoformat()
            })
            
            self._save_accounts()
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar conta: {e}")
            return False
    
    def get_active_account(self):
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
        self.current_account = self.get_active_account()
        print(f"Conta ativa: {email}")
    
    def check_backend_status(self) -> bool:
        """Verifica se o backend está rodando"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_extension_status(self) -> bool:
        """Verifica se a extensão está funcionando"""
        try:
            # Tentar fazer uma requisição de teste
            response = requests.post(
                self.extension_proxy_url,
                json={
                    "license_key": "test",
                    "project_id": "test",
                    "message": "test",
                    "session_token": "test"
                },
                timeout=5
            )
            # Se chegou até aqui, o endpoint existe
            return True
        except requests.exceptions.ConnectionError:
            return False
        except:
            # Outros erros (como 400, 403) indicam que o endpoint existe
            return True
    
    def send_command(self, message: str) -> Dict:
        """Envia comando via extensão/backend"""
        if not self.current_account:
            return {"success": False, "error": "Nenhuma conta ativa"}
        
        if not self.current_project_id:
            return {"success": False, "error": "Nenhum projeto selecionado"}
        
        try:
            # Preparar dados
            data = {
                "license_key": self.current_account['license_key'],
                "project_id": self.current_project_id,
                "message": message,
                "session_token": self.session_token or "auto"
            }
            
            print(f"Enviando comando: {message[:50]}...")
            
            # Enviar via backend/extensão
            response = requests.post(
                self.extension_proxy_url,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Salvar no histórico
                self.commands_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "account": self.current_account['email'],
                    "project_id": self.current_project_id,
                    "command": message,
                    "success": result.get('success', False),
                    "response": result.get('message', '')
                })
                self._save_commands_history()
                
                return result
            else:
                error_msg = f"Erro HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
                
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Backend não está rodando. Execute: python main.py"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout - comando pode ter sido enviado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def show_status(self):
        """Mostra status do sistema"""
        print("\n" + "="*60)
        print("STATUS DO SISTEMA")
        print("="*60)
        
        # Backend
        backend_status = "✅ Online" if self.check_backend_status() else "❌ Offline"
        print(f"Backend (Python): {backend_status}")
        
        # Extensão
        extension_status = "✅ Instalada" if self.check_extension_status() else "❌ Não encontrada"
        print(f"Extensão (Chrome): {extension_status}")
        
        # Conta ativa
        if self.current_account:
            print(f"Conta ativa: {self.current_account['email']}")
        else:
            print("Conta ativa: Nenhuma")
        
        # Projeto
        if self.current_project_id:
            print(f"Projeto: {self.current_project_id}")
        else:
            print("Projeto: Nenhum selecionado")
        
        # Histórico
        print(f"Comandos executados: {len(self.commands_history)}")
        
        print("="*60)
    
    def show_accounts(self):
        """Lista contas"""
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
    
    def show_history(self, limit: int = 10):
        """Mostra histórico de comandos"""
        if not self.commands_history:
            print("Nenhum comando executado ainda.")
            return
        
        print(f"\nÚltimos {limit} comandos:")
        for cmd in self.commands_history[-limit:]:
            timestamp = cmd['timestamp'][:19].replace('T', ' ')
            status = "✅" if cmd['success'] else "❌"
            command = cmd['command'][:50] + "..." if len(cmd['command']) > 50 else cmd['command']
            
            print(f"{timestamp} {status} {command}")
    
    def interactive_mode(self):
        """Modo interativo principal"""
        print("\n" + "="*60)
        print("CHATLOVE TERMINAL COMMANDER")
        print("Solução híbrida: Terminal + Extensão + Backend")
        print("="*60)
        
        # Verificar pré-requisitos
        if not self.check_backend_status():
            print("❌ Backend não está rodando!")
            print("Execute em outro terminal: cd chatlove-backend && python main.py")
            print("Continuando mesmo assim...")
        
        if not self.check_extension_status():
            print("❌ Extensão não encontrada!")
            print("Instale a extensão chatlove-proxy-extension no Chrome")
            print("Continuando mesmo assim...")
        
        # Selecionar conta se necessário
        if not self.current_account:
            if self.accounts:
                self.current_account = self.get_active_account()
                print(f"Usando conta: {self.current_account['email']}")
            else:
                print("Nenhuma conta cadastrada. Use 'add_account' para adicionar.")
        
        print("\nComandos disponíveis:")
        print("  send <mensagem>     - Enviar comando para Lovable")
        print("  project <id>        - Definir projeto ativo")
        print("  account <email>     - Trocar conta ativa")
        print("  add_account         - Adicionar nova conta")
        print("  status              - Ver status do sistema")
        print("  accounts            - Listar contas")
        print("  history             - Ver histórico de comandos")
        print("  help                - Mostrar ajuda")
        print("  quit                - Sair")
        print("\nExemplo: send Crie um botão azul com texto branco")
        
        while True:
            try:
                # Prompt
                account_name = self.current_account['email'][:20] if self.current_account else "no-account"
                project_name = self.current_project_id[:8] if self.current_project_id else "no-project"
                
                command = input(f"\n[{account_name}:{project_name}] > ").strip()
                
                if not command:
                    continue
                
                # Processar comando
                if command.lower() in ['quit', 'exit', 'q']:
                    print("Até logo!")
                    break
                
                elif command.lower() in ['help', 'h']:
                    self._show_help()
                
                elif command.lower() == 'status':
                    self.show_status()
                
                elif command.lower() == 'accounts':
                    self.show_accounts()
                
                elif command.lower() == 'history':
                    self.show_history()
                
                elif command.lower() == 'add_account':
                    self._add_account_interactive()
                
                elif command.startswith('project '):
                    project_id = command[8:].strip()
                    self.current_project_id = project_id
                    print(f"Projeto definido: {project_id}")
                
                elif command.startswith('account '):
                    email = command[8:].strip()
                    self.set_active_account(email)
                
                elif command.startswith('send '):
                    message = command[5:].strip()
                    if not message:
                        print("Erro: Mensagem vazia")
                        continue
                    
                    result = self.send_command(message)
                    
                    if result['success']:
                        print("✅ Comando enviado com sucesso!")
                        if 'message' in result:
                            print(f"Resposta: {result['message']}")
                    else:
                        print(f"❌ Erro: {result['error']}")
                
                else:
                    # Assumir que é um comando send
                    result = self.send_command(command)
                    
                    if result['success']:
                        print("✅ Comando enviado com sucesso!")
                        if 'message' in result:
                            print(f"Resposta: {result['message']}")
                    else:
                        print(f"❌ Erro: {result['error']}")
            
            except KeyboardInterrupt:
                print("\n\nUse 'quit' para sair.")
            except EOFError:
                print("\nAté logo!")
                break
            except Exception as e:
                print(f"Erro: {e}")
    
    def _show_help(self):
        """Mostra ajuda detalhada"""
        print("\n" + "="*60)
        print("AJUDA - CHATLOVE TERMINAL COMMANDER")
        print("="*60)
        print()
        print("CONFIGURAÇÃO INICIAL:")
        print("1. Execute o backend: cd chatlove-backend && python main.py")
        print("2. Instale a extensão chatlove-proxy-extension no Chrome")
        print("3. Ative a licença na extensão")
        print("4. Abra um projeto no Lovable.dev")
        print("5. Use este terminal para enviar comandos")
        print()
        print("COMANDOS:")
        print("  send <mensagem>     - Enviar comando para Lovable")
        print("  project <id>        - Definir projeto ativo (copie da URL)")
        print("  account <email>     - Trocar conta ativa")
        print("  add_account         - Adicionar nova conta")
        print("  status              - Ver status do sistema")
        print("  accounts            - Listar contas")
        print("  history             - Ver histórico de comandos")
        print("  help                - Mostrar esta ajuda")
        print("  quit                - Sair")
        print()
        print("EXEMPLOS:")
        print("  send Crie um botão azul com texto branco")
        print("  send Adicione um formulário de contato")
        print("  send Mude a cor de fundo para gradiente")
        print("  project abc123-def456-ghi789")
        print("  account usuario@email.com")
        print()
        print("FLUXO TÍPICO:")
        print("1. add_account (primeira vez)")
        print("2. Abrir projeto no Lovable.dev")
        print("3. project <id_do_projeto>")
        print("4. send <seu_comando>")
        print("5. Ver resultado no Lovable")
        print("="*60)
    
    def _add_account_interactive(self):
        """Adiciona conta interativamente"""
        print("\nAdicionar Nova Conta")
        
        email = input("Email: ").strip()
        if not email:
            print("Email não pode estar vazio!")
            return
        
        import getpass
        password = getpass.getpass("Senha: ")
        if not password:
            print("Senha não pode estar vazia!")
            return
        
        license_key = input("Chave de licença: ").strip()
        if not license_key:
            print("Chave de licença não pode estar vazia!")
            return
        
        if self.add_account(email, password, license_key):
            print(f"✅ Conta {email} adicionada com sucesso!")
            if not self.current_account:
                self.current_account = self.get_active_account()
        else:
            print("❌ Erro ao adicionar conta!")


def main():
    """Função principal"""
    commander = LovableTerminalCommander()
    
    # Verificar argumentos da linha de comando
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        
        if command == "status":
            commander.show_status()
        elif command == "accounts":
            commander.show_accounts()
        elif command == "history":
            commander.show_history()
        elif command.startswith("send "):
            message = command[5:]
            result = commander.send_command(message)
            if result['success']:
                print("✅ Comando enviado!")
            else:
                print(f"❌ Erro: {result['error']}")
        else:
            print(f"Comando não reconhecido: {command}")
    else:
        # Modo interativo
        commander.interactive_mode()


if __name__ == "__main__":
    main()
