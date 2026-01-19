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
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="licenses")
    usage_logs = relationship("UsageLog", back_populates="license")


class UsageLog(Base):
    """Track usage and tokens saved"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"))
    
    # Usage data
    tokens_saved = Column(Float, default=0.0)
    request_count = Column(Integer, default=1)
    message_length = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    license = relationship("License", back_populates="usage_logs")


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
