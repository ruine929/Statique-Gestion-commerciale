from models.vente import Vente
from models.achat import Achat
from models.produit import Produit
from models.client import Client
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, extract

class StatistiqueService:
    """Service pour la génération de statistiques"""
    
    @staticmethod
    def get_balance_commerciale(date_debut=None, date_fin=None):
        """Calcule la balance commerciale (ventes - achats)"""
        # Calculer le total des ventes
        ventes_query = db.session.query(func.sum(Vente.montant_total)).filter_by(statut='completed')
        if date_debut:
            ventes_query = ventes_query.filter(Vente.date_vente >= date_debut)
        if date_fin:
            ventes_query = ventes_query.filter(Vente.date_vente <= date_fin)
        
        total_ventes = ventes_query.scalar() or 0
        
        # Calculer le total des achats
        achats_query = db.session.query(func.sum(Achat.montant_total)).filter_by(statut='completed')
        if date_debut:
            achats_query = achats_query.filter(Achat.date_achat >= date_debut)
        if date_fin:
            achats_query = achats_query.filter(Achat.date_achat <= date_fin)
        
        total_achats = achats_query.scalar() or 0
        
        balance = total_ventes - total_achats
        
        return {
            'total_ventes': total_ventes,
            'total_achats': total_achats,
            'balance': balance,
            'marge_brute': (balance / total_ventes * 100) if total_ventes > 0 else 0
        }
    
    @staticmethod
    def get_monthly_statistics(mois=None, annee=None):
        """Retourne les statistiques mensuelles"""
        if not mois:
            mois = datetime.now().month
        if not annee:
            annee = datetime.now().year
        
        # Ventes du mois
        ventes = Vente.query.filter(
            extract('month', Vente.date_vente) == mois,
            extract('year', Vente.date_vente) == annee,
            Vente.statut == 'completed'
        ).all()
        
        # Achats du mois
        achats = Achat.query.filter(
            extract('month', Achat.date_achat) == mois,
            extract('year', Achat.date_achat) == annee,
            Achat.statut == 'completed'
        ).all()
        
        total_ventes = sum(vente.montant_total for vente in ventes)
        total_achats = sum(achat.montant_total for achat in achats)
        benefice = sum(vente.benefice for vente in ventes)
        
        return {
            'mois': mois,
            'annee': annee,
            'nombre_ventes': len(ventes),
            'nombre_achats': len(achats),
            'total_ventes': total_ventes,
            'total_achats': total_achats,
            'benefice': benefice,
            'balance': total_ventes - total_achats
        }
    
    @staticmethod
    def get_yearly_comparison(annee=None):
        """Compare les performances année sur année"""
        if not annee:
            annee = datetime.now().year
        
        current_year_stats = []
        previous_year_stats = []
        
        for mois in range(1, 13):
            # Statistiques année courante
            current_stats = StatistiqueService.get_monthly_statistics(mois, annee)
            current_year_stats.append(current_stats)
            
            # Statistiques année précédente
            previous_stats = StatistiqueService.get_monthly_statistics(mois, annee - 1)
            previous_year_stats.append(previous_stats)
        
        # Calculer les totaux annuels
        total_current = {
            'ventes': sum(stat['total_ventes'] for stat in current_year_stats),
            'achats': sum(stat['total_achats'] for stat in current_year_stats),
            'benefice': sum(stat['benefice'] for stat in current_year_stats)
        }
        
        total_previous = {
            'ventes': sum(stat['total_ventes'] for stat in previous_year_stats),
            'achats': sum(stat['total_achats'] for stat in previous_year_stats),
            'benefice': sum(stat['benefice'] for stat in previous_year_stats)
        }
        
        # Calculer les variations
        variations = {}
        for key in total_current:
            if total_previous[key] > 0:
                variations[key] = ((total_current[key] - total_previous[key]) / total_previous[key]) * 100
            else:
                variations[key] = 100 if total_current[key] > 0 else 0
        
        return {
            'annee_courante': annee,
            'stats_mensuelles_courantes': current_year_stats,
            'stats_mensuelles_precedentes': previous_year_stats,
            'totaux_courants': total_current,
            'totaux_precedents': total_previous,
            'variations': variations
        }
    
    @staticmethod
    def get_client_statistics():
        """Retourne les statistiques clients"""
        clients = Client.query.all()
        
        client_stats = []
        for client in clients:
            ventes = client.ventes.filter_by(statut='completed').all()
            
            client_stats.append({
                'client': client,
                'nombre_achats': len(ventes),
                'montant_total': sum(vente.montant_total for vente in ventes),
                'derniere_vente': max([vente.date_vente for vente in ventes]) if ventes else None,
                'panier_moyen': sum(vente.montant_total for vente in ventes) / len(ventes) if ventes else 0
            })
        
        # Trier par montant total décroissant
        client_stats.sort(key=lambda x: x['montant_total'], reverse=True)
        
        return client_stats
    
    @staticmethod
    def get_product_performance():
        """Analyse la performance des produits"""
        produits = Produit.query.filter_by(actif=True).all()
        
        product_stats = []
        for produit in produits:
            ventes = produit.ventes.filter_by(statut='completed').all()
            
            quantite_vendue = sum(vente.quantite for vente in ventes)
            ca_genere = sum(vente.montant_total for vente in ventes)
            benefice_genere = sum(vente.benefice for vente in ventes)
            
            # Calcul de la rotation du stock
            rotation = quantite_vendue / produit.stock_initial if produit.stock_initial > 0 else 0
            
            product_stats.append({
                'produit': produit,
                'quantite_vendue': quantite_vendue,
                'ca_genere': ca_genere,
                'benefice_genere': benefice_genere,
                'rotation_stock': rotation,
                'marge_moyenne': (benefice_genere / ca_genere * 100) if ca_genere > 0 else 0
            })
        
        # Trier par chiffre d'affaires décroissant
        product_stats.sort(key=lambda x: x['ca_genere'], reverse=True)
        
        return product_stats
    
    @staticmethod
    def get_dashboard_data():
        """Retourne les données pour le tableau de bord"""
        aujourd_hui = datetime.now().date()
        debut_semaine = aujourd_hui - timedelta(days=7)
        debut_mois = aujourd_hui.replace(day=1)
        
        # Statistiques du jour
        ventes_jour = Vente.query.filter(
            func.date(Vente.date_vente) == aujourd_hui,
            Vente.statut == 'completed'
        ).all()
        
        # Statistiques de la semaine
        ventes_semaine = Vente.query.filter(
            Vente.date_vente >= debut_semaine,
            Vente.statut == 'completed'
        ).all()
        
        # Statistiques du mois
        ventes_mois = Vente.query.filter(
            Vente.date_vente >= debut_mois,
            Vente.statut == 'completed'
        ).all()
        
        # Balance commerciale du mois
        balance_mois = StatistiqueService.get_balance_commerciale(debut_mois)
        
        # Produits en stock faible
        from services.stock_service import StockService
        produits_stock_faible = StockService.get_products_with_low_stock()
        
        # Top 5 des produits les plus vendus ce mois
        from services.vente_service import VenteService
        top_produits = VenteService.get_top_selling_products(limit=5, days=30)
        
        return {
            'ventes_jour': {
                'nombre': len(ventes_jour),
                'montant': sum(vente.montant_total for vente in ventes_jour)
            },
            'ventes_semaine': {
                'nombre': len(ventes_semaine),
                'montant': sum(vente.montant_total for vente in ventes_semaine)
            },
            'ventes_mois': {
                'nombre': len(ventes_mois),
                'montant': sum(vente.montant_total for vente in ventes_mois)
            },
            'balance_mois': balance_mois,
            'produits_stock_faible': len(produits_stock_faible),
            'top_produits': top_produits
        }
    
    @staticmethod
    def export_statistics_data(format_export='dict', date_debut=None, date_fin=None):
        """Exporte les données statistiques"""
        # Récupérer toutes les données
        balance = StatistiqueService.get_balance_commerciale(date_debut, date_fin)
        client_stats = StatistiqueService.get_client_statistics()
        product_stats = StatistiqueService.get_product_performance()
        
        # Préparer les données d'export
        export_data = {
            'periode': {
                'debut': date_debut.isoformat() if date_debut else None,
                'fin': date_fin.isoformat() if date_fin else None
            },
            'balance_commerciale': balance,
            'statistiques_clients': [
                {
                    'nom_client': stat['client'].nom,
                    'email': stat['client'].email,
                    'nombre_achats': stat['nombre_achats'],
                    'montant_total': stat['montant_total'],
                    'panier_moyen': stat['panier_moyen']
                }
                for stat in client_stats
            ],
            'performance_produits': [
                {
                    'nom_produit': stat['produit'].nom,
                    'quantite_vendue': stat['quantite_vendue'],
                    'ca_genere': stat['ca_genere'],
                    'benefice_genere': stat['benefice_genere'],
                    'rotation_stock': stat['rotation_stock'],
                    'marge_moyenne': stat['marge_moyenne']
                }
                for stat in product_stats
            ]
        }
        
        return export_data
