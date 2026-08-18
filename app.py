# =========================================================
# YEMALIN AURA
# app.py — PARTIE 1/2
# =========================================================

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


    # =====================================================
    # PRODUITS
    # =====================================================

    c.execute("""
        CREATE TABLE IF NOT EXISTS produits (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL,

            description TEXT,

            prix REAL NOT NULL,

            image TEXT,

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

            adresse TEXT,

            total REAL NOT NULL,

            statut TEXT DEFAULT 'Nouvelle',

            client_token TEXT UNIQUE NOT NULL,

            date TEXT NOT NULL

        )
    """)


    # =====================================================
    # PRODUITS COMMANDÉS
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
    # CHAT DES COMMANDES
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

            reponse TEXT,

            date TEXT NOT NULL,

            date_reponse TEXT

        )
    """)


    # =====================================================
    # PUBLICITÉ
    #
    # Une seule publicité sera utilisée.
    # position = 1
    # =====================================================

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

        VALUES
        (
            1,
            '',
            '',
            '',
            '',
            ''
        )
    """)


    # =====================================================
    # ABONNEMENTS PUSH
    # =====================================================

    c.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            client_token TEXT,

            endpoint TEXT UNIQUE NOT NULL,

            p256dh TEXT NOT NULL,

            auth TEXT NOT NULL,

            user_type TEXT DEFAULT 'client',

            date TEXT NOT NULL

        )
    """)


    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            client_token TEXT,

            commande_id INTEGER,

            titre TEXT NOT NULL,

            message TEXT NOT NULL,

            lu INTEGER DEFAULT 0,

            date TEXT NOT NULL

        )
    """)


    # =====================================================
    # PRODUITS DE DÉMONSTRATION
    # =====================================================

    nombre_produits = c.execute("""
        SELECT COUNT(*)
        FROM produits
    """).fetchone()[0]


    if nombre_produits == 0:

        c.execute("""
            INSERT INTO produits
            (
                nom,
                description,
                prix,
                image,
                date
            )

            VALUES (?, ?, ?, ?, ?)
        """, (

            "Produit exemple",

            "Découvrez notre produit.",

            5000,

            "",

            maintenant()

        ))


        c.execute("""
            INSERT INTO produits
            (
                nom,
                description,
                prix,
                image,
                date
            )

            VALUES (?, ?, ?, ?, ?)
        """, (

            "Deuxième produit",

            "Un autre produit Yemalin Aura.",

            7500,

            "",

            maintenant()

        ))


    conn.commit()

    conn.close()


# =========================================================
# ADMIN
# =========================================================

def admin_required(f):

    @wraps(f)

    def wrapper(*args, **kwargs):

        if not session.get("admin"):

            return jsonify({

                "ok": False,

                "message":
                    "Accès administrateur requis."

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

            "message":
                "Code administrateur incorrect."

        }), 401


    session.clear()

    session["admin"] = True


    return jsonify({

        "ok": True

    })


# =========================================================
# DÉCONNEXION ADMIN
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

    if not session.get("admin"):

        return redirect(
            url_for("admin_login")
        )


    return render_template(
        "admin.html"
    )


# =========================================================
# PAGE CLIENT
# =========================================================

@app.route("/")
def index():

    conn = db()


    produits = conn.execute("""
        SELECT *
        FROM produits
        ORDER BY id DESC
    """).fetchall()


    # Une seule publicité
    pub = conn.execute("""
        SELECT *
        FROM publicites
        WHERE position = 1
        LIMIT 1
    """).fetchone()


    conn.close()


    pubs = []


    if pub:

        pubs.append(pub)


    return render_template(

        "index.html",

        produits=produits,

        pubs=pubs

    )


# =========================================================
# API PRODUITS
# =========================================================

