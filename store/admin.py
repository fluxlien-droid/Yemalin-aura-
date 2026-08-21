from django.contrib import admin
from .models import Product, Customer, Order, Conversation, Message
admin.site.site_header='Yemanlin Aura'; admin.site.site_title='Yemanlin Aura'; admin.site.index_title='Espace Admin'
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=('name','price','stock','active'); search_fields=('name','category'); list_filter=('active',)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=('id','customer','product','total','status','created_at','delivered_at'); list_filter=('status',); search_fields=('customer__name','customer__phone','product__name')
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=('name','phone','whatsapp','city','district'); search_fields=('name','phone','whatsapp')
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin): list_display=('id','customer','created_at','updated_at')
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin): list_display=('conversation','sender','created_at','read'); list_filter=('sender','read')
