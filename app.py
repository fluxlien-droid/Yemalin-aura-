import os
import sqlite3
import secrets
from functools import wraps
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    make_response
)

import cloudinary
import cloudinary.uploader


# =========================================================
# APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)

DB = os.environ.get(
    "DATABASE_PATH",
    "commandes.db"
)

ADMIN_CODE = os.environ.get(
    "ADMIN_CODE",
    "CHANGE-MOI"
)


# =========================================================
# CLOUDINARY
# =========================================================

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)


# =========================================================
# BASE DE DONNÉES
# =========================================================

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def maintenant():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db():

    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            description TEXT DEFAULT '',
            prix REAL NOT NULL,
            image TEXT DEFAULT '',
            video TEXT DEFAULT '',
            media_type TEXT DEFAULT '',
            date TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_nom TEXT NOT NULL,
            telephone TEXT NOT NULL,
            adresse TEXT DEFAULT '',
            total REAL NOT NULL,
            statut TEXT DEFAULT 'Nouvelle',
            client_token TEXT UNIQUE NOT NULL,
            date TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS commande_produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commande_id INTEGER NOT NULL,
            produit_id INTEGER,
            nom TEXT,
            prix REAL,
            quantite INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commande_id INTEGER NOT NULL,
            client_token TEXT NOT NULL,
            client_nom TEXT,
            auteur TEXT NOT NULL,
            message TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages_generaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_token TEXT NOT NULL,
            client_nom TEXT NOT NULL,
            message TEXT NOT NULL,
            reponse TEXT DEFAULT '',
            date TEXT NOT NULL,
            date_reponse TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS publicites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position INTEGER UNIQUE NOT NULL,
            titre TEXT DEFAULT '',
            media_url TEXT DEFAULT '',
            media_type TEXT DEFAULT '',
            lien TEXT DEFAULT '',
            texte TEXT DEFAULT ''
        )
    """)

    c.execute("""
        INSERT OR IGNORE INTO publicites
        (
            position,
            titre,
            media_url,
            media_type,
            lien,
            texte
        )
        VALUES (1, '', '', '', '', '')
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# OUTILS ADMIN
# =========================================================

def admin_connecte():
    return bool(session.get("admin"))


def admin_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not admin_connecte():
            return jsonify({
                "ok": False,
                "message": "Accès administrateur requis."
            }), 401

        return f(*args, **kwargs)

    return wrapper


# =========================================================
# CLIENT TOKEN
# =========================================================

def obtenir_client_token():

    token = request.cookies.get("client_token")

    if not token:
        token = secrets.token_urlsafe(32)

    return token


# =========================================================
# CONNEXION ADMIN
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":

        if admin_connecte():
            return redirect(url_for("admin"))

        return render_template("login.html")

    data = request.get_json(silent=True) or request.form

    code = str(
        data.get("code", "")
    ).strip()

    if not secrets.compare_digest(
        code,
        ADMIN_CODE
    ):
        return jsonify({
            "ok": False,
            "message": "Code administrateur incorrect."
        }), 401

    session.clear()
    session["admin"] = True

    return jsonify({
        "ok": True,
        "message": "Connexion réussie."
    })


# =========================================================
# DÉCONNEXION
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# PAGE ADMIN
# =========================================================

@app.route("/admin")
def admin():

    if not admin_connecte():
        return redirect(
            url_for("admin_login")
        )

    return render_template(
        "admin.html"
    )


# =========================================================
# PAGE BOUTIQUE
# =========================================================

@app.route("/")
def index():

    conn = db()

    produits = conn.execute("""
        SELECT *
        FROM produits
        ORDER BY id DESC
    """).fetchall()

    pubs = conn.execute("""
        SELECT *
        FROM publicites
        WHERE position = 1
        LIMIT 1
    """).fetchall()

    conn.close()

    response = make_response(
        render_template(
            "index.html",
            produits=produits,
            pubs=pubs,
            vapid_public_key=os.environ.get(
                "VAPID_PUBLIC_KEY",
                ""
            )
        )
    )

    # Évite que le navigateur garde une ancienne boutique.
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )

    return response


# =========================================================
# API PRODUITS PUBLICS
# =========================================================

