from django import forms
from .models import Customer, Partnership, Message
class OrderForm(forms.ModelForm):
    class Meta:
        model=Customer
        fields=["name","phone","whatsapp","city","district","address"]
class MessageForm(forms.ModelForm):
    class Meta:
        model=Message
        fields=["body"]
class PartnershipForm(forms.ModelForm):
    class Meta:
        model=Partnership
        fields=["name","phone","email","project","partnership_type","message"]
