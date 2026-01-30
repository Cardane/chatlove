"""
ChatLove - Database Models and Setup
SQLite database for license management
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./chatlove.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =============================================================================
# MODELS
# =============================================================================

class Admin(Base):
    """Admin user for panel access"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="viewer")  # "master" or "viewer"
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """End user who purchases license"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    licenses = relationship("License", back_populates="user")


class License(Base):
    """License key for extension activation"""
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    license_key = Column(String, unique=True, index=True)
    hardware_id = Column(String, nullable=True)  # Unique device fingerprint
    
    # Status
    is_active = Column(Boolean, default=True)
    is_used = Column(Boolean, default=False)  # Once used, cannot be reused
    
    # License Type and Expiration
    license_type = Column(String, default="full")  # "trial" or "full"
    expires_at = Column(DateTime, nullable=True)   # Expiration date for trial licenses
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="licenses")
    usage_logs = relationship("UsageLog", back_populates="license")
    
    def is_expired(self):
        """Check if license is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


class HubAccount(Base):
    """Conta do hub com créditos para proxy"""
    __tablename__ = "hub_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)                # Nome amigável (ex: "Hub Account 1")
    email = Column(String, unique=True, index=True)  # Email da conta Lovable
    session_token = Column(String)                   # Token Bearer do Lovable
    credits_remaining = Column(Float, default=0.0)   # Créditos estimados restantes
    is_active = Column(Boolean, default=True)        # Se está disponível para uso
    priority = Column(Integer, default=0)            # 0 = maior prioridade (para futuro)
    
    # Estatísticas
    total_requests = Column(Integer, default=0)      # Total de requisições
    last_used_at = Column(DateTime, nullable=True)   # Última vez usada
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_mappings = relationship("ProjectMapping", back_populates="hub_account")
    usage_logs = relationship("UsageLog", back_populates="hub_account", foreign_keys="UsageLog.hub_account_id")


class ProjectMapping(Base):
    """Mapeia projetos originais para projetos equivalentes no hub"""
    __tablename__ = "project_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # IDs dos projetos
    original_project_id = Column(String, index=True)   # Projeto da conta do usuário
    hub_project_id = Column(String, index=True)        # Projeto criado na conta hub
    
    # Relacionamento
    hub_account_id = Column(Integer, ForeignKey("hub_accounts.id"))
    
    # Metadados
    project_name = Column(String, nullable=True)       # Nome do projeto (cache)
    sync_enabled = Column(Boolean, default=False)      # Se sincronização está ativa
    last_synced_at = Column(DateTime, nullable=True)   # Última sincronização
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    hub_account = relationship("HubAccount", back_populates="project_mappings")


class UsageLog(Base):
    """Track usage and tokens saved"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"))
    
    # ===== CAMPOS ADICIONADOS PARA HUB =====
    hub_account_id = Column(Integer, ForeignKey("hub_accounts.id"), nullable=True)
    original_project_id = Column(String, nullable=True)  # Projeto do usuário
    hub_project_id = Column(String, nullable=True)       # Projeto usado no hub
    # =======================================
    
    # Usage data
    tokens_saved = Column(Float, default=0.0)
    request_count = Column(Integer, default=1)
    message_length = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    license = relationship("License", back_populates="usage_logs")
    hub_account = relationship("HubAccount", back_populates="usage_logs", foreign_keys=[hub_account_id])


# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized successfully!")


def create_default_admin():
    """Create default admin user if not exists"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(Admin).filter(Admin.username == "admin").first()
        
        if not admin:
            # Create default admin
            admin = Admin(
                username="admin",
                password_hash=pwd_context.hash("admin123")  # Change this!
            )
            db.add(admin)
            db.commit()
            print("[OK] Default admin created!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   [WARNING] CHANGE THIS PASSWORD IMMEDIATELY!")
        else:
            print("[INFO] Admin already exists")
    
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing ChatLove Database...")
    init_db()
    create_default_admin()
    print("Done!")