@app.route("/api/produits")
def api_produits():

    conn = db()

    rows = conn.execute("""
        SELECT
            id,
            nom,
            description,
            prix,
            image,
            video,
            media_type,
            date
        FROM produits
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# ADMIN — AJOUTER PRODUIT
# =========================================================

@app.route(
    "/api/admin/produit",
    methods=["POST"]
)
@admin_required
def ajouter_produit():

    nom = (
        request.form.get("nom")
        or ""
    ).strip()

    description = (
        request.form.get("description")
        or ""
    ).strip()

    prix_brut = (
        request.form.get("prix")
        or ""
    ).strip()

    if not nom:
        return jsonify({
            "ok": False,
            "message": "Le nom du produit est obligatoire."
        }), 400

    if not prix_brut:
        return jsonify({
            "ok": False,
            "message": "Le prix est obligatoire."
        }), 400

    try:
        prix = float(prix_brut)
    except (ValueError, TypeError):
        return jsonify({
            "ok": False,
            "message": "Prix invalide."
        }), 400

    if prix < 0:
        return jsonify({
            "ok": False,
            "message": "Le prix ne peut pas être négatif."
        }), 400

    media = request.files.get("media")

    image_url = ""
    video_url = ""
    media_type = ""

    if media and media.filename:

        mime = (
            media.mimetype
            or ""
        ).lower()

        if mime.startswith("image/"):

            try:
                resultat = cloudinary.uploader.upload(
                    media,
                    folder="yemalin-aura/produits",
                    resource_type="image"
                )

                image_url = (
                    resultat.get("secure_url")
                    or ""
                )

                media_type = "image"

            except Exception as e:

                print(
                    "Erreur Cloudinary image:",
                    e
                )

                return jsonify({
                    "ok": False,
                    "message": "Impossible d'envoyer l'image."
                }), 500

        elif mime.startswith("video/"):

            try:
                resultat = cloudinary.uploader.upload(
                    media,
                    folder="yemalin-aura/produits",
                    resource_type="video"
                )

                video_url = (
                    resultat.get("secure_url")
                    or ""
                )

                media_type = "video"

            except Exception as e:

                print(
                    "Erreur Cloudinary vidéo:",
                    e
                )

                return jsonify({
                    "ok": False,
                    "message": "Impossible d'envoyer la vidéo."
                }), 500

        else:

            return jsonify({
                "ok": False,
                "message": "Format de média non supporté."
            }), 400

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produits
        (
            nom,
            description,
            prix,
            image,
            video,
            media_type,
            date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        nom,
        description,
        prix,
        image_url,
        video_url,
        media_type,
        maintenant()
    ))

    produit_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Produit ajouté avec succès.",
        "id": produit_id
    })


# =========================================================
# ADMIN — SUPPRIMER PRODUIT
# =========================================================

@app.route(
    "/api/admin/produit/<int:produit_id>",
    methods=["DELETE"]
)
@admin_required
def supprimer_produit(produit_id):

    conn = db()

    produit = conn.execute("""
        SELECT id
        FROM produits
        WHERE id = ?
    """, (produit_id,)).fetchone()

    if not produit:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Produit introuvable."
        }), 404

    conn.execute("""
        DELETE FROM produits
        WHERE id = ?
    """, (produit_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Produit supprimé."
    })
    # =========================================================
# COMMANDES — CLIENT
# =========================================================

@app.route(
    "/api/commande",
    methods=["POST"]
)
def passer_commande():

    data = request.get_json(
        silent=True
    ) or {}

    client_nom = str(
        data.get("client_nom", "")
    ).strip()

    telephone = str(
        data.get("telephone", "")
    ).strip()

    adresse = str(
        data.get("adresse", "")
    ).strip()

    produits_panier = (
        data.get("produits")
        or data.get("items")
        or []
    )

    if not client_nom:
        return jsonify({
            "ok": False,
            "message": "Votre nom est obligatoire."
        }), 400

    if not telephone:
        return jsonify({
            "ok": False,
            "message": "Votre numéro est obligatoire."
        }), 400

    if not isinstance(
        produits_panier,
        list
    ) or not produits_panier:

        return jsonify({
            "ok": False,
            "message": "Votre panier est vide."
        }), 400

    conn = db()

    lignes = []
    total = 0

    try:

        for item in produits_panier:

            try:
                produit_id = int(
                    item.get("id")
                )
            except Exception:
                continue

            try:
                quantite = int(
                    item.get("quantite", 1)
                )
            except Exception:
                quantite = 1

            if quantite < 1:
                quantite = 1

            produit = conn.execute("""
                SELECT
                    id,
                    nom,
                    prix
                FROM produits
                WHERE id = ?
            """, (
                produit_id,
            )).fetchone()

            if not produit:
                continue

            sous_total = (
                float(produit["prix"])
                * quantite
            )

            total += sous_total

            lignes.append({
                "id": produit["id"],
                "nom": produit["nom"],
                "prix": float(produit["prix"]),
                "quantite": quantite
            })

        if not lignes:

            conn.close()

            return jsonify({
                "ok": False,
                "message": "Aucun produit valide dans le panier."
            }), 400

        client_token = obtenir_client_token()

        # Une ancienne commande peut avoir le même token.
        # On conserve le token du client pour retrouver ses commandes.

        conn.execute("""
            INSERT INTO commandes
            (
                client_nom,
                telephone,
                adresse,
                total,
                statut,
                client_token,
                date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client_nom,
            telephone,
            adresse,
            total,
            "Nouvelle",
            client_token,
            maintenant()
        ))

        commande_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        for ligne in lignes:

            conn.execute("""
                INSERT INTO commande_produits
                (
                    commande_id,
                    produit_id,
                    nom,
                    prix,
                    quantite
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                commande_id,
                ligne["id"],
                ligne["nom"],
                ligne["prix"],
                ligne["quantite"]
            ))

        conn.commit()
        conn.close()

        response = jsonify({
            "ok": True,
            "message": "Commande enregistrée avec succès.",
            "commande_id": commande_id,
            "total": total
        })

        response.set_cookie(
            "client_token",
            client_token,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="Lax"
        )

        return response

    except Exception as e:

        conn.rollback()
        conn.close()

        print(
            "Erreur commande:",
            e
        )

        return jsonify({
            "ok": False,
            "message": "Impossible d'enregistrer la commande."
        }), 500


# =========================================================
# COMMANDES DU CLIENT
# =========================================================

@app.route("/api/mes-commandes")
def mes_commandes():

    token = request.cookies.get(
        "client_token"
    )

    if not token:

        return jsonify([])

    conn = db()

    commandes = conn.execute("""
        SELECT
            id,
            client_nom,
            telephone,
            adresse,
            total,
            statut,
            date
        FROM commandes
        WHERE client_token = ?
        ORDER BY id DESC
    """, (
        token,
    )).fetchall()

    resultat = []

    for commande in commandes:

        produits = conn.execute("""
            SELECT
                produit_id,
                nom,
                prix,
                quantite
            FROM commande_produits
            WHERE commande_id = ?
            ORDER BY id ASC
        """, (
            commande["id"],
        )).fetchall()

        resultat.append({
            "id": commande["id"],
            "client_nom": commande["client_nom"],
            "telephone": commande["telephone"],
            "adresse": commande["adresse"],
            "total": commande["total"],
            "statut": commande["statut"],
            "date": commande["date"],
            "produits": [
                dict(p)
                for p in produits
            ]
        })

    conn.close()

    return jsonify(resultat)


# =========================================================
# ADMIN — TOUTES LES COMMANDES
# =========================================================

@app.route("/api/admin/commandes")
@admin_required
def admin_commandes():

    conn = db()

    commandes = conn.execute("""
        SELECT
            id,
            client_nom,
            telephone,
            adresse,
            total,
            statut,
            client_token,
            date
        FROM commandes
        ORDER BY id DESC
    """).fetchall()

    resultat = []

    for commande in commandes:

        produits = conn.execute("""
            SELECT
                produit_id,
                nom,
                prix,
                quantite
            FROM commande_produits
            WHERE commande_id = ?
            ORDER BY id ASC
        """, (
            commande["id"],
        )).fetchall()

        resultat.append({
            **dict(commande),
            "produits": [
                dict(p)
                for p in produits
            ]
        })

    conn.close()

    return jsonify(resultat)


# =========================================================
# ADMIN — STATUT COMMANDE
# =========================================================

@app.route(
    "/api/admin/commande/<int:commande_id>/statut",
    methods=["POST"]
)
@admin_required
def changer_statut(commande_id):

    data = request.get_json(
        silent=True
    ) or {}

    statut = str(
        data.get("statut", "")
    ).strip()

    statuts_valides = [
        "Nouvelle",
        "Confirmée",
        "En livraison",
        "Terminée",
        "Annulée"
    ]

    if statut not in statuts_valides:

        return jsonify({
            "ok": False,
            "message": "Statut invalide."
        }), 400

    conn = db()

    existe = conn.execute("""
        SELECT id
        FROM commandes
        WHERE id = ?
    """, (
        commande_id,
    )).fetchone()

    if not existe:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Commande introuvable."
        }), 404

    conn.execute("""
        UPDATE commandes
        SET statut = ?
        WHERE id = ?
    """, (
        statut,
        commande_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Statut mis à jour."
    })


# =========================================================
# DASHBOARD ADMIN
# =========================================================

@app.route("/api/admin/dashboard")
@admin_required
def admin_dashboard():

    conn = db()

    commandes = conn.execute("""
        SELECT COUNT(*) AS total
        FROM commandes
    """).fetchone()["total"]

    clients = conn.execute("""
        SELECT COUNT(DISTINCT client_token) AS total
        FROM commandes
    """).fetchone()["total"]

    revenus = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM commandes
        WHERE statut != 'Annulée'
    """).fetchone()["total"]

    livraisons = conn.execute("""
        SELECT COUNT(*) AS total
        FROM commandes
        WHERE statut = 'En livraison'
    """).fetchone()["total"]

    nouvelles = conn.execute("""
        SELECT COUNT(*) AS total
        FROM commandes
        WHERE statut = 'Nouvelle'
    """).fetchone()["total"]

    conn.close()

    return jsonify({
        "ok": True,
        "stats": {
            "commandes": commandes,
            "clients": clients,
            "revenus": float(revenus or 0),
            "livraisons": livraisons,
            "nouvelles": nouvelles
        }
    })


