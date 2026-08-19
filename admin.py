from django.contrib import admin
from .models import Product, Customer, Order, Conversation, Message, Partnership
admin.site.site_header = "Yemanlin Aura — Admin"
admin.site.site_title = "Yemanlin Aura"
admin.site.index_title = "Dashboard Créateur"
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=("name","price","stock","active","updated_at")
    search_fields=("name","category")
    list_filter=("active","category")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=("id","customer","product","total","status","created_at","delivered_at")
    list_filter=("status",)
    search_fields=("customer__name","customer__phone","product__name")
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=("name","phone","city","district","created_at")
    search_fields=("name","phone","whatsapp")
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Partnership)
