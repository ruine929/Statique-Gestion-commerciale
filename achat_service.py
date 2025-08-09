from models.achat import Achat
from models.produit import Produit
from app import db
from datetime import datetime, timedelta

class AchatService:
    """Service pour la gestion des achats"""
    
    @staticmethod
    def create_achat(produit_id, quantite, prix_unitaire, fournisseur=None, notes=None, numero_facture=None):
        """Crée un nouvel achat"""
        produit = Produit.query.get(produit_id)
        
        if not produit:
            return None, "Produit non trouvé"
        
        # Créer l'achat
        achat = Achat()
        achat.produit_id = produit_id
        achat.quantite = quantite
        achat.prix_unitaire = prix_unitaire
        achat.fournisseur = fournisseur
        achat.notes = notes
        achat.numero_facture = numero_facture
        
        # Calculer le montant total
        achat.calculer_montant_total()
        
        try:
            # Sauvegarder l'achat
            db.session.add(achat)
            
            # Mettre à jour le stock et le prix d'achat
            produit.stock_actuel += quantite
            
            # Mettre à jour le prix d'achat moyen pondéré
            if produit.stock_actuel > quantite:  # Il y avait déjà du stock
                ancienne_valeur = (produit.stock_actuel - quantite) * produit.prix_achat
                nouvelle_valeur = quantite * prix_unitaire
                valeur_totale = ancienne_valeur + nouvelle_valeur
                produit.prix_achat = valeur_totale / produit.stock_actuel
            else:  # Premier stock
                produit.prix_achat = prix_unitaire
            
            db.session.commit()
            return achat, "Achat créé avec succès"
            
        except Exception as e:
            db.session.rollback()
            return None, f"Erreur lors de la création de l'achat: {str(e)}"
    
    @staticmethod
    def get_achats_by_period(date_debut=None, date_fin=None):
        """Retourne les achats pour une période donnée"""
        query = Achat.query
        
        if date_debut:
            query = query.filter(Achat.date_achat >= date_debut)
        if date_fin:
            query = query.filter(Achat.date_achat <= date_fin)
        
        return query.order_by(db.desc(Achat.date_achat)).all()
    
    @staticmethod
    def get_achats_by_product(produit_id):
        """Retourne les achats d'un produit"""
        return Achat.query.filter_by(produit_id=produit_id).order_by(db.desc(Achat.date_achat)).all()
    
    @staticmethod
    def get_achats_by_supplier(fournisseur):
        """Retourne les achats d'un fournisseur"""
        return Achat.query.filter_by(fournisseur=fournisseur).order_by(db.desc(Achat.date_achat)).all()
    
    @staticmethod
    def calculate_daily_purchases(days=7):
        """Calcule les achats quotidiens sur les derniers jours"""
        date_debut = datetime.utcnow() - timedelta(days=days)
        
        achats = Achat.query.filter(
            Achat.date_achat >= date_debut,
            Achat.statut == 'completed'
        ).all()
        
        purchases_by_day = {}
        for i in range(days + 1):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            purchases_by_day[date.isoformat()] = {'montant': 0, 'quantite': 0, 'transactions': 0}
        
        for achat in achats:
            date_key = achat.date_achat.date().isoformat()
            if date_key in purchases_by_day:
                purchases_by_day[date_key]['montant'] += achat.montant_total
                purchases_by_day[date_key]['quantite'] += achat.quantite
                purchases_by_day[date_key]['transactions'] += 1
        
        return purchases_by_day
    
    @staticmethod
    def get_top_suppliers(limit=10, days=30):
        """Retourne les principaux fournisseurs"""
        date_debut = datetime.utcnow() - timedelta(days=days)
        
        # Agrégation des achats par fournisseur
        results = db.session.query(
            Achat.fournisseur,
            db.func.sum(Achat.montant_total).label('total_montant'),
            db.func.sum(Achat.quantite).label('total_quantite'),
            db.func.count(Achat.id).label('nombre_achats')
        ).filter(
            Achat.date_achat >= date_debut,
            Achat.statut == 'completed',
            Achat.fournisseur.isnot(None)
        ).group_by(Achat.fournisseur).order_by(db.desc('total_montant')).limit(limit).all()
        
        return [
            {
                'fournisseur': result.fournisseur,
                'total_montant': result.total_montant,
                'total_quantite': result.total_quantite,
                'nombre_achats': result.nombre_achats
            }
            for result in results
        ]
    
    @staticmethod
    def get_purchases_summary(date_debut=None, date_fin=None):
        """Retourne un résumé des achats"""
        query = Achat.query.filter_by(statut='completed')
        
        if date_debut:
            query = query.filter(Achat.date_achat >= date_debut)
        if date_fin:
            query = query.filter(Achat.date_achat <= date_fin)
        
        achats = query.all()
        
        total_achats = len(achats)
        montant_total = sum(achat.montant_total for achat in achats)
        quantite_totale = sum(achat.quantite for achat in achats)
        
        # Calcul du panier moyen
        panier_moyen = montant_total / total_achats if total_achats > 0 else 0
        
        # Nombre de fournisseurs uniques
        fournisseurs = set(achat.fournisseur for achat in achats if achat.fournisseur)
        
        return {
            'total_achats': total_achats,
            'montant_total': montant_total,
            'quantite_totale': quantite_totale,
            'panier_moyen': panier_moyen,
            'nombre_fournisseurs': len(fournisseurs)
        }
    
    @staticmethod
    def cancel_achat(achat_id, reason=None):
        """Annule un achat et ajuste le stock"""
        achat = Achat.query.get(achat_id)
        if not achat:
            return False, "Achat non trouvé"
        
        if achat.statut == 'cancelled':
            return False, "Achat déjà annulé"
        
        try:
            # Ajuster le stock
            produit = achat.produit_rel
            if produit.stock_actuel >= achat.quantite:
                produit.stock_actuel -= achat.quantite
            else:
                return False, "Impossible d'annuler: stock insuffisant"
            
            # Marquer comme annulé
            achat.statut = 'cancelled'
            if reason:
                achat.notes = f"Annulé: {reason}. {achat.notes or ''}"
            
            db.session.commit()
            return True, "Achat annulé avec succès"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de l'annulation: {str(e)}"
