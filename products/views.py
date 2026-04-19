from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.db.models import Q
import requests

from payment.models import Payment
from orders.models import Order

from .models import Product, Category
from accounts.models import Interest, CustomerUser, CustomerActivity # Activity model import gareko

# 1. Main Home View (Search + Random Discovery)
def home(request):
    query = request.GET.get('q', '').strip()
    all_categories = Category.objects.all()
    
    # Highly Searched Section: Random 10 items discovery
    highly_searched = Product.objects.all().order_by('?')[:10] 

    if query:
        # SMART SEARCH logic
        words = query.split()
        search_filter = Q()
        for word in words:
            search_filter |= Q(name__icontains=word) | \
                            Q(description__icontains=word) | \
                            Q(category__name__icontains=word)
        
        product_list = Product.objects.filter(search_filter).distinct().order_by('-id')
        message = f"Search Results for '{query}'"
        
        # --- ACTIVITY LOG: Search ---
        if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
            CustomerActivity.objects.create(user=request.user, 
                action=f"Search: {query}", # Kun word search garyo tyo track hunchha
                product=None # Search ma product specific activity log gardaina, tesaile None pathaune
            )
            
    else:
        product_list = Product.objects.all().order_by('-id')
        message = "Featured Products"

    paginator = Paginator(product_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'components/product_list_ajax.html', {'page_obj': page_obj})

    return render(request, 'pages/home.html', {
        'page_obj': page_obj,
        'categories': all_categories,
        'highly_searched': highly_searched,
        'query': query,
        'message': message
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(user=request.user, action='view_product', product=product)

    return JsonResponse({'status': 'success', 'message': 'Activity logged'})

def log_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(user=request.user, action='view_product', product=product)
    return JsonResponse({'status': 'logged'})

# 3. Category wise products filter
def category_products(request, id):
    category = get_object_or_404(Category, id=id)
    all_categories = Category.objects.all() 

    product_list = Product.objects.filter(category=category).order_by('-id')
    
    # --- ACTIVITY LOG: View Category ---
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(user=request.user, action='view_category')

    paginator = Paginator(product_list, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'components/product_list_ajax.html', {'page_obj': page_obj})

    return render(request, 'pages/home.html', {
        'page_obj': page_obj,
        'categories': all_categories, 
        'message': f'Items in {category.name}',
        'selected_category': category
    })

# 4. Seller Dashboard
@login_required
def dashboard(request):
    if request.user.role != 'SELLER':
        return redirect('home')
    
    # --- ACTIVITY LOG: View Dashboard ---
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role == 'SELLER' and request.user.role == 'CUSTOMER': # In case customer somehow lands here
        CustomerActivity.objects.create(user=request.user, action='view_dashboard')

    products = Product.objects.filter(seller=request.user).order_by('-id')
    recent_orders = Order.objects.filter(product__seller=request.user).select_related('user', 'product').order_by('-created_at')
    
    context = {
        'products': products,
        'recent_orders': recent_orders,
        'total_products': products.count(),
        'total_sales': recent_orders.filter(status='Completed').count(),
    }
    
    return render(request, 'pages/dashboard.html', context)

@login_required
def update_payment_status(request, uuid):
    if request.user.role == 'SELLER':
        payment = get_object_or_404(Payment, uuid=uuid)
        if request.method == 'POST':
            new_status = request.POST.get('status')
            payment.status = new_status
            payment.save()
            
            CustomerActivity.objects.create(
                user=payment.user,
                action=f'order_{new_status.lower()}',
                transaction_id=str(payment.uuid)
            )
    return redirect('dashboard')

# 5. Seller le product add garne view
@login_required
def add_product(request):
    if request.user.role != 'SELLER':
        return redirect('home')

    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get("name")
        price = request.POST.get("price")
        description = request.POST.get("description")
        category_id = request.POST.get("category")
        image = request.FILES.get("image")

        try:
            category_obj = Category.objects.get(id=category_id)
            Product.objects.create(
                seller=request.user,
                name=name,
                price=price,
                description=description,
                category=category_obj,
                image=image
            )
            return redirect('dashboard')
        except Category.DoesNotExist:
            return render(request, 'pages/add_product.html', {
                'categories': categories, 
                'error': 'Invalid Category selected'
            })

    return render(request, 'pages/add_product.html', {'categories': categories})

# 6. Search Suggestions API
def search_suggestions(request):
    query = request.GET.get('term', '').strip()
    if query:
        words = query.split()
        search_filter = Q()
        for word in words:
            search_filter |= Q(name__icontains=word) | Q(category__name__icontains=word)

        products = Product.objects.filter(search_filter).distinct()[:6]
        results = [product.name for product in products]
        return JsonResponse(results, safe=False)
    
    return JsonResponse([], safe=False)

# 7. Dummy Data Seeding
def seed_dummy_json_inventory(request):
    base_url = "https://dummyjson.com/products"
    headers = {"User-Agent": "Mozilla/5.0"}
    seller = CustomerUser.objects.filter(is_superuser=True).first() or CustomerUser.objects.first()
    
    try:
        total_added = 0
        prod_response = requests.get(f"{base_url}?limit=200", headers=headers, timeout=15)
        products_data = prod_response.json().get('products', [])

        for item in products_data:
            cat_name = item.get('category', 'General').replace("-", " ").capitalize()
            category_obj, _ = Category.objects.get_or_create(name=cat_name)
            Interest.objects.get_or_create(name=cat_name)

            if not Product.objects.filter(name=item['title']).exists():
                p = Product(
                    name=item['title'],
                    price = round(item['price'] * 130, 2),
                    description=item.get('description', ''),
                    category=category_obj,
                    seller=seller,
                )
                img_url = item.get('thumbnail')
                if img_url:
                    try:
                        img_temp = requests.get(img_url, timeout=5).content
                        p.image.save(f"dummy_{item['id']}.jpg", ContentFile(img_temp), save=False)
                    except: pass
                p.save()
                total_added += 1
        return HttpResponse(f"<h1>Success!</h1><p>Added {total_added} products.</p>")
    except Exception as e:
        return HttpResponse(f"Error: {e}")