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

VAPID_PUBLIC_KEY = os.environ.get(
    "VAPID_PUBLIC_KEY",
    ""
)

VAPID_PRIVATE_KEY = os.environ.get(
    "VAPID_PRIVATE_KEY",
    ""
)

VAPID_EMAIL = os.environ.get(
    "VAPID_EMAIL",
    "mailto:admin@example.com"
)


# =========================================================
# CLOUDINARY
# =========================================================

cloudinary.config(
    cloud_name=os.environ.get(
        "CLOUDINARY_CLOUD_NAME"
    ),
    api_key=os.environ.get(
        "CLOUDINARY_API_KEY"
    ),
    api_secret=os.environ.get(
        "CLOUDINARY_API_SECRET"
    ),
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

    # -----------------------------------------------------
    # PRODUITS
    # -----------------------------------------------------

    c.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            description TEXT,
            prix REAL NOT NULL,
            image TEXT,
            video TEXT,
            media_type TEXT,
            date TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # MIGRATION ANCIENNE TABLE PRODUITS
    # -----------------------------------------------------

    colonnes = [
        row["name"]
        for row in c.execute(
            "PRAGMA table_info(produits)"
        ).fetchall()
    ]

    if "video" not in colonnes:

        c.execute("""
            ALTER TABLE produits
            ADD COLUMN video TEXT
        """)

    if "media_type" not in colonnes:

        c.execute("""
            ALTER TABLE produits
            ADD COLUMN media_type TEXT
        """)

    # -----------------------------------------------------
    # COMMANDES
    # -----------------------------------------------------

    c.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_nom TEXT NOT NULL,
            telephone TEXT NOT NULL,
            adresse TEXT,
            total REAL NOT NULL,
            statut TEXT DEFAULT 'Nouvelle',
            client_token TEXT UNIQUE NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # PRODUITS DES COMMANDES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # MESSAGES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # MESSAGES GÉNÉRAUX
    # -----------------------------------------------------

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages_generaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_token TEXT NOT NULL,
            client_nom TEXT NOT NULL,
            message TEXT NOT NULL,
            reponse TEXT,
            date TEXT NOT NULL,
            date_reponse TEXT
        )
    """)

    # -----------------------------------------------------
    # PUBLICITÉS
    # -----------------------------------------------------

    c.execute("""
        CREATE TABLE IF NOT EXISTS publicites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position INTEGER UNIQUE NOT NULL,
            titre TEXT,
            media_url TEXT,
            media_type TEXT,
            lien TEXT,
            texte TEXT
        )
    """)

    # -----------------------------------------------------
    # NOTIFICATIONS PUSH
    # -----------------------------------------------------

    c.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_token TEXT,
            endpoint TEXT UNIQUE NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # UNE SEULE PUBLICITÉ
    # -----------------------------------------------------

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


# =========================================================
# INITIALISATION
# =========================================================

init_db()


# =========================================================
# VARIABLES POUR LES TEMPLATES
# =========================================================

@app.context_processor
def inject_variables():

    return {
        "vapid_public_key": VAPID_PUBLIC_KEY
    }


# =========================================================
# ADMIN
# =========================================================

def admin_required(f):

    @wraps(f)
    def wrapper(*args, **kwargs):

        if not session.get("admin"):

            return jsonify({
                "ok": False,
                "message": "Accès administrateur requis."
            }), 401

        return f(*args, **kwargs)

    return wrapper


@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "GET":

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
            "message": "Code incorrect."
        }), 401

    session.clear()
    session["admin"] = True

    return jsonify({
        "ok": True
    })


@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        url_for("admin_login")
    )


@app.route("/admin")
def admin():

    if not session.get("admin"):

        return redirect(
            url_for("admin_login")
        )

    return render_template(
        "admin.html"
    )


# =========================================================
# ACCUEIL
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
        pubs=pubs,
        vapid_public_key=VAPID_PUBLIC_KEY
    )


# =========================================================
# PRODUITS
# =========================================================

@app.route("/api/produits")
def api_produits():

    conn = db()

    rows = conn.execute("""
        SELECT *
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
# IMAGE OU VIDÉO
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

    prix = request.form.get("prix")

    if not nom or not prix:

        return jsonify({
            "ok": False,
            "message": "Nom et prix obligatoires."
        }), 400

    try:

        prix = float(prix)

    except (ValueError, TypeError):

        return jsonify({
            "ok": False,
            "message": "Prix invalide."
        }), 400

    image_url = ""
    video_url = ""
    media_type = ""

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    image = request.files.get("image")

    if image and image.filename:

        try:

            resultat = cloudinary.uploader.upload(
                image,
                folder="yemalin-aura/produits",
                resource_type="image"
            )

            image_url = resultat.get(
                "secure_url",
                ""
            )

            media_type = "image"

        except Exception as e:

            return jsonify({
                "ok": False,
                "message": "Erreur Cloudinary image.",
                "error": str(e)
            }), 500

    # -----------------------------------------------------
    # VIDÉO
    # -----------------------------------------------------

    video = request.files.get("video")

    if video and video.filename:

        try:

            resultat = cloudinary.uploader.upload(
                video,
                folder="yemalin-aura/produits",
                resource_type="video"
            )

            video_url = resultat.get(
                "secure_url",
                ""
            )

            media_type = "video"

        except Exception as e:

            return jsonify({
                "ok": False,
                "message": "Erreur Cloudinary vidéo.",
                "error": str(e)
            }), 500

    # -----------------------------------------------------
    # ENREGISTREMENT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # NOTIFICATION NOUVEAU PRODUIT
    # -----------------------------------------------------

    envoyer_notification_tous(
        "Nouveau produit 🛍️",
        f"{nom} vient d'être ajouté sur Yemalin Aura."
    )

    return jsonify({
        "ok": True,
        "message": "Produit ajouté.",
        "id": produit_id
    })