@app.route("/api/produits")
def produits():

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


    prix = request.form.get(
        "prix"
    )


    if not nom or not prix:

        return jsonify({

            "ok": False,

            "message":
                "Nom et prix obligatoires."

        }), 400


    try:

        prix = float(prix)

    except ValueError:

        return jsonify({

            "ok": False,

            "message":
                "Prix invalide."

        }), 400


    image_url = ""


    fichier = request.files.get(
        "image"
    )


    # =====================================================
    # CLOUDINARY IMAGE PRODUIT
    # =====================================================

    if fichier and fichier.filename:

        try:

            resultat = (
                cloudinary
                .uploader
                .upload(

                    fichier,

                    folder=
                        "yemalin-aura/produits",

                    resource_type=
                        "image"

                )
            )


            image_url = (
                resultat.get(
                    "secure_url",
                    ""
                )
            )


        except Exception:

            return jsonify({

                "ok": False,

                "message":
                    "Impossible d'envoyer l'image."

            }), 500


    conn = db()


    conn.execute("""
        INSERT INTO produits

        (
            nom,
            description,
            prix,
            image,
            date
        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        nom,

        description,

        prix,

        image_url,

        maintenant()

    ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True,

        "message":
            "Produit ajouté avec succès."

    })


# =========================================================
# ADMIN — SUPPRIMER PRODUIT
# =========================================================

@app.route(
    "/api/admin/produit/<int:produit_id>",
    methods=["DELETE"]
)
@admin_required
def supprimer_produit(
    produit_id
):

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

        "message":
            "Produit supprimé."

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


    panier = (
        data.get("panier")
        or []
    )


    if not client_nom or not telephone:

        return jsonify({

            "ok": False,

            "message":
                "Nom et téléphone obligatoires."

        }), 400


    if not panier:

        return jsonify({

            "ok": False,

            "message":
                "Votre panier est vide."

        }), 400


    # =====================================================
    # CALCUL DU TOTAL CÔTÉ SERVEUR
    # On ne fait pas confiance au prix envoyé par le navigateur.
    # =====================================================

    conn = db()


    total = 0

    produits_valides = []


    try:

        for produit in panier:

            produit_id = int(
                produit.get("id")
            )


            quantite = int(
                produit.get("quantite")
            )


            if quantite <= 0:

                raise ValueError()


            ligne = conn.execute("""
                SELECT id, nom, prix
                FROM produits
                WHERE id = ?
            """, (
                produit_id,
            )).fetchone()


            if not ligne:

                raise ValueError()


            prix = float(
                ligne["prix"]
            )


            total += (
                prix *
                quantite
            )


            produits_valides.append({

                "id":
                    ligne["id"],

                "nom":
                    ligne["nom"],

                "prix":
                    prix,

                "quantite":
                    quantite

            })


    except Exception:

        conn.close()


        return jsonify({

            "ok": False,

            "message":
                "Un produit du panier est invalide."

        }), 400


    # =====================================================
    # TOKEN PRIVÉ DU CLIENT
    # =====================================================

    client_token = secrets.token_urlsafe(
        32
    )


    c = conn.cursor()


    c.execute("""
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


    commande_id = c.lastrowid


    # =====================================================
    # PRODUITS DE LA COMMANDE
    # =====================================================

    for produit in produits_valides:

        c.execute("""
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

            produit["id"],

            produit["nom"],

            produit["prix"],

            produit["quantite"]

        ))


    # =====================================================
    # NOTIFICATION POUR L'ADMIN
    # =====================================================

    c.execute("""
        INSERT INTO notifications

        (
            client_token,
            commande_id,
            titre,
            message,
            date
        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        None,

        commande_id,

        "Nouvelle commande",

        f"Nouvelle commande #{commande_id} de {client_nom}.",

        maintenant()

    ))


    conn.commit()

    conn.close()


    # Le token reste uniquement dans la session
    session["client_token"] = client_token


    return jsonify({

        "ok": True,

        "commande_id":
            commande_id

    })


# =========================================================
# MES COMMANDES
# =========================================================

@app.route("/api/mes-commandes")
def mes_commandes():

    client_token = session.get(
        "client_token"
    )


    if not client_token:

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

        client_token,

    )).fetchall()


    conn.close()


    return jsonify({

        "ok": True,

        "commandes": [

            dict(row)

            for row in rows

        ]

    })


