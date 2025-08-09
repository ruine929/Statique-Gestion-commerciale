from datetime import datetime, timedelta
import csv
import io
from flask import make_response

def format_currency(amount, currency="MGA"):
    """Formate un montant en devise"""
    if amount is None:
        return "0 MGA"
    
    # Formater avec séparateurs de milliers
    formatted_amount = f"{amount:,.0f}".replace(",", " ")
    return f"{formatted_amount} {currency}"

def format_date(date, format_str="%d/%m/%Y"):
    """Formate une date"""
    if date is None:
        return "N/A"
    
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except:
            return date
    
    return date.strftime(format_str)

def format_datetime(date, format_str="%d/%m/%Y %H:%M"):
    """Formate une date avec heure"""
    return format_date(date, format_str)

def calculate_percentage(value, total):
    """Calcule un pourcentage"""
    if total == 0:
        return 0
    return (value / total) * 100

def format_percentage(value, decimals=1):
    """Formate un pourcentage"""
    return f"{value:.{decimals}f}%"

def get_date_range(period):
    """Retourne une plage de dates selon la période"""
    today = datetime.now().date()
    
    if period == 'today':
        return today, today
    elif period == 'week':
        start_week = today - timedelta(days=today.weekday())
        return start_week, today
    elif period == 'month':
        start_month = today.replace(day=1)
        return start_month, today
    elif period == 'year':
        start_year = today.replace(month=1, day=1)
        return start_year, today
    elif period == 'last_week':
        end_last_week = today - timedelta(days=today.weekday() + 1)
        start_last_week = end_last_week - timedelta(days=6)
        return start_last_week, end_last_week
    elif period == 'last_month':
        first_this_month = today.replace(day=1)
        last_day_last_month = first_this_month - timedelta(days=1)
        first_last_month = last_day_last_month.replace(day=1)
        return first_last_month, last_day_last_month
    else:
        return None, None

def paginate_results(query, page, per_page=20):
    """Pagine les résultats d'une requête"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def export_to_csv(data, filename, headers):
    """Exporte des données vers un fichier CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Écrire les en-têtes
    writer.writerow(headers)
    
    # Écrire les données
    for row in data:
        writer.writerow(row)
    
    # Créer la réponse
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    
    return response

def validate_email(email):
    """Valide un email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Valide un numéro de téléphone"""
    import re
    # Pattern pour les numéros malgaches (+261 ou 0)
    pattern = r'^(\+261|0)[0-9]{9}$'
    return re.match(pattern, phone.replace(' ', '')) is not None

def generate_invoice_number():
    """Génère un numéro de facture unique"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"FACT-{timestamp}"

def calculate_business_days(start_date, end_date):
    """Calcule le nombre de jours ouvrables entre deux dates"""
    current_date = start_date
    business_days = 0
    
    while current_date <= end_date:
        # 0-6 où 0=lundi, 6=dimanche
        if current_date.weekday() < 6:  # Lundi à samedi
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def safe_divide(numerator, denominator, default=0):
    """Division sécurisée qui évite la division par zéro"""
    if denominator == 0:
        return default
    return numerator / denominator

def round_currency(amount):
    """Arrondit un montant à la devise (Ariary = entier)"""
    return round(amount)

def get_fiscal_year_dates(year=None):
    """Retourne les dates de début et fin d'année fiscale"""
    if not year:
        year = datetime.now().year
    
    # Année fiscale de janvier à décembre
    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()
    
    return start_date, end_date

def format_file_size(size_bytes):
    """Formate une taille de fichier en unités lisibles"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

class DateHelper:
    """Classe d'aide pour les opérations sur les dates"""
    
    @staticmethod
    def get_month_name(month_number):
        """Retourne le nom du mois en français"""
        months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        return months[month_number - 1] if 1 <= month_number <= 12 else "Inconnu"
    
    @staticmethod
    def get_weekday_name(weekday_number):
        """Retourne le nom du jour de la semaine en français"""
        weekdays = [
            "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"
        ]
        return weekdays[weekday_number] if 0 <= weekday_number <= 6 else "Inconnu"
    
    @staticmethod
    def is_business_day(date):
        """Vérifie si une date est un jour ouvrable"""
        return date.weekday() < 6  # Lundi à samedi