# =========================================================
# CHAT CLIENT — LIRE
# =========================================================

@app.route(
    "/api/chat/<int:commande_id>",
    methods=["GET"]
)
def chat_client(commande_id):

    token = request.cookies.get(
        "client_token"
    )

    if not token:

        return jsonify({
            "ok": False,
            "message": "Client non identifié."
        }), 401

    conn = db()

    commande = conn.execute("""
        SELECT
            id,
            client_nom,
            client_token
        FROM commandes
        WHERE id = ?
        AND client_token = ?
    """, (
        commande_id,
        token
    )).fetchone()

    if not commande:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Commande introuvable."
        }), 404

    messages = conn.execute("""
        SELECT
            id,
            client_nom,
            auteur,
            message,
            date
        FROM messages
        WHERE commande_id = ?
        AND client_token = ?
        ORDER BY id ASC
    """, (
        commande_id,
        token
    )).fetchall()

    conn.close()

    return jsonify({
        "ok": True,
        "commande": dict(commande),
        "messages": [
            dict(m)
            for m in messages
        ]
    })


# =========================================================
# CHAT CLIENT — ENVOYER
# =========================================================

@app.route(
    "/api/chat/<int:commande_id>",
    methods=["POST"]
)
def envoyer_chat_client(commande_id):

    token = request.cookies.get(
        "client_token"
    )

    if not token:

        return jsonify({
            "ok": False,
            "message": "Client non identifié."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:

        return jsonify({
            "ok": False,
            "message": "Message vide."
        }), 400

    if len(message) > 2000:

        return jsonify({
            "ok": False,
            "message": "Message trop long."
        }), 400

    conn = db()

    commande = conn.execute("""
        SELECT
            client_nom,
            client_token
        FROM commandes
        WHERE id = ?
        AND client_token = ?
    """, (
        commande_id,
        token
    )).fetchone()

    if not commande:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Commande introuvable."
        }), 404

    conn.execute("""
        INSERT INTO messages
        (
            commande_id,
            client_token,
            client_nom,
            auteur,
            message,
            date
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        commande_id,
        token,
        commande["client_nom"],
        "Client",
        message,
        maintenant()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Message envoyé."
        # =========================================================
# CHAT ADMIN — LIRE
# =========================================================

@app.route(
    "/api/admin/chat/<int:commande_id>",
    methods=["GET"]
)
@admin_required
def chat_admin(commande_id):

    conn = db()

    commande = conn.execute("""
        SELECT
            id,
            client_nom
        FROM commandes
        WHERE id = ?
    """, (
        commande_id,
    )).fetchone()

    if not commande:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Commande introuvable."
        }), 404

    messages = conn.execute("""
        SELECT
            id,
            client_nom,
            auteur,
            message,
            date
        FROM messages
        WHERE commande_id = ?
        ORDER BY id ASC
    """, (
        commande_id,
    )).fetchall()

    conn.close()

    return jsonify({
        "ok": True,
        "commande": dict(commande),
        "messages": [
            dict(m)
            for m in messages
        ]
    })


# =========================================================
# CHAT ADMIN — RÉPONDRE
# =========================================================

@app.route(
    "/api/chat/<int:commande_id>",
    methods=["POST"]
)
@admin_required
def envoyer_chat_admin(commande_id):

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:

        return jsonify({
            "ok": False,
            "message": "Message vide."
        }), 400

    if len(message) > 2000:

        return jsonify({
            "ok": False,
            "message": "Message trop long."
        }), 400

    conn = db()

    commande = conn.execute("""
        SELECT
            client_token,
            client_nom
        FROM commandes
        WHERE id = ?
    """, (
        commande_id,
    )).fetchone()

    if not commande:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Commande introuvable."
        }), 404

    conn.execute("""
        INSERT INTO messages
        (
            commande_id,
            client_token,
            client_nom,
            auteur,
            message,
            date
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        commande_id,
        commande["client_token"],
        commande["client_nom"],
        "Admin",
        message,
        maintenant()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Réponse envoyée."
    })


