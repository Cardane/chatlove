"""
Migration script to add 'role' column to admins table
"""

from database import SessionLocal, Admin, engine
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    
    try:
        # Add role column if it doesn't exist
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(admins)"))
            columns = [row[1] for row in result]
            
            if 'role' not in columns:
                print("[INFO] Adding 'role' column to admins table...")
                conn.execute(text("ALTER TABLE admins ADD COLUMN role VARCHAR DEFAULT 'viewer'"))
                conn.commit()
                print("[OK] Column 'role' added successfully!")
            else:
                print("[INFO] Column 'role' already exists")
        
        # Update existing admins
        print("[INFO] Updating admin roles...")
        
        # Set alancardane as master
        alan = db.query(Admin).filter(Admin.username == "alancardane").first()
        if alan:
            alan.role = "master"
            print("[OK] alancardane set as master")
        
        # Set rocha as viewer
        rocha = db.query(Admin).filter(Admin.username == "rocha").first()
        if rocha:
            rocha.role = "viewer"
            print("[OK] rocha set as viewer")
        
        db.commit()
        print("[SUCCESS] Migration completed!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting migration...")
    migrate()
