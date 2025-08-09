from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

class AuthUtils:
    """Utilitaires pour l'authentification"""
    
    @staticmethod
    def login_required(f):
        """Décorateur pour exiger une authentification"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('main.login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def is_admin_required(f):
        """Décorateur pour exiger des droits administrateur"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('main.login'))
            
            # Pour l'instant, tous les utilisateurs authentifiés sont admins
            # Cette logique peut être étendue plus tard
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def get_current_user_info():
        """Retourne les informations de l'utilisateur courant"""
        if current_user.is_authenticated:
            return {
                'id': current_user.id,
                'nom': current_user.nom,
                'email': current_user.email,
                'authenticated': True
            }
        return {'authenticated': False}
    
    @staticmethod
    def check_permissions(action, resource=None):
        """Vérifie les permissions pour une action donnée"""
        if not current_user.is_authenticated:
            return False
        
        # Pour l'instant, tous les utilisateurs authentifiés ont toutes les permissions
        # Cette logique peut être étendue avec un système de rôles plus complexe
        permissions = {
            'view_products': True,
            'create_product': True,
            'edit_product': True,
            'delete_product': True,
            'view_sales': True,
            'create_sale': True,
            'cancel_sale': True,
            'view_purchases': True,
            'create_purchase': True,
            'cancel_purchase': True,
            'view_clients': True,
            'view_statistics': True,
            'export_data': True
        }
        
        return permissions.get(action, False)
