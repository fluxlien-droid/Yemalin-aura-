from django.urls import path
from . import views
urlpatterns = [
    path("", views.home, name="home"),
    path("produits/", views.products, name="products"),
    path("produit/<int:pk>/", views.product_detail, name="product_detail"),
    path("produit/<int:pk>/commander/", views.order_product, name="order_product"),
    path("commande/<int:pk>/confirmation/", views.order_confirmation, name="order_confirmation"),
    path("mes-commandes/", views.my_orders, name="my_orders"),
    path("partenariat/", views.partnership, name="partnership"),
    path("messages/<int:conversation_id>/", views.conversation, name="conversation"),
]