# =========================================================
# MESSAGES GÉNÉRAUX — CLIENT
# =========================================================

@app.route(
    "/api/messages-general",
    methods=["POST"]
)
def message_general():

    data = request.get_json(
        silent=True
    ) or {}

    nom = str(
        data.get("nom", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    if not nom:

        return jsonify({
            "ok": False,
            "message": "Votre nom est obligatoire."
        }), 400

    if not message:

        return jsonify({
            "ok": False,
            "message": "Votre message est obligatoire."
        }), 400

    if len(message) > 3000:

        return jsonify({
            "ok": False,
            "message": "Message trop long."
        }), 400

    token = obtenir_client_token()

    conn = db()

    conn.execute("""
        INSERT INTO messages_generaux
        (
            client_token,
            client_nom,
            message,
            reponse,
            date
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        token,
        nom,
        message,
        "",
        maintenant()
    ))

    conn.commit()
    conn.close()

    response = jsonify({
        "ok": True,
        "message": "Votre message a été envoyé."
    })

    response.set_cookie(
        "client_token",
        token,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="Lax"
    )

    return response


# =========================================================
# ADMIN — MESSAGES GÉNÉRAUX
# =========================================================

@app.route("/api/admin/messages-generaux")
@admin_required
def admin_messages_generaux():

    conn = db()

    rows = conn.execute("""
        SELECT
            id,
            client_token,
            client_nom,
            message,
            reponse,
            date,
            date_reponse
        FROM messages_generaux
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# ADMIN — RÉPONDRE À UN MESSAGE GÉNÉRAL
# =========================================================

@app.route(
    "/api/admin/messages-generaux/<int:message_id>",
    methods=["POST"]
)
@admin_required
def repondre_message_general(message_id):

    data = request.get_json(
        silent=True
    ) or {}

    reponse = str(
        data.get("reponse", "")
    ).strip()

    if not reponse:

        return jsonify({
            "ok": False,
            "message": "Réponse vide."
        }), 400

    conn = db()

    existe = conn.execute("""
        SELECT id
        FROM messages_generaux
        WHERE id = ?
    """, (
        message_id,
    )).fetchone()

    if not existe:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Message introuvable."
        }), 404

    conn.execute("""
        UPDATE messages_generaux
        SET
            reponse = ?,
            date_reponse = ?
        WHERE id = ?
    """, (
        reponse,
        maintenant(),
        message_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Réponse enregistrée."
    })


# =========================================================
# PUBLICITÉ — ADMIN
# =========================================================

@app.route(
    "/api/admin/publicite",
    methods=["POST"]
)
@admin_required
def enregistrer_publicite():

    titre = (
        request.form.get("titre")
        or ""
    ).strip()

    lien = (
        request.form.get("lien")
        or ""
    ).strip()

    texte = (
        request.form.get("texte")
        or ""
    ).strip()

    position = 1

    media = request.files.get("media")

    media_url = ""
    media_type = ""

    if media and media.filename:

        mime = (
            media.mimetype
            or ""
        ).lower()

        try:

            if mime.startswith("image/"):

                resultat = cloudinary.uploader.upload(
                    media,
                    folder="yemalin-aura/publicites",
                    resource_type="image"
                )

                media_url = (
                    resultat.get("secure_url")
                    or ""
                )

                media_type = "image"

            elif mime.startswith("video/"):

                resultat = cloudinary.uploader.upload(
                    media,
                    folder="yemalin-aura/publicites",
                    resource_type="video"
                )

                media_url = (
                    resultat.get("secure_url")
                    or ""
                )

                media_type = "video"

            else:

                return jsonify({
                    "ok": False,
                    "message": "Format de publicité non supporté."
                }), 400

        except Exception as e:

            print(
                "Erreur Cloudinary publicité:",
                e
            )

            return jsonify({
                "ok": False,
                "message": "Impossible d'envoyer la publicité."
            }), 500

    conn = db()

    ancienne = conn.execute("""
        SELECT
            media_url,
            media_type
        FROM publicites
        WHERE position = ?
    """, (
        position,
    )).fetchone()

    # Si aucun nouveau média n'est envoyé,
    # on conserve celui qui existe déjà.
    if not media_url and ancienne:

        media_url = ancienne["media_url"] or ""
        media_type = ancienne["media_type"] or ""

    conn.execute("""
        INSERT INTO publicites
        (
            position,
            titre,
            media_url,
            media_type,
            lien,
            texte
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(position)
        DO UPDATE SET
            titre = excluded.titre,
            media_url = excluded.media_url,
            media_type = excluded.media_type,
            lien = excluded.lien,
            texte = excluded.texte
    """, (
        position,
        titre,
        media_url,
        media_type,
        lien,
        texte
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Publicité enregistrée."
    })


# =========================================================
# PUBLICITÉ — ADMIN — SUPPRIMER
# =========================================================

@app.route(
    "/api/admin/publicite",
    methods=["DELETE"]
)
@admin_required
def supprimer_publicite():

    conn = db()

    conn.execute("""
        UPDATE publicites
        SET
            titre = '',
            media_url = '',
            media_type = '',
            lien = '',
            texte = ''
        WHERE position = 1
    """)

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Publicité supprimée."
    })


