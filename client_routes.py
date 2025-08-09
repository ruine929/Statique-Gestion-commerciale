from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models.client import Client
from services.vente_service import VenteService
from services.statistique_service import StatistiqueService
from app import db
from utils.helpers import format_currency

client_bp = Blueprint('client', __name__, url_prefix='/clients')

@client_bp.route('/')
@login_required
def list_clients():
    """Liste tous les clients"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        sort_by = request.args.get('sort', 'nom', type=str)
        
        # Construire la requête
        query = Client.query
        
        # Filtrer par recherche
        if search:
            query = query.filter(
                db.or_(
                    Client.nom.contains(search),
                    Client.email.contains(search)
                )
            )
        
        # Trier
        if sort_by == 'nom':
            query = query.order_by(Client.nom)
        elif sort_by == 'date_inscription':
            query = query.order_by(db.desc(Client.date_inscription))
        elif sort_by == 'total_achats':
            # Tri complexe par total des achats - utilise une sous-requête
            from models.vente import Vente
            subquery = db.session.query(
                Vente.client_id,
                db.func.sum(Vente.montant_total).label('total')
            ).filter_by(statut='completed').group_by(Vente.client_id).subquery()
            
            query = query.outerjoin(subquery, Client.id == subquery.c.client_id).order_by(
                db.desc(db.coalesce(subquery.c.total, 0))
            )
        
        clients = query.paginate(page=page, per_page=20, error_out=False)
        
        # Récupérer les statistiques globales des clients
        client_stats = StatistiqueService.get_client_statistics()
        
        return render_template('clients.html',
                               clients=clients,
                               search=search,
                               sort_by=sort_by,
                               client_stats=client_stats[:10])  # Top 10 clients
        
    except Exception as e:
        flash(f"Erreur lors du chargement des clients: {str(e)}", "error")
        return render_template('clients.html', clients=None, search="", sort_by="nom", client_stats=[])

@client_bp.route('/detail/<int:id>')
@login_required
def detail_client(id):
    """Affiche les détails d'un client"""
    try:
        client = Client.query.get_or_404(id)
        
        # Récupérer l'historique des ventes
        ventes = VenteService.get_ventes_by_client(id)
        
        # Statistiques du client
        total_achats = client.total_achats
        nombre_achats = client.nombre_achats
        panier_moyen = total_achats / nombre_achats if nombre_achats > 0 else 0
        
        return render_template('clients.html',
                               show_detail=True,
                               client=client,
                               ventes=ventes,
                               stats_client={
                                   'total_achats': total_achats,
                                   'nombre_achats': nombre_achats,
                                   'panier_moyen': panier_moyen,
                                   'dernier_achat': client.dernier_achat
                               })
        
    except Exception as e:
        flash(f"Erreur lors du chargement des détails du client: {str(e)}", "error")
        return redirect(url_for('client.list_clients'))

@client_bp.route('/api/<int:id>/ventes')
@login_required
def api_client_ventes(id):
    """API pour récupérer les ventes d'un client"""
    try:
        client = Client.query.get_or_404(id)
        ventes = VenteService.get_ventes_by_client(id)
        
        # Préparer les données pour le graphique
        ventes_par_mois = {}
        for vente in ventes:
            mois_key = vente.date_vente.strftime('%Y-%m')
            if mois_key not in ventes_par_mois:
                ventes_par_mois[mois_key] = {'montant': 0, 'quantite': 0}
            ventes_par_mois[mois_key]['montant'] += vente.montant_total
            ventes_par_mois[mois_key]['quantite'] += 1
        
        # Trier par mois
        mois_tries = sorted(ventes_par_mois.keys())
        
        return jsonify({
            'client': client.to_dict(),
            'ventes_recentes': [vente.to_dict() for vente in ventes[:10]],
            'evolution_mensuelle': {
                'labels': mois_tries,
                'montants': [ventes_par_mois[mois]['montant'] for mois in mois_tries],
                'transactions': [ventes_par_mois[mois]['quantite'] for mois in mois_tries]
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/modifier/<int:id>', methods=['POST'])
@login_required
def modifier_client(id):
    """Modifie les informations d'un client"""
    try:
        client = Client.query.get_or_404(id)
        
        nom = request.form.get('nom', '').strip()
        telephone = request.form.get('telephone', '').strip()
        adresse = request.form.get('adresse', '').strip()
        
        # Validations
        if not nom:
            flash("Le nom du client est requis.", "error")
            return redirect(url_for('client.detail_client', id=id))
        
        # Mettre à jour les informations
        client.nom = nom
        client.telephone = telephone if telephone else None
        client.adresse = adresse if adresse else None
        
        db.session.commit()
        flash("Informations du client mises à jour avec succès.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la modification du client: {str(e)}", "error")
    
    return redirect(url_for('client.detail_client', id=id))

@client_bp.route('/statistiques')
@login_required
def statistiques_clients():
    """Statistiques détaillées des clients"""
    try:
        # Récupérer toutes les statistiques clients
        client_stats = StatistiqueService.get_client_statistics()
        
        # Calculer des métriques globales
        total_clients = len(client_stats)
        clients_actifs = len([c for c in client_stats if c['nombre_achats'] > 0])
        
        if client_stats:
            montant_total_tous = sum(c['montant_total'] for c in client_stats)
            panier_moyen_global = montant_total_tous / sum(c['nombre_achats'] for c in client_stats if c['nombre_achats'] > 0) if clients_actifs > 0 else 0
        else:
            montant_total_tous = 0
            panier_moyen_global = 0
        
        # Segmentation des clients
        segments = {
            'gros_clients': [c for c in client_stats if c['montant_total'] >= 100000],  # > 100k MGA
            'clients_moyens': [c for c in client_stats if 50000 <= c['montant_total'] < 100000],  # 50k-100k MGA
            'petits_clients': [c for c in client_stats if 0 < c['montant_total'] < 50000],  # < 50k MGA
            'clients_inactifs': [c for c in client_stats if c['montant_total'] == 0]
        }
        
        return render_template('clients.html',
                               show_stats=True,
                               client_stats=client_stats,
                               total_clients=total_clients,
                               clients_actifs=clients_actifs,
                               montant_total_tous=montant_total_tous,
                               panier_moyen_global=panier_moyen_global,
                               segments=segments)
        
    except Exception as e:
        flash(f"Erreur lors du chargement des statistiques: {str(e)}", "error")
        return redirect(url_for('client.list_clients'))

@client_bp.route('/export')
@login_required
def export_clients():
    """Exporte la liste des clients"""
    try:
        from utils.helpers import export_to_csv
        
        clients = Client.query.order_by(Client.nom).all()
        
        # Préparer les données
        data = []
        for client in clients:
            data.append([
                client.nom,
                client.email,
                client.telephone or '',
                client.adresse or '',
                client.date_inscription.strftime('%d/%m/%Y') if client.date_inscription else '',
                client.nombre_achats,
                client.total_achats,
                format_currency(client.total_achats / client.nombre_achats) if client.nombre_achats > 0 else '0 MGA'
            ])
        
        headers = [
            'Nom', 'Email', 'Téléphone', 'Adresse', 'Date inscription',
            'Nombre d\'achats', 'Total achats (MGA)', 'Panier moyen'
        ]
        
        return export_to_csv(data, 'clients.csv', headers)
        
    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "error")
        return redirect(url_for('client.list_clients'))
