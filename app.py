import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///gestion_commerciale.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'  # type: ignore

# Import models to ensure tables are created
from models.client import Client
from models.produit import Produit  
from models.vente import Vente
from models.achat import Achat

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(int(user_id))

# Register blueprints
from google_auth import google_auth
from routes.main_routes import main_bp
from routes.produit_routes import produit_bp
from routes.vente_routes import vente_bp
from routes.achat_routes import achat_bp
from routes.client_routes import client_bp
from routes.statistique_routes import statistique_bp

app.register_blueprint(google_auth)
app.register_blueprint(main_bp)
app.register_blueprint(produit_bp)
app.register_blueprint(vente_bp)
app.register_blueprint(achat_bp)
app.register_blueprint(client_bp)
app.register_blueprint(statistique_bp)

with app.app_context():
    db.create_all()
