import os

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///gestion_commerciale.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google OAuth configuration
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
    
    # Application settings
    CURRENCY = 'MGA'  # Ariary
    LOW_STOCK_THRESHOLD = 5
    
    # Pagination
    POSTS_PER_PAGE = 20