# =========================================================
# INITIALISATION
# =========================================================

with app.app_context():

    init_db()

# =========================================================
# YEMALIN AURA
# app.py — PARTIE 2/2
# =========================================================


# =========================================================
# DÉTAIL D'UNE COMMANDE
# =========================================================

@app.route(
    "/api/commande/<int:commande_id>"
)
def detail_commande(commande_id):

    client_token = session.get(
        "client_token"
    )


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

            "message":
                "Commande introuvable."

        }), 404


    # -----------------------------------------------------
    # Sécurité :
    # l'admin peut voir toutes les commandes,
    # le client uniquement sa propre commande.
    # -----------------------------------------------------

    if not session.get("admin"):

        if (
            not client_token
            or
            commande["client_token"]
            != client_token
        ):

            conn.close()

            return jsonify({

                "ok": False,

                "message":
                    "Accès refusé."

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
    """, (
        commande_id,
    )).fetchall()


    conn.close()


    return jsonify({

        "ok": True,

        "commande":
            dict(commande),

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

            "message":
                "Message vide."

        }), 400


    client_token = session.get(
        "client_token"
    )


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

            "message":
                "Commande introuvable."

        }), 404


    # -----------------------------------------------------
    # CLIENT :
    # il doit être propriétaire de la commande.
    # ADMIN :
    # il peut répondre à toutes les commandes.
    # -----------------------------------------------------

    if not session.get("admin"):

        if (
            not client_token
            or
            commande["client_token"]
            != client_token
        ):

            conn.close()

            return jsonify({

                "ok": False,

                "message":
                    "Accès refusé."

            }), 403


    auteur = (
        "Admin"
        if session.get("admin")
        else "Client"
    )


    maintenant_date = maintenant()


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

        maintenant_date

    ))


    # -----------------------------------------------------
    # NOTIFICATION
    # -----------------------------------------------------

    if session.get("admin"):

        titre = "Réponse de Yemalin Aura"

        texte = (
            f"Vous avez reçu une réponse "
            f"pour la commande #{commande_id}."
        )

    else:

        titre = "Nouveau message"

        texte = (
            f"{commande['client_nom']} "
            f"a envoyé un message pour "
            f"la commande #{commande_id}."
        )


    conn.execute("""
        INSERT INTO notifications

        (
            client_token,
            commande_id,
            titre,
            message,
            date
        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        commande["client_token"],

        commande_id,

        titre,

        texte,

        maintenant_date

    ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True

    })


# =========================================================
# ADMIN — TOUTES LES COMMANDES
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

        dict(row)

        for row in rows

    ])