# =========================================================
# PUBLICITÉ — API PUBLIQUE
# =========================================================

@app.route("/api/publicite")
def api_publicite():

    conn = db()

    pub = conn.execute("""
        SELECT
            id,
            position,
            titre,
            media_url,
            media_type,
            lien,
            texte
        FROM publicites
        WHERE position = 1
        LIMIT 1
    """).fetchone()

    conn.close()

    if not pub:
        return jsonify({
            "ok": True,
            "publicite": None
        })

    return jsonify({
        "ok": True,
        "publicite": dict(pub)
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    try:

        conn = db()

        conn.execute(
            "SELECT 1"
        ).fetchone()

        conn.close()

        return jsonify({
            "ok": True,
            "service": "Yemalin Aura",
            "database": True
        })

    except Exception as e:

        print(
            "Health error:",
            e
        )

        return jsonify({
            "ok": False,
            "service": "Yemalin Aura",
            "database": False
        }), 500


# =========================================================
# ERREUR 404 API
# =========================================================

@app.errorhandler(404)
def page_introuvable(error):

    if request.path.startswith("/api/"):

        return jsonify({
            "ok": False,
            "message": "Route API introuvable."
        }), 404

    return error


# =========================================================
# ERREUR 500
# =========================================================

@app.errorhandler(500)
def erreur_serveur(error):

    if request.path.startswith("/api/"):

        return jsonify({
            "ok": False,
            "message": "Erreur interne du serveur."
        }), 500

    return error


# =========================================================
# DÉMARRAGE
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
    })
