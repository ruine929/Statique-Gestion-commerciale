from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models.achat import Achat
from models.produit import Produit
from services.achat_service import AchatService
from app import db
from datetime import datetime
from utils.helpers import format_currency, get_date_range

achat_bp = Blueprint('achat', __name__, url_prefix='/achats')

@achat_bp.route('/')
@login_required
def list_achats():
    """Liste tous les achats"""
    try:
        page = request.args.get('page', 1, type=int)
        period = request.args.get('period', 'month', type=str)
        fournisseur = request.args.get('fournisseur', type=str)
        
        # Construire la requête
        query = Achat.query
        
        # Filtrer par période
        date_debut, date_fin = get_date_range(period)
        if date_debut and date_fin:
            query = query.filter(
                Achat.date_achat >= datetime.combine(date_debut, datetime.min.time()),
                Achat.date_achat <= datetime.combine(date_fin, datetime.max.time())
            )
        
        # Filtrer par fournisseur
        if fournisseur:
            query = query.filter(Achat.fournisseur.contains(fournisseur))
        
        achats = query.order_by(db.desc(Achat.date_achat)).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Récupérer tous les produits pour le formulaire
        produits = Produit.query.filter_by(actif=True).order_by(Produit.nom).all()
        
        # Récupérer les fournisseurs uniques pour le filtre
        fournisseurs = db.session.query(Achat.fournisseur).distinct().filter(
            Achat.fournisseur.isnot(None),
            Achat.fournisseur != ''
        ).all()
        fournisseurs = [f[0] for f in fournisseurs]
        
        # Calculer les statistiques de la période
        summary = AchatService.get_purchases_summary(
            datetime.combine(date_debut, datetime.min.time()) if date_debut else None,
            datetime.combine(date_fin, datetime.max.time()) if date_fin else None
        )
        
        return render_template('achats.html',
                               achats=achats,
                               produits=produits,
                               fournisseurs=fournisseurs,
                               period=period,
                               fournisseur_filter=fournisseur,
                               summary=summary)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des achats: {str(e)}", "error")
        return render_template('achats.html', achats=None, produits=[], fournisseurs=[], summary={})

@achat_bp.route('/nouveau', methods=['POST'])
@login_required
def nouvel_achat():
    """Crée un nouvel achat"""
    try:
        produit_id = int(request.form.get('produit_id') or 0)
        quantite = int(request.form.get('quantite') or 0)
        prix_unitaire = float(request.form.get('prix_unitaire') or 0)
        fournisseur = request.form.get('fournisseur', '').strip()
        notes = request.form.get('notes', '').strip()
        numero_facture = request.form.get('numero_facture', '').strip()
        
        # Validations
        if quantite <= 0:
            flash("La quantité doit être supérieure à zéro.", "error")
            return redirect(url_for('achat.list_achats'))
        
        if prix_unitaire <= 0:
            flash("Le prix unitaire doit être supérieur à zéro.", "error")
            return redirect(url_for('achat.list_achats'))
        
        # Créer l'achat
        achat, message = AchatService.create_achat(
            produit_id=produit_id,
            quantite=quantite,
            prix_unitaire=prix_unitaire,
            fournisseur=fournisseur if fournisseur else None,
            notes=notes if notes else None,
            numero_facture=numero_facture if numero_facture else None
        )
        
        if achat:
            flash(message, "success")
        else:
            flash(message, "error")
            
    except ValueError:
        flash("Erreur dans les valeurs saisies.", "error")
    except Exception as e:
        flash(f"Erreur lors de la création de l'achat: {str(e)}", "error")
    
    return redirect(url_for('achat.list_achats'))

@achat_bp.route('/annuler/<int:id>', methods=['POST'])
@login_required
def annuler_achat(id):
    """Annule un achat"""
    try:
        reason = request.form.get('reason', '').strip()
        
        success, message = AchatService.cancel_achat(id, reason)
        
        if success:
            flash(message, "success")
        else:
            flash(message, "error")
            
    except Exception as e:
        flash(f"Erreur lors de l'annulation de l'achat: {str(e)}", "error")
    
    return redirect(url_for('achat.list_achats'))

@achat_bp.route('/detail/<int:id>')
@login_required
def detail_achat(id):
    """Retourne les détails d'un achat en JSON"""
    try:
        achat = Achat.query.get_or_404(id)
        
        return jsonify({
            'achat': achat.to_dict(),
            'produit': achat.produit_rel.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@achat_bp.route('/statistiques')
@login_required
def statistiques_achats():
    """Statistiques détaillées des achats"""
    try:
        period = request.args.get('period', 'month', type=str)
        
        # Récupérer les données selon la période
        date_debut, date_fin = get_date_range(period)
        
        # Statistiques générales
        summary = AchatService.get_purchases_summary(
            datetime.combine(date_debut, datetime.min.time()) if date_debut else None,
            datetime.combine(date_fin, datetime.max.time()) if date_fin else None
        )
        
        # Top fournisseurs
        top_fournisseurs = AchatService.get_top_suppliers(limit=10, days=30)
        
        # Achats quotidiens
        daily_purchases = AchatService.calculate_daily_purchases(days=30)
        
        return render_template('achats.html',
                               show_stats=True,
                               summary=summary,
                               top_fournisseurs=top_fournisseurs,
                               daily_purchases=daily_purchases,
                               period=period)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des statistiques: {str(e)}", "error")
        return redirect(url_for('achat.list_achats'))

@achat_bp.route('/api/daily-purchases')
@login_required
def api_daily_purchases():
    """API pour les achats quotidiens (pour les graphiques)"""
    try:
        days = request.args.get('days', 7, type=int)
        daily_purchases = AchatService.calculate_daily_purchases(days)
        
        # Transformer pour Chart.js
        labels = list(daily_purchases.keys())
        data_montant = [daily_purchases[date]['montant'] for date in labels]
        data_transactions = [daily_purchases[date]['transactions'] for date in labels]
        
        return jsonify({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Montant (MGA)',
                    'data': data_montant,
                    'borderColor': 'rgb(255, 159, 64)',
                    'backgroundColor': 'rgba(255, 159, 64, 0.2)',
                    'tension': 0.1
                },
                {
                    'label': 'Nombre de transactions',
                    'data': data_transactions,
                    'borderColor': 'rgb(153, 102, 255)',
                    'backgroundColor': 'rgba(153, 102, 255, 0.2)',
                    'tension': 0.1,
                    'yAxisID': 'y1'
                }
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@achat_bp.route('/fournisseurs')
@login_required
def list_fournisseurs():
    """Liste des fournisseurs avec leurs statistiques"""
    try:
        # Récupérer les top fournisseurs
        top_fournisseurs = AchatService.get_top_suppliers(limit=50, days=365)
        
        return render_template('achats.html',
                               show_fournisseurs=True,
                               fournisseurs_stats=top_fournisseurs)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des fournisseurs: {str(e)}", "error")
        return redirect(url_for('achat.list_achats'))
