from models.produit import Produit
from services.stock_service import StockService
from datetime import datetime, timedelta
import logging

class AlerteService:
    """Service pour la gestion des alertes"""
    
    @staticmethod
    def check_low_stock_alerts():
        """Vérifie et retourne les alertes de stock faible"""
        produits_stock_faible = StockService.get_products_with_low_stock()
        
        alertes = []
        for produit in produits_stock_faible:
            niveau_alerte = "critique" if produit.stock_actuel == 0 else "faible"
            
            alerte = {
                'type': 'stock_faible',
                'niveau': niveau_alerte,
                'produit_id': produit.id,
                'produit_nom': produit.nom,
                'stock_actuel': produit.stock_actuel,
                'stock_minimum': produit.stock_minimum,
                'message': f"Stock {niveau_alerte} pour {produit.nom}: {produit.stock_actuel} unités restantes",
                'date_alerte': datetime.utcnow(),
                'urgent': produit.stock_actuel == 0
            }
            alertes.append(alerte)
        
        return alertes
    
    @staticmethod
    def check_sales_performance_alerts(days=7):
        """Vérifie les alertes de performance de vente"""
        from services.vente_service import VenteService
        
        # Comparer avec la période précédente
        fin_periode_actuelle = datetime.utcnow()
        debut_periode_actuelle = fin_periode_actuelle - timedelta(days=days)
        fin_periode_precedente = debut_periode_actuelle
        debut_periode_precedente = fin_periode_precedente - timedelta(days=days)
        
        ventes_actuelles = VenteService.get_sales_summary(debut_periode_actuelle, fin_periode_actuelle)
        ventes_precedentes = VenteService.get_sales_summary(debut_periode_precedente, fin_periode_precedente)
        
        alertes = []
        
        # Alerte si baisse significative des ventes (>20%)
        if ventes_precedentes['montant_total'] > 0:
            variation = ((ventes_actuelles['montant_total'] - ventes_precedentes['montant_total']) 
                        / ventes_precedentes['montant_total']) * 100
            
            if variation < -20:  # Baisse de plus de 20%
                alerte = {
                    'type': 'baisse_ventes',
                    'niveau': 'attention',
                    'variation': variation,
                    'montant_actuel': ventes_actuelles['montant_total'],
                    'montant_precedent': ventes_precedentes['montant_total'],
                    'message': f"Baisse des ventes de {abs(variation):.1f}% sur les {days} derniers jours",
                    'date_alerte': datetime.utcnow(),
                    'urgent': variation < -50
                }
                alertes.append(alerte)
        
        # Alerte si aucune vente dans la période
        if ventes_actuelles['total_ventes'] == 0:
            alerte = {
                'type': 'aucune_vente',
                'niveau': 'critique',
                'message': f"Aucune vente enregistrée dans les {days} derniers jours",
                'date_alerte': datetime.utcnow(),
                'urgent': True
            }
            alertes.append(alerte)
        
        return alertes
    
    @staticmethod
    def check_product_expiry_alerts():
        """Vérifie les alertes pour les produits qui ne se vendent pas"""
        from services.vente_service import VenteService
        
        alertes = []
        produits = Produit.query.filter_by(actif=True).all()
        
        date_limite = datetime.utcnow() - timedelta(days=30)  # 30 jours sans vente
        
        for produit in produits:
            # Vérifier si le produit a été vendu dans les 30 derniers jours
            ventes_recentes = produit.ventes.filter(
                produit.ventes.c.date_vente >= date_limite,
                produit.ventes.c.statut == 'completed'
            ).count()
            
            if ventes_recentes == 0 and produit.stock_actuel > 0:
                alerte = {
                    'type': 'produit_non_vendu',
                    'niveau': 'attention',
                    'produit_id': produit.id,
                    'produit_nom': produit.nom,
                    'stock_actuel': produit.stock_actuel,
                    'valeur_stock': produit.valeur_stock,
                    'message': f"Produit {produit.nom} non vendu depuis 30 jours",
                    'date_alerte': datetime.utcnow(),
                    'urgent': False
                }
                alertes.append(alerte)
        
        return alertes
    
    @staticmethod
    def get_all_alerts():
        """Retourne toutes les alertes actives"""
        alertes = []
        
        # Alertes de stock
        alertes.extend(AlerteService.check_low_stock_alerts())
        
        # Alertes de performance
        alertes.extend(AlerteService.check_sales_performance_alerts())
        
        # Alertes de produits non vendus
        alertes.extend(AlerteService.check_product_expiry_alerts())
        
        # Trier par urgence puis par date
        alertes.sort(key=lambda x: (not x.get('urgent', False), x['date_alerte']), reverse=True)
        
        return alertes
    
    @staticmethod
    def get_alerts_summary():
        """Retourne un résumé des alertes"""
        alertes = AlerteService.get_all_alerts()
        
        summary = {
            'total_alertes': len(alertes),
            'alertes_urgentes': len([a for a in alertes if a.get('urgent', False)]),
            'alertes_par_type': {},
            'alertes_par_niveau': {}
        }
        
        for alerte in alertes:
            # Compter par type
            type_alerte = alerte['type']
            summary['alertes_par_type'][type_alerte] = summary['alertes_par_type'].get(type_alerte, 0) + 1
            
            # Compter par niveau
            niveau = alerte['niveau']
            summary['alertes_par_niveau'][niveau] = summary['alertes_par_niveau'].get(niveau, 0) + 1
        
        return summary
    
    @staticmethod
    def log_alert(alerte):
        """Enregistre une alerte dans les logs"""
        niveau_log = logging.WARNING if alerte.get('urgent') else logging.INFO
        
        logging.log(
            niveau_log,
            f"ALERTE {alerte['type'].upper()}: {alerte['message']}"
        )
    
    @staticmethod
    def format_alert_for_display(alerte):
        """Formate une alerte pour l'affichage"""
        icons = {
            'stock_faible': '📦',
            'baisse_ventes': '📉',
            'aucune_vente': '🚫',
            'produit_non_vendu': '⏰'
        }
        
        couleurs = {
            'critique': 'danger',
            'attention': 'warning',
            'faible': 'info'
        }
        
        return {
            'icon': icons.get(alerte['type'], '⚠️'),
            'couleur': couleurs.get(alerte['niveau'], 'secondary'),
            'message': alerte['message'],
            'urgent': alerte.get('urgent', False),
            'date': alerte['date_alerte'].strftime('%d/%m/%Y %H:%M')
        }
