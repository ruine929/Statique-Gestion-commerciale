from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import relationship

class Client(UserMixin, db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.Text)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    ventes = relationship('Vente', backref='client_rel', lazy='dynamic')
    
    def __repr__(self):
        return f'<Client {self.nom}>'
    
    @property
    def total_achats(self):
        """Calcule le montant total des achats du client"""
        return sum(vente.montant_total for vente in self.ventes)
    
    @property
    def nombre_achats(self):
        """Retourne le nombre d'achats du client"""
        return self.ventes.count()
    
    @property
    def dernier_achat(self):
        """Retourne la date du dernier achat"""
        derniere_vente = self.ventes.order_by(db.desc('date_vente')).first()
        return derniere_vente.date_vente if derniere_vente else None
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'nom': self.nom,
            'email': self.email,
            'telephone': self.telephone,
            'adresse': self.adresse,
            'date_inscription': self.date_inscription.isoformat() if self.date_inscription else None,
            'total_achats': self.total_achats,
            'nombre_achats': self.nombre_achats,
            'dernier_achat': self.dernier_achat.isoformat() if self.dernier_achat else None
        }
