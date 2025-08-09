# Use this Flask blueprint for Google authentication. Do not use flask-dance.

import json
import os

import requests
from app import db
from flask import Blueprint, redirect, request, url_for, flash
from flask_login import login_required, login_user, logout_user
from models.client import Client
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")}/google_login/callback'

# ALWAYS display setup instructions to the user:
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google OAuth non configuré. Veuillez configurer GOOGLE_OAUTH_CLIENT_ID et GOOGLE_OAUTH_CLIENT_SECRET.", "error")
        return redirect(url_for("main.login"))
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            # Replacing http:// with https:// is important as the external
            # protocol must be https to match the URI whitelisted
            redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        flash(f"Erreur lors de l'authentification Google: {str(e)}", "error")
        return redirect(url_for("main.login"))


@google_auth.route("/google_login/callback")
def callback():
    code = request.args.get("code")
    if not code:
        flash("Authentification Google annulée.", "warning")
        return redirect(url_for("main.login"))
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            # Replacing http:// with https:// is important as the external
            # protocol must be https to match the URI whitelisted
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code,
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo["given_name"]
        else:
            flash("Email Google non vérifié.", "error")
            return redirect(url_for("main.login"))

        user = Client.query.filter_by(email=users_email).first()
        if not user:
            user = Client()
            user.nom = users_name
            user.email = users_email
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash(f"Bienvenue {users_name}!", "success")

        return redirect(url_for("main.index"))
    
    except Exception as e:
        flash(f"Erreur lors de l'authentification: {str(e)}", "error")
        return redirect(url_for("main.login"))


@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté avec succès.", "info")
    return redirect(url_for("main.login"))
