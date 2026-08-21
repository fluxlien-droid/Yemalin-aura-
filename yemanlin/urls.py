from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from store.admin_views import (
    admin_login,
    admin_logout,

    dashboard,
    update_order_status,

    dashboard_orders,
    delete_order,

    dashboard_products,
    dashboard_product_add,
    dashboard_product_edit,
    delete_product,

    dashboard_customers,
    contact_customer,
)


urlpatterns = [

    # =====================================================
    # SITE VISITEUR
    # =====================================================

    path(
        "",
        include("store.urls")
    ),


    # =====================================================
    # ADMIN - CONNEXION
    # =====================================================

    path(
        "admin/login/",
        admin_login,
        name="admin_login"
    ),

    path(
        "admin/logout/",
        admin_logout,
        name="admin_logout"
    ),


    # =====================================================
    # ADMIN - TABLEAU DE BORD
    # =====================================================

    path(
        "admin/dashboard/",
        dashboard,
        name="admin_dashboard"
    ),


    # =====================================================
    # ADMIN - COMMANDES
    # =====================================================

    path(
        "admin/dashboard/commandes/",
        dashboard_orders,
        name="dashboard_orders"
    ),

    path(
        "admin/dashboard/commande/<int:pk>/statut/",
        update_order_status,
        name="update_order_status"
    ),

    path(
        "admin/dashboard/commande/<int:pk>/supprimer/",
        delete_order,
        name="delete_order"
    ),


    # =====================================================
    # ADMIN - PRODUITS
    # =====================================================

    path(
        "admin/dashboard/produits/",
        dashboard_products,
        name="dashboard_products"
    ),

    path(
        "admin/dashboard/produit/ajouter/",
        dashboard_product_add,
        name="dashboard_product_add"
    ),

    path(
        "admin/dashboard/produit/<int:pk>/modifier/",
        dashboard_product_edit,
        name="dashboard_product_edit"
    ),

    path(
        "admin/dashboard/produit/<int:pk>/supprimer/",
        delete_product,
        name="delete_product"
    ),


    # =====================================================
    # ADMIN - CLIENTS
    # =====================================================

    path(
        "admin/dashboard/clients/",
        dashboard_customers,
        name="dashboard_customers"
    ),

    path(
        "admin/dashboard/client/<int:pk>/contacter/",
        contact_customer,
        name="contact_customer"
    ),
]


# =========================================================
# MEDIA EN DÉVELOPPEMENT
# =========================================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )