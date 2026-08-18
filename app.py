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
    url_for
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
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def init_db():

    conn = db()
    c = conn.cursor()

    # =====================================================
    # PRODUITS
    # =====================================================

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

    # =====================================================
    # COMMANDES
    # =====================================================

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

    # =====================================================
    # PRODUITS COMMANDES
    # =====================================================

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

    # =====================================================
    # CHAT
    # =====================================================

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

    # =====================================================
    # MESSAGES GÉNÉRAUX
    # =====================================================

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

    # =====================================================
    # PUBLICITÉS
    # =====================================================

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
        VALUES (
            1,
            '',
            '',
            '',
            '',
            ''
        )
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
# CONNEXION ADMIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "GET":

        if admin_connecte():
            return redirect(
                url_for("admin")
            )

        return render_template(
            "login.html"
        )

    data = request.get_json(
        silent=True
    )

    if not data:
        data = request.form

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

    session.pop(
        "admin",
        None
    )

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
# PAGE ACCUEIL
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

    return render_template(
        "index.html",
        produits=produits,
        pubs=pubs
    )


# =========================================================
# API PRODUITS
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
# Compatible avec admin.html :
# name="nom"
# name="prix"
# name="description"
# name="media"
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

    # =====================================================
    # MÉDIA
    # =====================================================

    if media and media.filename:

        mime = (
            media.mimetype
            or ""
        ).lower()

        # IMAGE
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
                    "Cloudinary image:",
                    e
                )

                return jsonify({
                    "ok": False,
                    "message": "Impossible d'envoyer l'image."
                }), 500

        # VIDÉO
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
                    "Cloudinary vidéo:",
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

    # =====================================================
    # ENREGISTREMENT
    # =====================================================

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
    """, (
        produit_id,
    )).fetchone()

    if not produit:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Produit introuvable."
        }), 404

    conn.execute("""
        DELETE FROM produits
        WHERE id = ?
    """, (
        produit_id,
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Produit supprimé."
    })


# =========================================================
# FIN PARTIE 1
# =========================================================
# =========================================================
# CRÉER UNE COMMANDE
# =========================================================

@app.route(
    "/api/commande",
    methods=["POST"]
)
def creer_commande():

    data = request.get_json(
        silent=True
    ) or {}

    client_nom = (
        data.get("client_nom")
        or ""
    ).strip()

    telephone = (
        data.get("telephone")
        or ""
    ).strip()

    adresse = (
        data.get("adresse")
        or ""
    ).strip()

    panier = data.get("panier") or []

    if not client_nom:

        return jsonify({
            "ok": False,
            "message": "Nom obligatoire."
        }), 400

    if not telephone:

        return jsonify({
            "ok": False,
            "message": "Téléphone obligatoire."
        }), 400

    if not panier:

        return jsonify({
            "ok": False,
            "message": "Le panier est vide."
        }), 400

    total = 0

    for produit in panier:

        try:

            prix = float(
                produit.get("prix", 0)
            )

            quantite = int(
                produit.get("quantite", 0)
            )

        except (ValueError, TypeError):

            return jsonify({
                "ok": False,
                "message": "Produit invalide."
            }), 400

        if prix < 0 or quantite <= 0:

            return jsonify({
                "ok": False,
                "message": "Prix ou quantité invalide."
            }), 400

        total += prix * quantite

    client_token = secrets.token_urlsafe(32)

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
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

    commande_id = cursor.lastrowid

    # IMPORTANT :
    # commande_id doit être le premier paramètre.
    for produit in panier:

        cursor.execute("""
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
            produit.get("id"),
            produit.get("nom"),
            produit.get("prix"),
            produit.get("quantite")
        ))

    conn.commit()
    conn.close()

    session["client_token"] = client_token

    return jsonify({
        "ok": True,
        "message": "Commande enregistrée.",
        "commande_id": commande_id,
        "client_token": client_token
    })


# =========================================================
# MES COMMANDES
# =========================================================