# =========================================================
# SUPPRIMER PRODUIT
# =========================================================

@app.route(
    "/api/admin/produit/<int:produit_id>",
    methods=["DELETE"]
)
@admin_required
def supprimer_produit(produit_id):

    conn = db()

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

    if not client_nom or not telephone:

        return jsonify({
            "ok": False,
            "message": "Nom et téléphone obligatoires."
        }), 400

    if not panier:

        return jsonify({
            "ok": False,
            "message": "Votre panier est vide."
        }), 400

    try:

        total = sum(
            float(p.get("prix", 0))
            * int(p.get("quantite", 0))
            for p in panier
        )

    except Exception:

        return jsonify({
            "ok": False,
            "message": "Panier invalide."
        }), 400

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
    """, (token,)).fetchall()

    conn.close()

    return jsonify({
        "ok": True,
        "commandes": [dict(row) for row in rows]
    })


# =========================================================
# DÉTAIL D'UNE COMMANDE
# =========================================================

@app.route("/api/commande/<int:commande_id>")
def detail_commande(commande_id):

    token = session.get("client_token")

    conn = db()

    commande = conn.execute("""
        SELECT *
        FROM commandes
        WHERE id = ?
    """, (commande_id,)).fetchone()

    if not commande:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Commande introuvable."
        }), 404

    # Le client ne peut voir que sa propre commande.
    if not session.get("admin"):

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
    """, (commande_id,)).fetchall()

    messages = conn.execute("""
        SELECT
            id,
            commande_id,
            client_nom,
            auteur,
            message,
            date
        FROM messages
        WHERE commande_id = ?
        ORDER BY id ASC
    """, (commande_id,)).fetchall()

    conn.close()

    return jsonify({
        "ok": True,
        "commande": dict(commande),
        "produits": [
            dict(x) for x in produits
        ],
        "messages": [
            dict(x) for x in messages
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

    token = session.get("client_token")

    conn = db()

    commande = conn.execute("""
        SELECT *
        FROM commandes
        WHERE id = ?
    """, (commande_id,)).fetchone()

    if not commande:

        conn.close()

        return jsonify({
            "ok": False,
            "message": "Commande introuvable."
        }), 404

    # -----------------------------------------------------
    # SÉCURITÉ CLIENT
    # -----------------------------------------------------

    if not session.get("admin"):

        if commande["client_token"] != token:

            conn.close()

            return jsonify({
                "ok": False,
                "message": "Accès refusé."
            }), 403

    auteur = (
        "Admin"
        if session.get("admin")
        else "Client"
    )

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

    # -----------------------------------------------------
    # NOTIFICATION SI L'ADMIN RÉPOND
    # -----------------------------------------------------

    if session.get("admin"):

        envoyer_notification_client(
            commande["client_token"],
            "Nouvelle réponse 💬",
            "L'administrateur a répondu à votre commande."
        )

    return jsonify({
        "ok": True,
        "message": "Message envoyé."
    })


# =========================================================
# ADMIN — LISTE DES COMMANDES
# =========================================================

@app.route("/api/admin/commandes")
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
        dict(row)
        for row in rows
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
    """, (commande_id,)).fetchone()

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
    """, (commande_id,)).fetchall()

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
# ADMIN — CHANGER LE STATUT
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
        SELECT client_token
        FROM commandes
        WHERE id = ?
    """, (commande_id,)).fetchone()

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

    envoyer_notification_client(
        commande["client_token"],
        "Commande mise à jour 📦",
        f"Votre commande est maintenant : {statut}"
    )

    return jsonify({
        "ok": True,
        "message": "Statut mis à jour."
    })


# =========================================================
# ADMIN — DASHBOARD
# =========================================================

@app.route("/api/admin/dashboard")
@admin_required
def dashboard():

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

    messages = conn.execute("""
        SELECT COUNT(*)
        FROM messages
        WHERE auteur = 'Client'
    """).fetchone()[0]

    messages_generaux = conn.execute("""
        SELECT COUNT(*)
        FROM messages_generaux
    """).fetchone()[0]

    conn.close()

    return jsonify({
        "ok": True,
        "stats": {
            "commandes": commandes,
            "clients": clients,
            "revenus": revenus,
            "livraisons": livraisons,
            "nouvelles": nouvelles,
            "messages": messages,
            "messages_generaux": messages_generaux
        }
    })


# =========================================================
# MESSAGES GÉNÉRAUX — CLIENT
# =========================================================

@app.route(
    "/api/message-general",
    methods=["POST"]
)
def message_general():

    data = request.get_json(
        silent=True
    ) or {}

    nom = (
        data.get("nom")
        or ""
    ).strip()

    message = (
        data.get("message")
        or ""
    ).strip()

    if not nom or not message:

        return jsonify({
            "ok": False,
            "message": "Nom et message obligatoires."
        }), 400

    token = session.get("client_token")

    if not token:

        token = secrets.token_urlsafe(32)

        session["client_token"] = token

    conn = db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages_generaux
        (
            client_token,
            client_nom,
            message,
            reponse,
            date,
            date_reponse
        )
        VALUES (?, ?, ?, NULL, ?, NULL)
    """, (
        token,
        nom,
        message,
        maintenant()
    ))

    message_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message_id": message_id
    })


