from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.vente import Vente
from models.produit import Produit
from models.client import Client
from services.vente_service import VenteService
from app import db
from datetime import datetime
from utils.helpers import format_currency, get_date_range

vente_bp = Blueprint('vente', __name__, url_prefix='/ventes')

@vente_bp.route('/')
@login_required
def list_ventes():
    """Liste toutes les ventes"""
    try:
        page = request.args.get('page', 1, type=int)
        period = request.args.get('period', 'month', type=str)
        client_id = request.args.get('client_id', type=int)
        
        # Construire la requête
        query = Vente.query
        
        # Filtrer par période
        date_debut, date_fin = get_date_range(period)
        if date_debut and date_fin:
            query = query.filter(
                Vente.date_vente >= datetime.combine(date_debut, datetime.min.time()),
                Vente.date_vente <= datetime.combine(date_fin, datetime.max.time())
            )
        
        # Filtrer par client
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        ventes = query.order_by(db.desc(Vente.date_vente)).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Récupérer les clients pour le filtre
        clients = Client.query.order_by(Client.nom).all()
        
        # Récupérer les produits disponibles
        produits = Produit.query.filter(
            Produit.actif == True,
            Produit.stock_actuel > 0
        ).order_by(Produit.nom).all()
        
        # Calculer les statistiques de la période
        summary = VenteService.get_sales_summary(
            datetime.combine(date_debut, datetime.min.time()) if date_debut else None,
            datetime.combine(date_fin, datetime.max.time()) if date_fin else None
        )
        
        return render_template('ventes.html',
                               ventes=ventes,
                               clients=clients,
                               produits=produits,
                               period=period,
                               client_id=client_id,
                               summary=summary)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des ventes: {str(e)}", "error")
        return render_template('ventes.html', ventes=None, clients=[], produits=[], summary={})

@vente_bp.route('/nouvelle', methods=['POST'])
@login_required
def nouvelle_vente():
    """Crée une nouvelle vente"""
    try:
        produit_id = int(request.form.get('produit_id') or 0)
        client_id = int(request.form.get('client_id') or 0)
        quantite = int(request.form.get('quantite') or 0)
        prix_unitaire = request.form.get('prix_unitaire')
        remise = float(request.form.get('remise', 0))
        notes = request.form.get('notes', '').strip()
        
        # Validation de base
        if quantite <= 0:
            flash("La quantité doit être supérieure à zéro.", "error")
            return redirect(url_for('vente.list_ventes'))
        
        if remise < 0 or remise > 100:
            flash("La remise doit être entre 0 et 100%.", "error")
            return redirect(url_for('vente.list_ventes'))
        
        # Utiliser le prix du produit si pas spécifié
        prix_unitaire_final = None
        if prix_unitaire:
            try:
                prix_unitaire_final = float(prix_unitaire)
                if prix_unitaire_final <= 0:
                    flash("Le prix unitaire doit être supérieur à zéro.", "error")
                    return redirect(url_for('vente.list_ventes'))
            except ValueError:
                flash("Prix unitaire invalide.", "error")
                return redirect(url_for('vente.list_ventes'))
        
        # Créer la vente
        vente, message = VenteService.create_vente(
            produit_id=produit_id,
            client_id=client_id,
            quantite=quantite,
            prix_unitaire=prix_unitaire_final,
            remise=remise,
            notes=notes
        )
        
        if vente:
            flash(message, "success")
        else:
            flash(message, "error")
            
    except ValueError:
        flash("Erreur dans les valeurs saisies.", "error")
    except Exception as e:
        flash(f"Erreur lors de la création de la vente: {str(e)}", "error")
    
    return redirect(url_for('vente.list_ventes'))

@vente_bp.route('/annuler/<int:id>', methods=['POST'])
@login_required
def annuler_vente(id):
    """Annule une vente"""
    try:
        reason = request.form.get('reason', '').strip()
        
        success, message = VenteService.cancel_vente(id, reason)
        
        if success:
            flash(message, "success")
        else:
            flash(message, "error")
            
    except Exception as e:
        flash(f"Erreur lors de l'annulation de la vente: {str(e)}", "error")
    
    return redirect(url_for('vente.list_ventes'))

@vente_bp.route('/detail/<int:id>')
@login_required
def detail_vente(id):
    """Retourne les détails d'une vente en JSON"""
    try:
        vente = Vente.query.get_or_404(id)
        
        return jsonify({
            'vente': vente.to_dict(),
            'produit': vente.produit_rel.to_dict(),
            'client': vente.client_rel.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vente_bp.route('/statistiques')
@login_required
def statistiques_ventes():
    """Statistiques détaillées des ventes"""
    try:
        period = request.args.get('period', 'month', type=str)
        
        # Récupérer les données selon la période
        date_debut, date_fin = get_date_range(period)
        
        # Statistiques générales
        summary = VenteService.get_sales_summary(
            datetime.combine(date_debut, datetime.min.time()) if date_debut else None,
            datetime.combine(date_fin, datetime.max.time()) if date_fin else None
        )
        
        # Top produits
        top_produits = VenteService.get_top_selling_products(limit=10, days=30)
        
        # Ventes quotidiennes
        daily_sales = VenteService.calculate_daily_sales(days=30)
        
        return render_template('ventes.html',
                               show_stats=True,
                               summary=summary,
                               top_produits=top_produits,
                               daily_sales=daily_sales,
                               period=period)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des statistiques: {str(e)}", "error")
        return redirect(url_for('vente.list_ventes'))

@vente_bp.route('/api/daily-sales')
@login_required
def api_daily_sales():
    """API pour les ventes quotidiennes (pour les graphiques)"""
    try:
        days = request.args.get('days', 7, type=int)
        daily_sales = VenteService.calculate_daily_sales(days)
        
        # Transformer pour Chart.js
        labels = list(daily_sales.keys())
        data_montant = [daily_sales[date]['montant'] for date in labels]
        data_transactions = [daily_sales[date]['transactions'] for date in labels]
        
        return jsonify({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Montant (MGA)',
                    'data': data_montant,
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1
                },
                {
                    'label': 'Nombre de transactions',
                    'data': data_transactions,
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'tension': 0.1,
                    'yAxisID': 'y1'
                }
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vente_bp.route('/produit/<int:produit_id>/prix')
@login_required
def get_prix_produit(produit_id):
    """Retourne le prix de vente d'un produit"""
    try:
        produit = Produit.query.get_or_404(produit_id)
        return jsonify({
            'prix_vente': produit.prix_vente,
            'stock_disponible': produit.stock_actuel
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
