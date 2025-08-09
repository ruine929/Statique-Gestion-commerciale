from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models.produit import Produit
from services.stock_service import StockService
from app import db
from utils.helpers import format_currency, calculate_percentage

produit_bp = Blueprint('produit', __name__, url_prefix='/produits')

@produit_bp.route('/')
@login_required
def list_produits():
    """Liste tous les produits"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        
        query = Produit.query.filter_by(actif=True)
        
        if search:
            query = query.filter(Produit.nom.contains(search))
        
        produits = query.order_by(Produit.nom).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Récupérer le résumé du stock
        stock_summary = StockService.get_stock_summary()
        
        return render_template('produits.html', 
                               produits=produits, 
                               search=search,
                               stock_summary=stock_summary)
    except Exception as e:
        flash(f"Erreur lors du chargement des produits: {str(e)}", "error")
        return render_template('produits.html', produits=None, search="", stock_summary={})

@produit_bp.route('/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_produit():
    """Crée un nouveau produit"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            description = request.form.get('description', '').strip()
            prix_achat = float(request.form.get('prix_achat', 0))
            prix_vente = float(request.form.get('prix_vente', 0))
            stock_initial = int(request.form.get('stock_initial', 0))
            stock_minimum = int(request.form.get('stock_minimum', 5))
            
            # Validations
            if not nom:
                flash("Le nom du produit est requis.", "error")
                return render_template('produits.html')
            
            if prix_achat <= 0 or prix_vente <= 0:
                flash("Les prix doivent être supérieurs à zéro.", "error")
                return render_template('produits.html')
            
            if prix_vente <= prix_achat:
                flash("Le prix de vente doit être supérieur au prix d'achat.", "error")
                return render_template('produits.html')
            
            if stock_initial < 0 or stock_minimum < 0:
                flash("Les quantités ne peuvent pas être négatives.", "error")
                return render_template('produits.html')
            
            # Vérifier si le produit existe déjà
            produit_existant = Produit.query.filter_by(nom=nom, actif=True).first()
            if produit_existant:
                flash("Un produit avec ce nom existe déjà.", "error")
                return render_template('produits.html')
            
            # Calculer la marge
            taux_marge = ((prix_vente - prix_achat) / prix_achat) * 100
            
            # Créer le produit
            produit = Produit()
            produit.nom = nom
            produit.description = description
            produit.prix_achat = prix_achat
            produit.prix_vente = prix_vente
            produit.stock_initial = stock_initial
            produit.stock_actuel = stock_initial
            produit.stock_minimum = stock_minimum
            produit.taux_marge = taux_marge
            
            db.session.add(produit)
            db.session.commit()
            
            flash(f"Produit '{nom}' créé avec succès.", "success")
            return redirect(url_for('produit.list_produits'))
            
        except ValueError:
            flash("Erreur dans les valeurs numériques saisies.", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création du produit: {str(e)}", "error")
    
    return redirect(url_for('produit.list_produits'))

@produit_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_produit(id):
    """Modifie un produit existant"""
    produit = Produit.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            description = request.form.get('description', '').strip()
            prix_achat = float(request.form.get('prix_achat', 0))
            prix_vente = float(request.form.get('prix_vente', 0))
            stock_minimum = int(request.form.get('stock_minimum', 5))
            
            # Validations
            if not nom:
                flash("Le nom du produit est requis.", "error")
                return redirect(url_for('produit.list_produits'))
            
            if prix_achat <= 0 or prix_vente <= 0:
                flash("Les prix doivent être supérieurs à zéro.", "error")
                return redirect(url_for('produit.list_produits'))
            
            if prix_vente <= prix_achat:
                flash("Le prix de vente doit être supérieur au prix d'achat.", "error")
                return redirect(url_for('produit.list_produits'))
            
            if stock_minimum < 0:
                flash("Le stock minimum ne peut pas être négatif.", "error")
                return redirect(url_for('produit.list_produits'))
            
            # Vérifier si un autre produit avec ce nom existe
            autre_produit = Produit.query.filter(
                Produit.nom == nom,
                Produit.id != id,
                Produit.actif == True
            ).first()
            
            if autre_produit:
                flash("Un autre produit avec ce nom existe déjà.", "error")
                return redirect(url_for('produit.list_produits'))
            
            # Mettre à jour le produit
            produit.nom = nom
            produit.description = description
            produit.prix_achat = prix_achat
            produit.prix_vente = prix_vente
            produit.stock_minimum = stock_minimum
            produit.taux_marge = ((prix_vente - prix_achat) / prix_achat) * 100
            
            db.session.commit()
            
            flash(f"Produit '{nom}' modifié avec succès.", "success")
            
        except ValueError:
            flash("Erreur dans les valeurs numériques saisies.", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification du produit: {str(e)}", "error")
    
    return redirect(url_for('produit.list_produits'))

@produit_bp.route('/supprimer/<int:id>', methods=['POST'])
@login_required
def supprimer_produit(id):
    """Supprime (désactive) un produit"""
    try:
        produit = Produit.query.get_or_404(id)
        
        # Vérifier s'il y a des ventes ou achats associés
        if produit.ventes.count() > 0 or produit.achats.count() > 0:
            # Ne pas supprimer, juste désactiver
            produit.actif = False
            flash(f"Produit '{produit.nom}' désactivé (historique conservé).", "info")
        else:
            # Supprimer complètement si aucun historique
            db.session.delete(produit)
            flash(f"Produit '{produit.nom}' supprimé définitivement.", "success")
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression du produit: {str(e)}", "error")
    
    return redirect(url_for('produit.list_produits'))

@produit_bp.route('/detail/<int:id>')
@login_required
def detail_produit(id):
    """Affiche les détails d'un produit"""
    try:
        produit = Produit.query.get_or_404(id)
        
        # Récupérer les mouvements de stock
        mouvements = StockService.get_stock_movements(produit_id=id, limit=20)
        
        # Calculer la rotation du stock
        rotation = StockService.calculate_stock_turnover(id, days=30)
        
        return jsonify({
            'produit': produit.to_dict(),
            'mouvements': mouvements,
            'rotation_stock': rotation
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@produit_bp.route('/stock-faible')
@login_required
def produits_stock_faible():
    """Liste des produits avec stock faible"""
    try:
        produits = StockService.get_products_with_low_stock()
        return render_template('produits.html', 
                               produits_stock_faible=produits,
                               titre="Produits en stock faible")
    except Exception as e:
        flash(f"Erreur lors du chargement des produits en stock faible: {str(e)}", "error")
        return redirect(url_for('produit.list_produits'))