# =========================================================
# MESSAGES DU CLIENT
# =========================================================

@app.route("/api/mes-messages")
def mes_messages():

    token = session.get("client_token")

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
    """, (token,)).fetchall()

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

@app.route("/api/admin/messages")
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
# ADMIN — RÉPONDRE À UN MESSAGE
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
    """, (message_id,)).fetchone()

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

    # Notification au client
    envoyer_notification_client(
        message["client_token"],
        "Nouvelle réponse 💬",
        "L'administrateur a répondu à votre message."
    )

    return jsonify({
        "ok": True,
        "message": "Réponse envoyée."
        # =========================================================
# PUBLICITÉS
# =========================================================

@app.route("/api/publicites")
def publicites():

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM publicites
        WHERE position = 1
        LIMIT 1
    """).fetchall()

    conn.close()

    return jsonify([
        dict(x)
        for x in rows
    ])


# =========================================================
# ADMIN — MODIFIER LA PUBLICITÉ
# IMAGE OU VIDÉO
# =========================================================

@app.route(
    "/api/admin/publicite",
    methods=["POST"]
)
@admin_required
def modifier_publicite():

    position = request.form.get(
        "position",
        type=int
    )

    if position != 1:

        return jsonify({
            "ok": False,
            "message": "L'emplacement doit être 1."
        }), 400

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

    media_url = ""
    media_type = ""

    fichier = request.files.get("media")

    # -----------------------------------------------------
    # UPLOAD CLOUDINARY
    # -----------------------------------------------------

    if fichier and fichier.filename:

        nom = fichier.filename.lower()

        extensions_video = (
            ".mp4",
            ".webm",
            ".mov",
            ".m4v"
        )

        if nom.endswith(extensions_video):

            resource_type = "video"
            media_type = "video"

        else:

            resource_type = "image"
            media_type = "image"

        try:

            resultat = cloudinary.uploader.upload(
                fichier,
                folder="yemalin-aura/publicites",
                resource_type=resource_type
            )

            media_url = resultat.get(
                "secure_url",
                ""
            )

        except Exception as e:

            return jsonify({
                "ok": False,
                "message": "Erreur Cloudinary.",
                "error": str(e)
            }), 500

    # -----------------------------------------------------
    # CONSERVER L'ANCIEN MÉDIA
    # -----------------------------------------------------

    conn = db()

    ancien = conn.execute("""
        SELECT media_url, media_type
        FROM publicites
        WHERE position = 1
    """).fetchone()

    if not media_url and ancien:

        media_url = (
            ancien["media_url"]
            or ""
        )

        media_type = (
            ancien["media_type"]
            or ""
        )

    # -----------------------------------------------------
    # ENREGISTRER
    # -----------------------------------------------------

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
        1,
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
# ADMIN — SUPPRIMER LA PUBLICITÉ
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
# PUSH — ABONNER UN CLIENT
# =========================================================

@app.route(
    "/api/push/subscribe",
    methods=["POST"]
)
@app.route(
    "/api/push/abonner",
    methods=["POST"]
)
def push_abonner():

    data = request.get_json(
        silent=True
    ) or {}

    # Accepte aussi bien :
    # {endpoint, keys}
    # que :
    # {subscription: {endpoint, keys}}

    subscription = data.get(
        "subscription"
    )

    if isinstance(subscription, dict):

        data = subscription

    endpoint = (
        data.get("endpoint")
        or ""
    ).strip()

    keys = data.get("keys") or {}

    p256dh = (
        keys.get("p256dh")
        or ""
    ).strip()

    auth = (
        keys.get("auth")
        or ""
    ).strip()

    if not endpoint or not p256dh or not auth:

        return jsonify({
            "ok": False,
            "message": "Abonnement push invalide."
        }), 400

    token = session.get(
        "client_token"
    )

    # -----------------------------------------------------
    # Si le client n'a pas encore de token
    # -----------------------------------------------------

    if not token:

        token = secrets.token_urlsafe(32)

        session["client_token"] = token

    conn = db()

    conn.execute("""
        INSERT INTO push_subscriptions
        (
            client_token,
            endpoint,
            p256dh,
            auth,
            date
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(endpoint)
        DO UPDATE SET
            client_token = excluded.client_token,
            p256dh = excluded.p256dh,
            auth = excluded.auth,
            date = excluded.date
    """, (
        token,
        endpoint,
        p256dh,
        auth,
        maintenant()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": "Notifications activées."
    })


# =========================================================
# PUSH — DÉSABONNER
# =========================================================

@app.route(
    "/api/push/unsubscribe",
    methods=["POST"]
)
@app.route(
    "/api/push/desabonner",
    methods=["POST"]
)
def push_desabonner():

    data = request.get_json(
        silent=True
    ) or {}

    endpoint = (
        data.get("endpoint")
        or ""
    ).strip()

    if not endpoint:

        return jsonify({
            "ok": False,
            "message": "Endpoint manquant."
        }), 400

    conn = db()

    conn.execute("""
        DELETE FROM push_subscriptions
        WHERE endpoint = ?
    """, (
        endpoint,
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True
    })


# =========================================================
# FONCTION ENVOI PUSH
# =========================================================

def envoyer_push(
    subscription,
    titre,
    message
):

    if not VAPID_PUBLIC_KEY:

        print(
            "VAPID_PUBLIC_KEY absente."
        )

        return False

    if not VAPID_PRIVATE_KEY:

        print(
            "VAPID_PRIVATE_KEY absente."
        )

        return False

    try:

        from pywebpush import webpush

        abonnement = {
            "endpoint": subscription["endpoint"],
            "keys": {
                "p256dh": subscription["p256dh"],
                "auth": subscription["auth"]
            }
        }

        webpush(
            subscription_info=abonnement,
            data=(
                f'{{'
                f'"title": {titre!r}, '
                f'"body": {message!r}, '
                f'"url": "/"'
                f'}}'
            ),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": VAPID_EMAIL
            }
        )

        return True

    except Exception as e:

        print(
            "Erreur push :",
            e
        )

        return False


# =========================================================
# NOTIFICATION — CLIENT PARTICULIER
# =========================================================

def envoyer_notification_client(
    client_token,
    titre,
    message
):

    if not client_token:

        return

    conn = db()

    subscriptions = conn.execute("""
        SELECT *
        FROM push_subscriptions
        WHERE client_token = ?
    """, (
        client_token,
    )).fetchall()

    conn.close()

    for subscription in subscriptions:

        envoyer_push(
            subscription,
            titre,
            message
        )


# =========================================================
# NOTIFICATION — TOUS LES CLIENTS
# =========================================================

def envoyer_notification_tous(
    titre,
    message
):

    conn = db()

    subscriptions = conn.execute("""
        SELECT *
        FROM push_subscriptions
    """).fetchall()

    conn.close()

    for subscription in subscriptions:

        envoyer_push(
            subscription,
            titre,
            message
        )


# =========================================================
# SANTÉ DU SERVEUR
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "ok": True,
        "service": "Yemalin Aura",
        "status": "online"
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
    })
