from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/images/", blank=True, null=True)
    video = models.FileField(upload_to="products/videos/", blank=True, null=True)
    external_link = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.name

class Customer(models.Model):
    name = models.CharField(max_length=180)
    phone = models.CharField(max_length=40)
    whatsapp = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=120)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Order(models.Model):
    STATUS = [
        ("new","Nouvelle"),("confirmed","Confirmée"),("delivery","En livraison"),
        ("delivered","Livraison faite"),("cancelled","Annulée")
    ]
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name="orders")
    product = models.ForeignKey(Product,on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=12,decimal_places=2)
    extra_info = models.TextField(blank=True)
    status = models.CharField(max_length=20,choices=STATUS,default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(blank=True,null=True)
    def mark_delivered(self):
        self.status="delivered"; self.delivered_at=timezone.now(); self.save(update_fields=["status","delivered_at"])

class Conversation(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation,on_delete=models.CASCADE,related_name="messages")
    sender = models.CharField(max_length=20,choices=[("client","Client"),("admin","Admin")])
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

class Partnership(models.Model):
    name = models.CharField(max_length=180)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    project = models.CharField(max_length=180,blank=True)
    partnership_type = models.CharField(max_length=180,blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
