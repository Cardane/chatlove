"""
Script para migrar o banco de dados adicionando novos campos
"""
import sqlite3

# Conectar ao banco
conn = sqlite3.connect('chatlove.db')
cursor = conn.cursor()

try:
    # Adicionar coluna license_type
    cursor.execute("ALTER TABLE licenses ADD COLUMN license_type TEXT DEFAULT 'full'")
    print("[OK] Coluna 'license_type' adicionada")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("[INFO] Coluna 'license_type' ja existe")
    else:
        print(f"[ERRO] Erro ao adicionar 'license_type': {e}")

try:
    # Adicionar coluna expires_at
    cursor.execute("ALTER TABLE licenses ADD COLUMN expires_at TIMESTAMP NULL")
    print("[OK] Coluna 'expires_at' adicionada")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("[INFO] Coluna 'expires_at' ja existe")
    else:
        print(f"[ERRO] Erro ao adicionar 'expires_at': {e}")

# Commit e fechar
conn.commit()
conn.close()

print("\n[SUCESSO] Migracao concluida!")
print("Reinicie o backend: python main.py")
