from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required
from services.statistique_service import StatistiqueService
from services.vente_service import VenteService
from services.achat_service import AchatService
from services.stock_service import StockService
from datetime import datetime
from utils.helpers import format_currency, get_date_range, export_to_csv
import json

statistique_bp = Blueprint('statistique', __name__, url_prefix='/statistiques')

@statistique_bp.route('/')
@login_required
def dashboard_statistiques():
    """Tableau de bord des statistiques"""
    try:
        period = request.args.get('period', 'month', type=str)
        
        # Récupérer les dates selon la période
        date_debut, date_fin = get_date_range(period)
        
        # Balance commerciale
        balance = StatistiqueService.get_balance_commerciale(
            datetime.combine(date_debut, datetime.min.time()) if date_debut else None,
            datetime.combine(date_fin, datetime.max.time()) if date_fin else None
        )
        
        # Statistiques mensuelles
        stats_mensuelles = StatistiqueService.get_monthly_statistics()
        
        # Performance des produits
        performance_produits = StatistiqueService.get_product_performance()
        
        # Statistiques clients
        stats_clients = StatistiqueService.get_client_statistics()
        
        # Données pour le tableau de bord
        dashboard_data = StatistiqueService.get_dashboard_data()
        
        return render_template('statistiques.html',
                               balance=balance,
                               stats_mensuelles=stats_mensuelles,
                               performance_produits=performance_produits[:10],  # Top 10
                               stats_clients=stats_clients[:10],  # Top 10
                               dashboard_data=dashboard_data,
                               period=period)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des statistiques: {str(e)}", "error")
        return render_template('statistiques.html', 
                               balance={}, stats_mensuelles={}, 
                               performance_produits=[], stats_clients=[],
                               dashboard_data={})

@statistique_bp.route('/balance')
@login_required
def balance_commerciale():
    """Balance commerciale détaillée"""
    try:
        period = request.args.get('period', 'year', type=str)
        
        date_debut, date_fin = get_date_range(period)
        
        balance = StatistiqueService.get_balance_commerciale(
            datetime.combine(date_debut, datetime.min.time()) if date_debut else None,
            datetime.combine(date_fin, datetime.max.time()) if date_fin else None
        )
        
        # Comparaison année sur année
        comparison = StatistiqueService.get_yearly_comparison()
        
        return render_template('statistiques.html',
                               show_balance=True,
                               balance=balance,
                               comparison=comparison,
                               period=period)
        
    except Exception as e:
        flash(f"Erreur lors du chargement de la balance: {str(e)}", "error")
        return redirect(url_for('statistique.dashboard_statistiques'))

@statistique_bp.route('/produits')
@login_required
def performance_produits():
    """Performance détaillée des produits"""
    try:
        performance = StatistiqueService.get_product_performance()
        
        return render_template('statistiques.html',
                               show_produits=True,
                               performance_produits=performance)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des performances produits: {str(e)}", "error")
        return redirect(url_for('statistique.dashboard_statistiques'))

@statistique_bp.route('/api/monthly-evolution')
@login_required
def api_monthly_evolution():
    """API pour l'évolution mensuelle"""
    try:
        annee = request.args.get('year', datetime.now().year, type=int)
        comparison = StatistiqueService.get_yearly_comparison(annee)
        
        current_year = comparison['stats_mensuelles_courantes']
        previous_year = comparison['stats_mensuelles_precedentes']
        
        labels = [f"{stat['mois']:02d}/{stat['annee']}" for stat in current_year]
        
        return jsonify({
            'labels': labels,
            'datasets': [
                {
                    'label': f'Ventes {annee}',
                    'data': [stat['total_ventes'] for stat in current_year],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1
                },
                {
                    'label': f'Achats {annee}',
                    'data': [stat['total_achats'] for stat in current_year],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'tension': 0.1
                },
                {
                    'label': f'Bénéfice {annee}',
                    'data': [stat['benefice'] for stat in current_year],
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'tension': 0.1
                }
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@statistique_bp.route('/api/top-products')
@login_required
def api_top_products():
    """API pour les produits les plus vendus"""
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        top_products = VenteService.get_top_selling_products(limit=limit, days=days)
        
        labels = [prod['produit'].nom for prod in top_products]
        data = [prod['total_quantite'] for prod in top_products]
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'Quantité vendue',
                'data': data,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 205, 86, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(153, 102, 255, 0.6)',
                    'rgba(255, 159, 64, 0.6)',
                    'rgba(199, 199, 199, 0.6)',
                    'rgba(83, 102, 255, 0.6)',
                    'rgba(40, 159, 64, 0.6)',
                    'rgba(210, 199, 199, 0.6)'
                ]
            }]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@statistique_bp.route('/export')
