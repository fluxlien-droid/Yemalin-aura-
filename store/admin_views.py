from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

from django.db.models import Sum

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.utils import timezone

from .models import Product, Customer, Order


# =========================================================
# PROTECTION DES PAGES ADMIN
# =========================================================

staff_member_required = user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url="/admin/login/"
)


# =========================================================
# CONNEXION ADMIN
# =========================================================

def admin_login(request):

    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if user.is_staff:

                login(
                    request,
                    user
                )

                return redirect(
                    "admin_dashboard"
                )

            messages.error(
                request,
                "Ce compte n'a pas accès à l'administration."
            )

        else:

            messages.error(
                request,
                "Nom d'utilisateur ou mot de passe incorrect."
            )

    return render(
        request,
        "admin_login.html"
    )


# =========================================================
# DÉCONNEXION ADMIN
# =========================================================

def admin_logout(request):

    if request.method == "POST":

        logout(request)

        return redirect(
            "admin_login"
        )

    return redirect(
        "admin_dashboard"
    )


# =========================================================
# DASHBOARD
# =========================================================

@staff_member_required
def dashboard(request):

    orders = Order.objects.select_related(
        "customer",
        "product"
    ).order_by(
        "-created_at"
    )

    delivered = orders.filter(
        status="delivered"
    )

    revenue = delivered.aggregate(
        total=Sum("total")
    )["total"] or 0

    return render(
        request,
        "admin_dashboard.html",
        {
            "orders": orders[:30],

            "revenue": revenue,

            "counts": {
                "orders": orders.count(),
                "products": Product.objects.count(),
                "customers": Customer.objects.count(),
            }
        }
    )


# =========================================================
# STATUT COMMANDE
# =========================================================

@staff_member_required
def update_order_status(request, pk):

    order = get_object_or_404(
        Order,
        pk=pk
    )

    if request.method == "POST":

        status = request.POST.get(
            "status"
        )

        allowed_statuses = {
            "new",
            "confirmed",
            "delivery",
            "delivered",
            "cancelled",
        }

        if status in allowed_statuses:

            order.status = status

            if status == "delivered":

                if not order.delivered_at:
                    order.delivered_at = timezone.now()

            else:

                order.delivered_at = None

            order.save(
                update_fields=[
                    "status",
                    "delivered_at",
                ]
            )

    return redirect(
        "admin_dashboard"
    )


# =========================================================
# COMMANDES
# =========================================================

@staff_member_required
def dashboard_orders(request):

    orders = Order.objects.select_related(
        "customer",
        "product"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "dashboard_orders.html",
        {
            "orders": orders
        }
    )


# =========================================================
# MODIFIER UNE COMMANDE
# =========================================================

@staff_member_required
def edit_order(request, pk):

    order = get_object_or_404(
        Order,
        pk=pk
    )

    if request.method == "POST":

        quantity = request.POST.get(
            "quantity"
        )

        total = request.POST.get(
            "total"
        )

        extra_info = request.POST.get(
            "extra_info",
            ""
        ).strip()

        status = request.POST.get(
            "status"
        )

        if quantity:
            order.quantity = quantity

        if total:
            order.total = total

        order.extra_info = extra_info

        allowed_statuses = {
            "new",
            "confirmed",
            "delivery",
            "delivered",
            "cancelled",
        }

        if status in allowed_statuses:

            order.status = status

            if status == "delivered":

                if not order.delivered_at:
                    order.delivered_at = timezone.now()

            else:

                order.delivered_at = None

        order.save()

        return redirect(
            "dashboard_orders"
        )

    return render(
        request,
        "dashboard_order_edit.html",
        {
            "order": order
        }
    )


# =========================================================
# SUPPRIMER UNE COMMANDE
# =========================================================

@staff_member_required
def delete_order(request, pk):

    order = get_object_or_404(
        Order,
        pk=pk
    )

    if request.method == "POST":

        order.delete()

    return redirect(
        "dashboard_orders"
    )


# =========================================================
# PRODUITS
# =========================================================

@staff_member_required
def dashboard_products(request):

    products = Product.objects.order_by(
        "-created_at"
    )

    return render(
        request,
        "dashboard_products.html",
        {
            "products": products
        }
    )


# =========================================================
# AJOUTER UN PRODUIT
# =========================================================

@staff_member_required
def dashboard_product_add(request):

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        price = request.POST.get(
            "price",
            "0"
        )

        category = request.POST.get(
            "category",
            ""
        ).strip()

        stock = request.POST.get(
            "stock",
            "0"
        )

        external_link = request.POST.get(
            "external_link",
            ""
        ).strip()

        image = request.FILES.get(
            "image"
        )

        video = request.FILES.get(
            "video"
        )

        active = (
            request.POST.get("active") == "on"
        )

        if name:

            Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                stock=stock,
                external_link=external_link,
                image=image,
                video=video,
                active=active,
            )

            return redirect(
                "dashboard_products"
            )

    return render(
        request,
        "dashboard_product_add.html"
    )


# =========================================================
# MODIFIER UN PRODUIT
# =========================================================

@staff_member_required
def dashboard_product_edit(request, pk):

    product = get_object_or_404(
        Product,
        pk=pk
    )

    if request.method == "POST":

        product.name = request.POST.get(
            "name",
            ""
        ).strip()

        product.description = request.POST.get(
            "description",
            ""
        ).strip()

        product.price = request.POST.get(
            "price",
            "0"
        )

        product.category = request.POST.get(
            "category",
            ""
        ).strip()

        product.stock = request.POST.get(
            "stock",
            "0"
        )

        product.external_link = request.POST.get(
            "external_link",
            ""
        ).strip()

        product.active = (
            request.POST.get("active") == "on"
        )

        image = request.FILES.get(
            "image"
        )

        if image:
            product.image = image

        video = request.FILES.get(
            "video"
        )

        if video:
            product.video = video

        product.save()

        return redirect(
            "dashboard_products"
        )

    return render(
        request,
        "dashboard_product_edit.html",
        {
            "product": product
        }
    )


# =========================================================
# SUPPRIMER UN PRODUIT
# =========================================================

@staff_member_required
def delete_product(request, pk):

    product = get_object_or_404(
        Product,
        pk=pk
    )

    if request.method == "POST":

        product.delete()

    return redirect(
        "dashboard_products"
    )


# =========================================================
# CLIENTS
# =========================================================

@staff_member_required
def dashboard_customers(request):

    customers = Customer.objects.order_by(
        "-created_at"
    )

    return render(
        request,
        "dashboard_customers.html",
        {
            "customers": customers
        }
    )


# =========================================================
# CONTACTER UN CLIENT
# =========================================================

@staff_member_required
def contact_customer(request, pk):

    customer = get_object_or_404(
        Customer,
        pk=pk
    )

    return render(
        request,
        "contact_customer.html",
        {
            "customer": customer
        }
    )