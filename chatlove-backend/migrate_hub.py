"""
Migração para adicionar suporte ao Hub de Contas
Adiciona tabelas: hub_accounts, project_mappings
Adiciona colunas em usage_logs: hub_account_id, original_project_id, hub_project_id
"""

import sqlite3
from datetime import datetime

DB_PATH = "chatlove.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("MIGRAÇÃO: Hub de Contas")
    print("=" * 60)
    
    # ========================================
    # 1. CRIAR TABELA: hub_accounts
    # ========================================
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hub_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                session_token VARCHAR NOT NULL,
                credits_remaining FLOAT DEFAULT 0.0,
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                last_used_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Tabela 'hub_accounts' criada")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("[INFO] Tabela 'hub_accounts' ja existe")
        else:
            print(f"[ERRO] Erro ao criar 'hub_accounts': {e}")
    
    # ========================================
    # 2. CRIAR TABELA: project_mappings
    # ========================================
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_project_id VARCHAR NOT NULL,
                hub_project_id VARCHAR NOT NULL,
                hub_account_id INTEGER NOT NULL,
                project_name VARCHAR NULL,
                sync_enabled BOOLEAN DEFAULT 0,
                last_synced_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hub_account_id) REFERENCES hub_accounts(id)
            )
        """)
        print("[OK] Tabela 'project_mappings' criada")
        
        # Criar índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_mappings_original 
            ON project_mappings(original_project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_mappings_hub 
            ON project_mappings(hub_project_id)
        """)
        print("[OK] Indices criados para 'project_mappings'")
        
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("[INFO] Tabela 'project_mappings' ja existe")
        else:
            print(f"[ERRO] Erro ao criar 'project_mappings': {e}")
    
    # ========================================
    # 3. ADICIONAR COLUNAS EM usage_logs
    # ========================================
    
    # 3.1. hub_account_id
    try:
        cursor.execute("ALTER TABLE usage_logs ADD COLUMN hub_account_id INTEGER NULL")
        print("[OK] Coluna 'hub_account_id' adicionada em usage_logs")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[INFO] Coluna 'hub_account_id' ja existe")
        else:
            print(f"[ERRO] Erro: {e}")
    
    # 3.2. original_project_id
    try:
        cursor.execute("ALTER TABLE usage_logs ADD COLUMN original_project_id VARCHAR NULL")
        print("[OK] Coluna 'original_project_id' adicionada em usage_logs")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[INFO] Coluna 'original_project_id' ja existe")
        else:
            print(f"[ERRO] Erro: {e}")
    
    # 3.3. hub_project_id
    try:
        cursor.execute("ALTER TABLE usage_logs ADD COLUMN hub_project_id VARCHAR NULL")
        print("[OK] Coluna 'hub_project_id' adicionada em usage_logs")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[INFO] Coluna 'hub_project_id' ja existe")
        else:
            print(f"[ERRO] Erro: {e}")
    
    # ========================================
    # 4. COMMIT E FECHAR
    # ========================================
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print("[OK] MIGRACAO CONCLUIDA COM SUCESSO!")
    print("=" * 60)
    print("\nPróximos passos:")
    print("1. Reiniciar backend: python main.py")
    print("2. Adicionar conta hub via admin panel")
    print("3. Testar proxy hub")
    print()


if __name__ == "__main__":
    migrate()