# =========================================================
# ADMIN — DÉTAIL + CHAT
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

            "message":
                "Commande introuvable."

        }), 404


    messages = conn.execute("""
        SELECT *
        FROM messages
        WHERE commande_id = ?
        ORDER BY id ASC
    """, (
        commande_id,
    )).fetchall()


    produits = conn.execute("""
        SELECT *
        FROM commande_produits
        WHERE commande_id = ?
        ORDER BY id ASC
    """, (
        commande_id,
    )).fetchall()


    conn.close()


    return jsonify({

        "ok": True,

        "commande":
            dict(commande),

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

            "message":
                "Statut invalide."

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

            "message":
                "Commande introuvable."

        }), 404


    conn.execute("""
        UPDATE commandes

        SET statut = ?

        WHERE id = ?

    """, (

        statut,

        commande_id

    ))


    # -----------------------------------------------------
    # Notification pour le client
    # -----------------------------------------------------

    conn.execute("""
        INSERT INTO notifications

        (
            client_token,
            commande_id,
            titre,
            message,
            date
        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        commande["client_token"],

        commande_id,

        "Commande mise à jour",

        f"Votre commande #{commande_id} est maintenant : {statut}.",

        maintenant()

    ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True,

        "message":
            "Statut mis à jour."

    })


# =========================================================
# ADMIN — STATISTIQUES
# =========================================================

@app.route(
    "/api/admin/dashboard"
)
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
        SELECT COALESCE(
            SUM(total),
            0
        )
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


    produits = conn.execute("""
        SELECT COUNT(*)
        FROM produits
    """).fetchone()[0]


    conn.close()


    return jsonify({

        "ok": True,

        "stats": {

            "commandes":
                commandes,

            "clients":
                clients,

            "revenus":
                revenus,

            "livraisons":
                livraisons,

            "nouvelles":
                nouvelles,

            "messages":
                messages,

            "produits":
                produits

        }

    })


# =========================================================
# ADMIN — LISTE DES MESSAGES GÉNÉRAUX
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
# CLIENT — ENVOYER UN MESSAGE GÉNÉRAL
# =========================================================

@app.route(
    "/api/message",
    methods=["POST"]
)
def message_general():

    data = request.get_json(
        silent=True
    ) or {}


    nom = (
        data.get("client_nom")
        or ""
    ).strip()


    message = (
        data.get("message")
        or ""
    ).strip()


    if not nom or not message:

        return jsonify({

            "ok": False,

            "message":
                "Veuillez remplir les champs."

        }), 400


    client_token = session.get(
        "client_token"
    )


    if not client_token:

        client_token = secrets.token_urlsafe(
            32
        )

        session["client_token"] = (
            client_token
        )


    conn = db()


    conn.execute("""
        INSERT INTO messages_generaux

        (
            client_token,
            client_nom,
            message,
            date
        )

        VALUES (?, ?, ?, ?)

    """, (

        client_token,

        nom,

        message,

        maintenant()

    ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True,

        "message":
            "Message envoyé."

    })


# =========================================================
# ADMIN — RÉPONDRE À UN MESSAGE GÉNÉRAL
# =========================================================

@app.route(
    "/api/admin/message/<int:message_id>/repondre",
    methods=["POST"]
)
@admin_required
def repondre_message_general(
    message_id
):

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

            "message":
                "Réponse vide."

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

            "message":
                "Message introuvable."

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


    conn.execute("""
        INSERT INTO notifications

        (
            client_token,
            commande_id,
            titre,
            message,
            date
        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        message["client_token"],

        0,

        "Réponse de Yemalin Aura",

        reponse,

        maintenant()

    ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True,

        "message":
            "Réponse envoyée."

    })


# =========================================================
# PUBLICITÉ — CLIENT
# =========================================================

@app.route(
    "/api/publicites"
)
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
# PUBLICITÉ — ADMIN
# =========================================================

@app.route(
    "/api/admin/publicite",
    methods=["POST"]
)
@admin_required
def modifier_publicite():

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


    fichier = request.files.get(
        "media"
    )


    media_url = ""


    media_type = ""


    # -----------------------------------------------------
    # UPLOAD CLOUDINARY
    # -----------------------------------------------------

    if fichier and fichier.filename:

        nom = (
            fichier.filename
            .lower()
        )


        if nom.endswith((
            ".mp4",
            ".webm",
            ".mov",
            ".m4v"
        )):

            resource_type = "video"

            media_type = "video"

        else:

            resource_type = "image"

            media_type = "image"


        try:

            resultat = (
                cloudinary
                .uploader
                .upload(

                    fichier,

                    folder=
                        "yemalin-aura/publicites",

                    resource_type=
                        resource_type

                )
            )


            media_url = (
                resultat.get(
                    "secure_url",
                    ""
                )
            )


        except Exception:

            return jsonify({

                "ok": False,

                "message":
                    "Erreur Cloudinary."

            }), 500


    conn = db()


    # Si aucun nouveau média,
    # on garde l'ancien.
    if media_url:

        conn.execute("""
            UPDATE publicites

            SET
                titre = ?,
                media_url = ?,
                media_type = ?,
                lien = ?,
                texte = ?

            WHERE position = 1

        """, (

            titre,

            media_url,

            media_type,

            lien,

            texte

        ))

    else:

        conn.execute("""
            UPDATE publicites

            SET
                titre = ?,
                lien = ?,
                texte = ?

            WHERE position = 1

        """, (

            titre,

            lien,

            texte

        ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True,

        "message":
            "Publicité enregistrée."

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

        "message":
            "Publicité supprimée."

    })