@app.route("/api/mes-commandes")
def mes_commandes():

    token = session.get("client_token")

    if not token:

        return jsonify({
            "ok": True,
            "commandes": []
        })

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM commandes
        WHERE client_token = ?
        ORDER BY id DESC
    """, (
        token,
    )).fetchall()

    conn.close()

    return jsonify({
        "ok": True,
        "commandes": [
            dict(x)
            for x in rows
        ]
    })


# =========================================================
# DÉTAIL COMMANDE
# =========================================================

@app.route(
    "/api/commande/<int:commande_id>"
)
def detail_commande(commande_id):

    conn = db()

    commande = conn.execute("""
        SELECT *
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

    if not admin_connecte():

        token = session.get("client_token")

        if commande["client_token"] != token:

            conn.close()

            return jsonify({
                "ok": False,
                "message": "Accès refusé."
            }), 403

    produits = conn.execute("""
        SELECT *
        FROM commande_produits
        WHERE commande_id = ?
        ORDER BY id ASC
    """, (
        commande_id,
    )).fetchall()

    messages = conn.execute("""
        SELECT *
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
        "produits": [
            dict(x)
            for x in produits
        ],
        "messages": [
            dict(x)
            for x in messages
        ]
    })


# =========================================================
# CHAT CLIENT / ADMIN
# =========================================================

@app.route(
    "/api/chat/<int:commande_id>",
    methods=["POST"]
)
def envoyer_chat(commande_id):

    data = request.get_json(
        silent=True
    ) or {}

    message = (
        data.get("message")
        or ""
    ).strip()

    if not message:

        return jsonify({
            "ok": False,
            "message": "Message vide."
        }), 400

    conn = db()

    commande = conn.execute("""
        SELECT *
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

    if admin_connecte():

        auteur = "Admin"

    else:

        token = session.get(
            "client_token"
        )

        if not token:

            conn.close()

            return jsonify({
                "ok": False,
                "message": "Session client introuvable."
            }), 401

        if commande["client_token"] != token:

            conn.close()

            return jsonify({
                "ok": False,
                "message": "Accès refusé."
            }), 403

        auteur = "Client"

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
        auteur,
        message,
        maintenant()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Message envoyé."
    })


# =========================================================
# ADMIN — DASHBOARD
# Compatible avec admin.html
# =========================================================

@app.route(
    "/api/admin/dashboard"
)
@admin_required
def admin_dashboard():

    conn = db()

    commandes = conn.execute("""
        SELECT COUNT(*)
        FROM commandes
    """).fetchone()[0]

    clients = conn.execute("""
        SELECT COUNT(DISTINCT telephone)
        FROM commandes
    """).fetchone()[0]

    revenus = conn.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM commandes
        WHERE statut != 'Annulée'
    """).fetchone()[0]

    livraisons = conn.execute("""
        SELECT COUNT(*)
        FROM commandes
        WHERE statut = 'En livraison'
    """).fetchone()[0]

    nouvelles = conn.execute("""
        SELECT COUNT(*)
        FROM commandes
        WHERE statut = 'Nouvelle'
    """).fetchone()[0]

    conn.close()

    return jsonify({
        "ok": True,
        "stats": {
            "commandes": commandes,
            "clients": clients,
            "revenus": revenus,
            "livraisons": livraisons,
            "nouvelles": nouvelles
        }
    })


# =========================================================
# ADMIN — COMMANDES
# =========================================================

@app.route(
    "/api/admin/commandes"
)
@admin_required
def admin_commandes():

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM commandes
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(x)
        for x in rows
    ])


# =========================================================
# ADMIN — CHAT D'UNE COMMANDE
# =========================================================

@app.route(
    "/api/admin/chat/<int:commande_id>"
)
@admin_required
def admin_chat(commande_id):

    conn = db()

    commande = conn.execute("""
        SELECT *
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
        SELECT *
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
            dict(x)
            for x in messages
        ]
    })


# =========================================================
# ADMIN — CHANGER STATUT
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

    statut = (
        data.get("statut")
        or ""
    ).strip()

    statuts = [
        "Nouvelle",
        "Confirmée",
        "En livraison",
        "Terminée",
        "Annulée"
    ]

    if statut not in statuts:

        return jsonify({
            "ok": False,
            "message": "Statut invalide."
        }), 400

    conn = db()

    commande = conn.execute("""
        SELECT id
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
# MESSAGES GÉNÉRAUX — CLIENT
# =========================================================

@app.route(
    "/api/messages-generaux",
    methods=["POST"]
)
def envoyer_message_general():

    data = request.get_json(
        silent=True
    ) or {}

    client_nom = (
        data.get("client_nom")
        or ""
    ).strip()

    message = (
        data.get("message")
        or ""
    ).strip()

    if not client_nom:

        return jsonify({
            "ok": False,
            "message": "Nom obligatoire."
        }), 400

    if not message:

        return jsonify({
            "ok": False,
            "message": "Message vide."
        }), 400

    token = session.get(
        "client_token"
    )

    if not token:

        token = secrets.token_urlsafe(32)

        session["client_token"] = token

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
        client_nom,
        message,
        "",
        maintenant()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Message envoyé."
    })


# =========================================================
# MESSAGES GÉNÉRAUX — CLIENT
# =========================================================

@app.route(
    "/api/messages-generaux",
    methods=["GET"]
)
def lire_messages_generaux():

    token = session.get(
        "client_token"
    )

    if not token:

        return jsonify({
            "ok": True,
            "messages": []
        })

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM messages_generaux
        WHERE client_token = ?
        ORDER BY id DESC
    """, (
        token,
    )).fetchall()

    conn.close()

    return jsonify({
        "ok": True,
        "messages": [
            dict(x)
            for x in rows
        ]
    })


