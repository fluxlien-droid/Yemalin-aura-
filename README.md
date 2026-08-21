# Yemanlin Aura

Site e-commerce Django pour Yemanlin Aura.
Aucun produit, client, commande ou revenu fictif n'est préinstallé.

## Installation
```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Site public : http://127.0.0.1:8000/
Administration Django : http://127.0.0.1:8000/admin/

Le dossier `static/logo/` est prévu pour recevoir le logo fourni par le propriétaire.
Pour l'interface Admin personnalisée, une page dédiée sera ajoutée autour de l'administration Django.

## Sécurité
Le code Admin initial demandé dans le cahier des charges n'est pas exposé dans le JavaScript ou le HTML.
Utilisez un vrai compte administrateur avec un mot de passe sécurisé.

## Logo
Ajoute ton propre fichier `logo.png` directement dans `static/` :
`YemanlinAura/static/logo.png`

La page d'accueil utilise ce logo en arrière-plan flou et l'animation affiche d'abord
« Yemanlin Aura » lettre par lettre, puis « Le raffinement qui nous distingue » lettre par lettre.

## Contact pour finaliser une commande
Appel : 0193456835
WhatsApp : 94236550
Après une commande, ces boutons permettent au client de contacter directement Yemanlin Aura.

## Admin simplifié
L'Admin conserve uniquement : Produits, Commandes, Clients et Discussions.
