from app import db
from datetime import datetime

class Vente(db.Model):
    __tablename__ = 'ventes'
    
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)  # Prix en Ariary (MGA)
    remise = db.Column(db.Float, default=0.0)  # Remise en pourcentage
    montant_remise = db.Column(db.Float, default=0.0)  # Montant de la remise
    montant_total = db.Column(db.Float, nullable=False)  # Montant total en Ariary
    date_vente = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='completed')  # completed, cancelled, pending
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Vente {self.id} - {self.quantite} unités>'
    
    @property
    def montant_brut(self):
        """Calcule le montant brut avant remise"""
        return self.quantite * self.prix_unitaire
    
    @property
    def benefice(self):
        """Calcule le bénéfice de cette vente"""
        from models.produit import Produit
        produit = Produit.query.get(self.produit_id)
        if produit:
            cout_achat = self.quantite * produit.prix_achat
            return self.montant_total - cout_achat
        return 0
    
    def calculer_montant_total(self):
        """Calcule et met à jour le montant total avec remise"""
        montant_brut = self.quantite * self.prix_unitaire
        self.montant_remise = montant_brut * (self.remise / 100)
        self.montant_total = montant_brut - self.montant_remise
        return self.montant_total
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'produit_id': self.produit_id,
            'client_id': self.client_id,
            'quantite': self.quantite,
            'prix_unitaire': self.prix_unitaire,
            'remise': self.remise,
            'montant_remise': self.montant_remise,
            'montant_total': self.montant_total,
            'date_vente': self.date_vente.isoformat() if self.date_vente else None,
            'statut': self.statut,
            'notes': self.notes,
            'montant_brut': self.montant_brut,
            'benefice': self.benefice
        }
