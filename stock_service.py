from models.produit import Produit
from models.vente import Vente
from models.achat import Achat
from app import db
from datetime import datetime

class StockService:
    """Service pour la gestion des stocks"""
    
    @staticmethod
    def get_products_with_low_stock():
        """Retourne les produits avec un stock faible"""
        return Produit.query.filter(
            Produit.stock_actuel <= Produit.stock_minimum,
            Produit.actif == True
        ).all()
    
    @staticmethod
    def get_stock_summary():
        """Retourne un résumé du stock global"""
        produits = Produit.query.filter_by(actif=True).all()
        
        total_produits = len(produits)
        total_stock_unites = sum(p.stock_actuel for p in produits)
        total_valeur_achat = sum(p.valeur_stock for p in produits)
        total_valeur_vente = sum(p.valeur_stock_vente for p in produits)
        produits_stock_faible = len([p for p in produits if p.stock_alerte])
        
        return {
            'total_produits': total_produits,
            'total_stock_unites': total_stock_unites,
            'total_valeur_achat': total_valeur_achat,
            'total_valeur_vente': total_valeur_vente,
            'produits_stock_faible': produits_stock_faible,
            'pourcentage_stock_faible': (produits_stock_faible / total_produits * 100) if total_produits > 0 else 0
        }
    
    @staticmethod
    def update_stock_from_sale(produit_id, quantite):
        """Met à jour le stock après une vente"""
        produit = Produit.query.get(produit_id)
        if produit and produit.stock_actuel >= quantite:
            produit.stock_actuel -= quantite
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def update_stock_from_purchase(produit_id, quantite):
        """Met à jour le stock après un achat"""
        produit = Produit.query.get(produit_id)
        if produit:
            produit.stock_actuel += quantite
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_stock_movements(produit_id=None, limit=50):
        """Retourne l'historique des mouvements de stock"""
        movements = []
        
        # Récupérer les ventes
        ventes_query = Vente.query
        if produit_id:
            ventes_query = ventes_query.filter_by(produit_id=produit_id)
        
        ventes = ventes_query.order_by(db.desc(Vente.date_vente)).limit(limit).all()
        
        for vente in ventes:
            movements.append({
                'type': 'vente',
                'produit_nom': vente.produit_rel.nom,
                'quantite': -vente.quantite,  # Négatif pour les sorties
                'date': vente.date_vente,
                'reference': f"Vente #{vente.id}",
                'client': vente.client_rel.nom if vente.client_rel else "N/A"
            })
        
        # Récupérer les achats
        achats_query = Achat.query
        if produit_id:
            achats_query = achats_query.filter_by(produit_id=produit_id)
        
        achats = achats_query.order_by(db.desc(Achat.date_achat)).limit(limit).all()
        
        for achat in achats:
            movements.append({
                'type': 'achat',
                'produit_nom': achat.produit_rel.nom,
                'quantite': achat.quantite,  # Positif pour les entrées
                'date': achat.date_achat,
                'reference': f"Achat #{achat.id}",
                'fournisseur': achat.fournisseur or "N/A"
            })
        
        # Trier par date décroissante
        movements.sort(key=lambda x: x['date'], reverse=True)
        
        return movements[:limit]
    
    @staticmethod
    def calculate_stock_turnover(produit_id, days=30):
        """Calcule la rotation du stock pour un produit"""
        from datetime import timedelta
        
        produit = Produit.query.get(produit_id)
        if not produit:
            return 0
        
        date_debut = datetime.utcnow() - timedelta(days=days)
        
        ventes = Vente.query.filter(
            Vente.produit_id == produit_id,
            Vente.date_vente >= date_debut,
            Vente.statut == 'completed'
        ).all()
        
        quantite_vendue = sum(vente.quantite for vente in ventes)
        stock_moyen = (produit.stock_initial + produit.stock_actuel) / 2
        
        if stock_moyen > 0:
            return quantite_vendue / stock_moyen
        return 0