# =========================================================
# NOTIFICATIONS — CLIENT
# =========================================================

@app.route(
    "/api/notifications"
)
def notifications():

    client_token = session.get(
        "client_token"
    )


    if not client_token:

        return jsonify({

            "ok": True,

            "notifications": []

        })


    conn = db()


    rows = conn.execute("""
        SELECT *

        FROM notifications

        WHERE client_token = ?

        ORDER BY id DESC

        LIMIT 50
    """, (

        client_token,

    )).fetchall()


    conn.close()


    return jsonify({

        "ok": True,

        "notifications": [

            dict(x)

            for x in rows

        ]

    })


# =========================================================
# NOTIFICATIONS — ADMIN
# =========================================================

@app.route(
    "/api/admin/notifications"
)
@admin_required
def admin_notifications():

    conn = db()


    rows = conn.execute("""
        SELECT *

        FROM notifications

        WHERE client_token IS NULL

        ORDER BY id DESC

        LIMIT 50
    """).fetchall()


    conn.close()


    return jsonify({

        "ok": True,

        "notifications": [

            dict(x)

            for x in rows

        ]

    })


# =========================================================
# MARQUER UNE NOTIFICATION COMME LUE
# =========================================================

@app.route(
    "/api/notifications/<int:notification_id>/lu",
    methods=["POST"]
)
def notification_lue(
    notification_id
):

    client_token = session.get(
        "client_token"
    )


    if not client_token:

        return jsonify({

            "ok": False

        }), 401


    conn = db()


    conn.execute("""
        UPDATE notifications

        SET lu = 1

        WHERE id = ?

        AND client_token = ?
    """, (

        notification_id,

        client_token

    ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True

    })

# =========================================================
# PUSH — ENREGISTRER L'ABONNEMENT
# =========================================================

@app.route(
    "/api/push/subscribe",
    methods=["POST"]
)
def push_subscribe():

    data = request.get_json(
        silent=True
    ) or {}


    subscription = (
        data.get("subscription")
        or {}
    )


    endpoint = (
        subscription.get("endpoint")
        or ""
    ).strip()


    keys = (
        subscription.get("keys")
        or {}
    )


    p256dh = (
        keys.get("p256dh")
        or ""
    ).strip()


    auth = (
        keys.get("auth")
        or ""
    ).strip()


    if (
        not endpoint
        or not p256dh
        or not auth
    ):

        return jsonify({

            "ok": False,

            "message":
                "Abonnement push invalide."

        }), 400


    client_token = session.get(
        "client_token"
    )


    user_type = (
        "admin"
        if session.get("admin")
        else "client"
    )


    conn = db()


    conn.execute("""
        INSERT OR REPLACE INTO
        push_subscriptions

        (
            client_token,
            endpoint,
            p256dh,
            auth,
            user_type,
            date
        )

        VALUES (?, ?, ?, ?, ?, ?)

    """, (

        client_token,

        endpoint,

        p256dh,

        auth,

        user_type,

        maintenant()

    ))


    conn.commit()

    conn.close()


    return jsonify({

        "ok": True,

        "message":
            "Notifications activées."

    })


# =========================================================
# ROUTE DE TEST
# =========================================================

@app.route(
    "/api/test"
)
def test():

    return jsonify({

        "ok": True,

        "site":
            "Yemalin Aura",

        "slogan":
            "Le raffinement qui nous distingue"

    })


# =========================================================
# FIN
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=False

    ) 