# =========================================================
# ADMIN — MESSAGES GÉNÉRAUX
# =========================================================

@app.route(
    "/api/admin/messages"
)
@admin_required
def admin_messages():

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM messages_generaux
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(x)
        for x in rows
    ])


# =========================================================
# ADMIN — RÉPONDRE MESSAGE GÉNÉRAL
# =========================================================

@app.route(
    "/api/admin/message-general/<int:message_id>/repondre",
    methods=["POST"]
)
@admin_required
def repondre_message_general(message_id):

    data = request.get_json(
        silent=True
    ) or {}

    reponse = (
        data.get("reponse")
        or ""
    ).strip()

    if not reponse:

        return jsonify({
            "ok": False,
            "message": "Réponse vide."
        }), 400

    conn = db()

    message = conn.execute("""
        SELECT *
        FROM messages_generaux
        WHERE id = ?
    """, (
        message_id,
    )).fetchone()

    if not message:

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
        "message": "Réponse envoyée."
    })


# =========================================================
# FIN PARTIE 2
# =========================================================
# =========================================================
# PUBLICITÉS — PUBLIC
# =========================================================

@app.route(
    "/api/publicites"
)
def api_publicites():

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM publicites
        ORDER BY position ASC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(x)
        for x in rows
    ])


# =========================================================
# ADMIN — AJOUTER / MODIFIER PUBLICITÉ
#
# Compatible avec admin.html :
#
# name="position"
# name="titre"
# name="lien"
# name="texte"
# name="media"
# =========================================================

@app.route(
    "/api/admin/publicite",
    methods=["POST"]
)
@admin_required
def modifier_publicite():

    position = (
        request.form.get(
            "position",
            "1"
        )
        or "1"
    ).strip()

    try:
        position = int(position)
    except (ValueError, TypeError):
        position = 1

    if position < 1:
        position = 1

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

    media = request.files.get(
        "media"
    )

    media_url = ""
    media_type = ""

    # =====================================================
    # UPLOAD NOUVEAU MÉDIA
    # =====================================================

    if media and media.filename:

        mime = (
            media.mimetype
            or ""
        ).lower()

        # IMAGE
        if mime.startswith("image/"):

            try:

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

            except Exception as e:

                print(
                    "Cloudinary publicité image:",
                    e
                )

                return jsonify({
                    "ok": False,
                    "message": "Impossible d'envoyer l'image."
                }), 500

        # VIDÉO
        elif mime.startswith("video/"):

            try:

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

            except Exception as e:

                print(
                    "Cloudinary publicité vidéo:",
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

    # =====================================================
    # VÉRIFIER SI LA PUBLICITÉ EXISTE
    # =====================================================

    ancienne = conn.execute("""
        SELECT *
        FROM publicites
        WHERE position = ?
    """, (
        position,
    )).fetchone()

    # =====================================================
    # EXISTANTE
    # =====================================================

    if ancienne:

        if media_url:

            conn.execute("""
                UPDATE publicites
                SET
                    titre = ?,
                    media_url = ?,
                    media_type = ?,
                    lien = ?,
                    texte = ?
                WHERE position = ?
            """, (
                titre,
                media_url,
                media_type,
                lien,
                texte,
                position
            ))

        else:

            # On conserve l'ancien média
            conn.execute("""
                UPDATE publicites
                SET
                    titre = ?,
                    lien = ?,
                    texte = ?
                WHERE position = ?
            """, (
                titre,
                lien,
                texte,
                position
            ))

    # =====================================================
    # NOUVELLE PUBLICITÉ
    # =====================================================

    else:

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
# ADMIN — SUPPRIMER PUBLICITÉ
# =========================================================

@app.route(
    "/api/admin/publicite/supprimer",
    methods=["POST", "DELETE"]
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
# TEST SERVEUR
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "ok": True,
        "service": "Yemalin Aura"
    })


# =========================================================
# LANCEMENT
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
                )
