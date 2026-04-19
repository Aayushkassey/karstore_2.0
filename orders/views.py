from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from urllib3 import request
from .models import Order
from products.models import Product
from .models import Cart, CartItem
from django.http import JsonResponse
# CustomerActivity import garnu parchha (accounts app bata)
from accounts.models import CustomerActivity 
from django.contrib import messages

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'login_required'}, status=401)

    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    # --- ACTIVITY LOG START ---
    # Customer le add garda matra record basne
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='add_to_cart',
            product=product
        )
    # --- ACTIVITY LOG END ---

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'cart_count': cart.items.count()})
    
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'orders/cart_detail.html', {'cart': cart})

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # --- ACTIVITY LOG START ---
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role == 'SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='remove_from_cart',
            product=cart_item.product
        )
    # --- ACTIVITY LOG END ---
    
    cart_item.delete()
    return redirect('cart_detail')

def update_cart_qty(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Login required'}, status=401)

    action = request.GET.get('action')
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    if action == 'plus':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'minus':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            return JsonResponse({
                'status': 'success', 
                'new_qty': 0, 
                'cart_count': cart.items.count(),
                'total_price': cart.total_price # Property call
            })
    
    return JsonResponse({
        'status': 'success', 
        'new_qty': cart_item.quantity, 
        'cart_count': cart.items.count(),
        'total_price': cart.total_price, # Total price pathako
        'subtotal': cart_item.subtotal   # Individual item ko subtotal
    })

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).select_related('product').order_by('-created_at')

    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='view_orders'
        )

    return render(request, 'orders/orders.html', {'orders': orders})

@login_required
def update_order_status(request):
    if request.method == 'POST' and request.user.role == 'SELLER':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        
        # Ensure the order belongs to one of the seller's products
        order = get_object_or_404(Order, id=order_id, product__seller=request.user)
        order.status = new_status
        order.save()
        
        messages.success(request, f"Order #{order.id} status updated to {new_status}.")
        return redirect('dashboard') # Redirect back to dashboard
    
    return redirect('dashboard')

def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.delete()
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='delete_order',
            product_id=str(order.product.id)  # FK object ko id pathako
        )
    return redirect('orders')
def product_list(request):
    products = Product.objects.all().order_by('?') 
    context = {
        'products': products,
    }
    return render(request, 'pages/products.html', context)

def whistles_view(request):
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role == 'SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='view_whistles'
        )
    products = Product.objects.filter(is_whistle=True) 
    return render(request, 'pages/whistles.html', {'products': products})

def toggle_whistle(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'login_required'}, status=401)
    
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role == 'SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='toggle_whistle',
            product_id=product_id
        )

    product = get_object_or_404(Product, id=product_id)
    
    # Toggle logic
    product.is_whistle = not product.is_whistle
    product.save()

    return JsonResponse({
        'status': 'success', 
        'is_whistle': product.is_whistle  # Yo value frontend le use garchha red heart ko lagi
    })
