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
from orders.models import Whistle

@login_required
def add_to_cart(request, product_id):
    if request.user.role != 'CUSTOMER':
        return JsonResponse({
            'status': 'error', 
            'message': 'Only customers can add items to cart.'
        }, status=403)


    if not request.user.is_authenticated:
        return JsonResponse({'status': 'login_required'}, status=401)

    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    # ✅ नयाँ लजिक: फ्रन्टइन्डबाट आएको quantity तान्ने, नआए १ मान्ने
    qty_from_post = int(request.POST.get('quantity', 1))

    if not item_created:
        # पहिले नै कार्टमा छ भने आएको परिमाण थप्ने
        cart_item.quantity += qty_from_post
    else:
        # नयाँ आइटम हो भने सिधै आएको परिमाण राख्ने
        cart_item.quantity = qty_from_post
    
    cart_item.save()

    # --- ACTIVITY LOG ---
    if request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='add_to_cart',
            product=product,
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # cart.items.count() ले आइटमको सङ्ख्या दिन्छ (जस्तै: २ थरी सामान)
        # यदि तिमीलाई जम्मा सामान (Quantity) को टोटल चाहिएको हो भने अर्कै लजिक चाहिन्छ
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
            product=cart_item.product,
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

    # एक्टिभिटी लगको लागि एक्सन नाम राख्ने रिएबल
    activity_action = None

    if action == 'plus':
        cart_item.quantity += 1
        cart_item.save()
        activity_action = 'add_to_cart'
    
    elif action == 'minus':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            activity_action = 'reduce_cart_qty' 
        else:
            cart_item.delete()
            activity_action = 'remove_from_cart'
        
            if request.user.role == 'CUSTOMER':
                CustomerActivity.objects.create(
                    user=request.user,
                    action=activity_action,
                    product=product
                )
            
            return JsonResponse({
                'status': 'success', 
                'new_qty': 0, 
                'cart_count': cart.items.count(),
                'total_price': cart.total_price
            })

    if activity_action and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action=activity_action,
            product=product,
            extra_info=f"New quantity: {cart_item.quantity}" if action != 'minus' or cart_item.id else "Item removed"
        )
    
    return JsonResponse({
        'status': 'success', 
        'new_qty': cart_item.quantity, 
        'cart_count': cart.items.count(),
        'total_price': cart.total_price,
        'subtotal': cart_item.subtotal
    })

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).select_related('product').order_by('-created_at')

    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='view_orders',
            extra_info=f"Total Orders: {orders.count()}"
        )

    return render(request, 'orders/orders.html', {'orders': orders})

@login_required
def update_order_status(request):
    if request.method == 'POST' and request.user.role == 'SELLER':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        
        order = get_object_or_404(Order, id=order_id, product__seller=request.user)
        
        # पुराना स्थिति के थियो भनेर चेक गर्ने (यदि पछि स्टक मिलाउनु पर्यो भने)
        old_status = order.status
        
        order.status = new_status
        order.save()

        # ✅ यदि सेलरले अर्डर क्यान्सिल गर्यो भने स्टक फिर्ता गरिदिने
        if new_status == 'Cancelled' and old_status != 'Cancelled':
            product = order.product
            product.stock += order.quantity # सामान स्टकमा फिर्ता भयो
            product.save()
            messages.warning(request, f"Order #{order.id} cancelled and stock updated.")
        else:
            messages.success(request, f"Order #{order.id} status updated to {new_status}.")
            
        return redirect('dashboard')
    
    return redirect('dashboard')

def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.delete()
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='delete_order',
            product_id=str(order.product.id), 
        )
    return redirect('orders')

def product_list(request):
    products = Product.objects.all().order_by('?') 
    context = {
        'products': products,
    }
    return render(request, 'pages/products.html', context)


def whistles_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Activity Log: विस्लिस्ट पेज हेरेको रेकर्ड
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role == 'SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action='view_whistles'
        )
    
    
    whistled_products = Product.objects.filter(whistle__user=request.user).order_by('-whistle__created_at')
    
    return render(request, 'pages/whistles.html', {'products': whistled_products})


# २. मुटु थिच्दा (Add/Remove) हुने View
@login_required
def toggle_whistle(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'login_required'}, status=401)
    
    product = get_object_or_404(Product, id=product_id)
    
    # ✅ Private Logic: Whistle टेबलमा यो युजर र प्रोडक्ट छ कि छैन चेक गर्ने
    whistle_qs = Whistle.objects.filter(user=request.user, product=product)
    
    if whistle_qs.exists():
        # पहिले नै मन पराएको रहेछ भने हटाउने
        whistle_qs.delete()
        is_whistle = False
        current_action = 'remove_whistle'
    else:
        # मन पराएको छैन भने नयाँ रेकर्ड थप्ने
        Whistle.objects.create(user=request.user, product=product)
        is_whistle = True
        current_action = 'add_whistle'

    # Customer Activity Log
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role == 'SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user,
            action=current_action,
            product_id=product_id
        )

    return JsonResponse({
        'status': 'success', 
        'is_whistle': is_whistle  # यो भ्यालुले फ्रन्टइन्डमा मुटुको रङ फेर्छ
    })