from app import db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

def get_database_url():
    """Get database URL from environment or use SQLite as fallback"""
    return os.environ.get('DATABASE_URL', 'sqlite:///gestion_commerciale.db')

def init_database():
    """Initialize database with all tables"""
    with db.app.app_context():
        db.create_all()
        print("Database initialized successfully")

def reset_database():
    """Reset database by dropping and recreating all tables"""
    with db.app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully")

class DatabaseManager:
    """Database manager for handling transactions"""
    
    @staticmethod
    def save(obj):
        """Save object to database"""
        try:
            db.session.add(obj)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error saving to database: {e}")
            return False
    
    @staticmethod
    def delete(obj):
        """Delete object from database"""
        try:
            db.session.delete(obj)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting from database: {e}")
            return False
    
    @staticmethod
    def commit():
        """Commit current session"""
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error committing to database: {e}")
            return False
