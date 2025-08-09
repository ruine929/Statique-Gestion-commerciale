from app import db
from datetime import datetime

class Achat(db.Model):
    __tablename__ = 'achats'
    
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)  # Prix d'achat en Ariary (MGA)
    montant_total = db.Column(db.Float, nullable=False)  # Montant total en Ariary
    fournisseur = db.Column(db.String(100))
    date_achat = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='completed')  # completed, cancelled, pending
    notes = db.Column(db.Text)
    numero_facture = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Achat {self.id} - {self.quantite} unités>'
    
    def calculer_montant_total(self):
        """Calcule et met à jour le montant total"""
        self.montant_total = self.quantite * self.prix_unitaire
        return self.montant_total
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'produit_id': self.produit_id,
            'quantite': self.quantite,
            'prix_unitaire': self.prix_unitaire,
            'montant_total': self.montant_total,
            'fournisseur': self.fournisseur,
            'date_achat': self.date_achat.isoformat() if self.date_achat else None,
            'statut': self.statut,
            'notes': self.notes,
            'numero_facture': self.numero_facture
        }