@login_required
def export_statistiques():
    """Exporte les statistiques"""
    try:
        format_export = request.args.get('format', 'csv', type=str)
        period = request.args.get('period', 'month', type=str)
        
        date_debut, date_fin = get_date_range(period)
        
        # Récupérer les données à exporter
        export_data = StatistiqueService.export_statistics_data(
            format_export='dict',
            date_debut=datetime.combine(date_debut, datetime.min.time()) if date_debut else None,
            date_fin=datetime.combine(date_fin, datetime.max.time()) if date_fin else None
        )
        
        if format_export == 'json':
            response = make_response(json.dumps(export_data, indent=2, default=str))
            response.headers["Content-Disposition"] = "attachment; filename=statistiques.json"
            response.headers["Content-type"] = "application/json"
            return response
        
        elif format_export == 'csv':
            # Exporter la balance commerciale
            data = []
            balance = export_data['balance_commerciale']
            data.append([
                'Balance commerciale',
                balance['total_ventes'],
                balance['total_achats'],
                balance['balance'],
                f"{balance['marge_brute']:.2f}%"
            ])
            
            # Ajouter les statistiques clients
            data.append(['', '', '', '', ''])  # Ligne vide
            data.append(['Top Clients', '', '', '', ''])
            for client_stat in export_data['statistiques_clients'][:10]:
                data.append([
                    client_stat['nom_client'],
                    client_stat['email'],
                    client_stat['nombre_achats'],
                    client_stat['montant_total'],
                    client_stat['panier_moyen']
                ])
            
            # Ajouter les performances produits
            data.append(['', '', '', '', ''])  # Ligne vide
            data.append(['Performance Produits', '', '', '', ''])
            for prod_stat in export_data['performance_produits'][:10]:
                data.append([
                    prod_stat['nom_produit'],
                    prod_stat['quantite_vendue'],
                    prod_stat['ca_genere'],
                    prod_stat['benefice_genere'],
                    f"{prod_stat['marge_moyenne']:.2f}%"
                ])
            
            headers = ['Élément', 'Valeur 1', 'Valeur 2', 'Valeur 3', 'Valeur 4']
            return export_to_csv(data, f'statistiques_{period}.csv', headers)
        
        else:
            flash("Format d'export non supporté.", "error")
            return redirect(url_for('statistique.dashboard_statistiques'))
            
    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "error")
        return redirect(url_for('statistique.dashboard_statistiques'))

@statistique_bp.route('/rapport')
@login_required
def rapport_complet():
    """Génère un rapport complet"""
    try:
        # Récupérer toutes les données nécessaires
        balance = StatistiqueService.get_balance_commerciale()
        dashboard_data = StatistiqueService.get_dashboard_data()
        performance_produits = StatistiqueService.get_product_performance()
        stats_clients = StatistiqueService.get_client_statistics()
        stock_summary = StockService.get_stock_summary()
        
        # Top 5 dans chaque catégorie
        top_produits = performance_produits[:5]
        top_clients = stats_clients[:5]
        
        return render_template('statistiques.html',
                               show_rapport=True,
                               balance=balance,
                               dashboard_data=dashboard_data,
                               top_produits=top_produits,
                               top_clients=top_clients,
                               stock_summary=stock_summary,
                               date_rapport=datetime.now())
        
    except Exception as e:
        flash(f"Erreur lors de la génération du rapport: {str(e)}", "error")
        return redirect(url_for('statistique.dashboard_statistiques'))
