from app import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Produit(db.Model):
    __tablename__ = 'produits'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    prix_achat = db.Column(db.Float, nullable=False)  # Prix en Ariary (MGA)
    prix_vente = db.Column(db.Float, nullable=False)  # Prix en Ariary (MGA)
    stock_initial = db.Column(db.Integer, default=0)
    stock_actuel = db.Column(db.Integer, default=0)
    stock_minimum = db.Column(db.Integer, default=5)  # Seuil d'alerte
    taux_marge = db.Column(db.Float, default=0.0)  # Marge en pourcentage
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)
    
    # Relations
    ventes = relationship('Vente', backref='produit_rel', lazy='dynamic')
    achats = relationship('Achat', backref='produit_rel', lazy='dynamic')
    
    def __repr__(self):
        return f'<Produit {self.nom}>'
    
    @property
    def marge_unitaire(self):
        """Calcule la marge unitaire"""
        return self.prix_vente - self.prix_achat
    
    @property
    def pourcentage_marge(self):
        """Calcule le pourcentage de marge"""
        if self.prix_achat > 0:
            return ((self.prix_vente - self.prix_achat) / self.prix_achat) * 100
        return 0
    
    @property
    def stock_alerte(self):
        """Vérifie si le stock est en alerte"""
        return self.stock_actuel <= self.stock_minimum
    
    @property
    def valeur_stock(self):
        """Calcule la valeur du stock actuel au prix d'achat"""
        return self.stock_actuel * self.prix_achat
    
    @property
    def valeur_stock_vente(self):
        """Calcule la valeur du stock actuel au prix de vente"""
        return self.stock_actuel * self.prix_vente
    
    @property
    def total_vendu(self):
        """Calcule la quantité totale vendue"""
        return sum(vente.quantite for vente in self.ventes)
    
    @property
    def chiffre_affaires(self):
        """Calcule le chiffre d'affaires généré par ce produit"""
        return sum(vente.montant_total for vente in self.ventes)
    
    def ajuster_stock(self, quantite, operation='vente'):
        """Ajuste le stock selon l'opération (vente ou achat)"""
        if operation == 'vente':
            if self.stock_actuel >= quantite:
                self.stock_actuel -= quantite
                return True
            return False
        elif operation == 'achat':
            self.stock_actuel += quantite
            return True
        return False
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'nom': self.nom,
            'description': self.description,
            'prix_achat': self.prix_achat,
            'prix_vente': self.prix_vente,
            'stock_initial': self.stock_initial,
            'stock_actuel': self.stock_actuel,
            'stock_minimum': self.stock_minimum,
            'taux_marge': self.taux_marge,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'actif': self.actif,
            'marge_unitaire': self.marge_unitaire,
            'pourcentage_marge': self.pourcentage_marge,
            'stock_alerte': self.stock_alerte,
            'valeur_stock': self.valeur_stock,
            'total_vendu': self.total_vendu,
            'chiffre_affaires': self.chiffre_affaires
        }
