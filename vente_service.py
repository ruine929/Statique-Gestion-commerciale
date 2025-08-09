from models.vente import Vente
from models.produit import Produit
from models.client import Client
from services.stock_service import StockService
from app import db
from datetime import datetime, timedelta

class VenteService:
    """Service pour la gestion des ventes"""
    
    @staticmethod
    def create_vente(produit_id, client_id, quantite, prix_unitaire=None, remise=0.0, notes=None):
        """Crée une nouvelle vente"""
        produit = Produit.query.get(produit_id)
        client = Client.query.get(client_id)
        
        if not produit or not client:
            return None, "Produit ou client non trouvé"
        
        if produit.stock_actuel < quantite:
            return None, f"Stock insuffisant. Stock disponible: {produit.stock_actuel}"
        
        # Utiliser le prix de vente du produit si pas spécifié
        if prix_unitaire is None:
            prix_unitaire = produit.prix_vente
        
        # Créer la vente
        vente = Vente()
        vente.produit_id = produit_id
        vente.client_id = client_id
        vente.quantite = quantite
        vente.prix_unitaire = prix_unitaire
        vente.remise = remise
        vente.notes = notes
        
        # Calculer le montant total
        vente.calculer_montant_total()
        
        try:
            # Sauvegarder la vente
            db.session.add(vente)
            
            # Mettre à jour le stock
            produit.stock_actuel -= quantite
            
            db.session.commit()
            return vente, "Vente créée avec succès"
            
        except Exception as e:
            db.session.rollback()
            return None, f"Erreur lors de la création de la vente: {str(e)}"
    
    @staticmethod
    def get_ventes_by_period(date_debut=None, date_fin=None):
        """Retourne les ventes pour une période donnée"""
        query = Vente.query
        
        if date_debut:
            query = query.filter(Vente.date_vente >= date_debut)
        if date_fin:
            query = query.filter(Vente.date_vente <= date_fin)
        
        return query.order_by(db.desc(Vente.date_vente)).all()
    
    @staticmethod
    def get_ventes_by_client(client_id):
        """Retourne les ventes d'un client"""
        return Vente.query.filter_by(client_id=client_id).order_by(db.desc(Vente.date_vente)).all()
    
    @staticmethod
    def get_ventes_by_product(produit_id):
        """Retourne les ventes d'un produit"""
        return Vente.query.filter_by(produit_id=produit_id).order_by(db.desc(Vente.date_vente)).all()
    
    @staticmethod
    def calculate_daily_sales(days=7):
        """Calcule les ventes quotidiennes sur les derniers jours"""
        date_debut = datetime.utcnow() - timedelta(days=days)
        
        ventes = Vente.query.filter(
            Vente.date_vente >= date_debut,
            Vente.statut == 'completed'
        ).all()
        
        sales_by_day = {}
        for i in range(days + 1):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            sales_by_day[date.isoformat()] = {'montant': 0, 'quantite': 0, 'transactions': 0}
        
        for vente in ventes:
            date_key = vente.date_vente.date().isoformat()
            if date_key in sales_by_day:
                sales_by_day[date_key]['montant'] += vente.montant_total
                sales_by_day[date_key]['quantite'] += vente.quantite
                sales_by_day[date_key]['transactions'] += 1
        
        return sales_by_day
    
    @staticmethod
    def get_top_selling_products(limit=10, days=30):
        """Retourne les produits les plus vendus"""
        date_debut = datetime.utcnow() - timedelta(days=days)
        
        # Agrégation des ventes par produit
        results = db.session.query(
            Vente.produit_id,
            db.func.sum(Vente.quantite).label('total_quantite'),
            db.func.sum(Vente.montant_total).label('total_montant'),
            db.func.count(Vente.id).label('nombre_ventes')
        ).filter(
            Vente.date_vente >= date_debut,
            Vente.statut == 'completed'
        ).group_by(Vente.produit_id).order_by(db.desc('total_quantite')).limit(limit).all()
        
        top_products = []
        for result in results:
            produit = Produit.query.get(result.produit_id)
            if produit:
                top_products.append({
                    'produit': produit,
                    'total_quantite': result.total_quantite,
                    'total_montant': result.total_montant,
                    'nombre_ventes': result.nombre_ventes
                })
        
        return top_products
    
    @staticmethod
    def get_sales_summary(date_debut=None, date_fin=None):
        """Retourne un résumé des ventes"""
        query = Vente.query.filter_by(statut='completed')
        
        if date_debut:
            query = query.filter(Vente.date_vente >= date_debut)
        if date_fin:
            query = query.filter(Vente.date_vente <= date_fin)
        
        ventes = query.all()
        
        total_ventes = len(ventes)
        montant_total = sum(vente.montant_total for vente in ventes)
        quantite_totale = sum(vente.quantite for vente in ventes)
        benefice_total = sum(vente.benefice for vente in ventes)
        
        # Calcul du panier moyen
        panier_moyen = montant_total / total_ventes if total_ventes > 0 else 0
        
        return {
            'total_ventes': total_ventes,
            'montant_total': montant_total,
            'quantite_totale': quantite_totale,
            'benefice_total': benefice_total,
            'panier_moyen': panier_moyen
        }
    
    @staticmethod
    def cancel_vente(vente_id, reason=None):
        """Annule une vente et remet le stock"""
        vente = Vente.query.get(vente_id)
        if not vente:
            return False, "Vente non trouvée"
        
        if vente.statut == 'cancelled':
            return False, "Vente déjà annulée"
        
        try:
            # Remettre le stock
            produit = vente.produit_rel
            produit.stock_actuel += vente.quantite
            
            # Marquer comme annulée
            vente.statut = 'cancelled'
            if reason:
                vente.notes = f"Annulée: {reason}. {vente.notes or ''}"
            
            db.session.commit()
            return True, "Vente annulée avec succès"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de l'annulation: {str(e)}"
