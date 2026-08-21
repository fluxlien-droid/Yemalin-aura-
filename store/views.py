from django.shortcuts import render,get_object_or_404,redirect
from django.contrib import messages
from django.db.models import Sum
from .models import Product,Customer,Order,Conversation
from .forms import OrderForm,PartnershipForm,MessageForm

def home(request):
    return render(request,"home.html",{"products":Product.objects.filter(active=True)[:8]})

def products(request):
    q=request.GET.get("q","").strip()
    qs=Product.objects.filter(active=True)
    if q: qs=qs.filter(name__icontains=q)
    return render(request,"products.html",{"products":qs,"q":q})

def product_detail(request,pk):
    return render(request,"product_detail.html",{"product":get_object_or_404(Product,pk=pk,active=True)})

def order_product(request,pk):
    product=get_object_or_404(Product,pk=pk,active=True)
    if request.method=="POST":
        form=OrderForm(request.POST)
        if form.is_valid():
            customer=form.save()
            order=Order.objects.create(customer=customer,product=product,quantity=1,total=product.price,extra_info=request.POST.get("extra_info",""))
            ids=request.session.get("order_ids",[])
            if order.id not in ids: ids.append(order.id)
            request.session["order_ids"]=ids
            return redirect("order_confirmation",pk=order.pk)
    else: form=OrderForm()
    return render(request,"order.html",{"form":form,"product":product})

def my_orders(request):
    ids=request.session.get("order_ids",[])
    orders=Order.objects.filter(id__in=ids).select_related("product","customer").order_by("-created_at")
    return render(request,"my_orders.html",{"orders":orders})

def order_confirmation(request,pk):
    order=get_object_or_404(Order,pk=pk)
    return render(request,"confirmation.html",{"order":order})

def partnership(request):
    if request.method=="POST":
        form=PartnershipForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request,"Votre demande de partenariat a été envoyée.")
            return redirect("partnership")
    else: form=PartnershipForm()
    return render(request,"partnership.html",{"form":form})

def conversation(request,conversation_id):
    conv=get_object_or_404(Conversation,pk=conversation_id)
    if request.method=="POST":
        form=MessageForm(request.POST)
        if form.is_valid():
            m=form.save(commit=False); m.conversation=conv; m.sender="client"; m.save()
            return redirect("conversation",conversation_id=conv.id)
    else: form=MessageForm()
    return render(request,"conversation.html",{"conversation":conv,"form":form})
