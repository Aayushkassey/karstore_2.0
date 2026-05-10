from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.db.models import Q
import requests
from django.contrib import messages
from payment.models import Payment
from orders.models import Order

from .models import Product, Category

from django.db.models import Exists, OuterRef, Value, BooleanField, Count

from orders.models import Whistle
# from accounts.ml_utils import get_recommendations

from accounts.models import Interest, CustomerUser, CustomerActivity # Activity model import gareko

from ml_services.services.recsys import get_popular_products
from ml_services.services.recsys import get_recommendations, get_popular_products
from retention.models import UserRecommendation, PopularProducts

from django.core.cache import cache

# 1. Main Home View (Search + Random Discovery)
# def home(request):
#     # 1. Basic redirections
#     if request.user.is_authenticated and not (request.user.is_superuser or request.user.is_staff or request.user.role == 'SELLER'):
#         if request.user.role == 'CUSTOMER' and not request.user.has_set_interests:
#             return redirect('select_interest')

#     query = request.GET.get('q', '').strip()
#     # all_categories = Category.objects.all()

#     # highly_searched = Product.objects.annotate(
#     #     num_sales=Count('order')
#     # ).order_by('-num_sales')[:10]

#     # # यदि अर्डर नै छैन भने (नयाँ साइटमा)
#     # if not highly_searched.exists() or highly_searched[0].num_sales == 0:
#     #     highly_searched = Product.objects.all().order_by('?')[:10]

#     try:
#         pop_cache = PopularProducts.objects.first()
#         popular_ids = pop_cache.product_ids[:10] if pop_cache else []
#     except Exception:
#         popular_ids = []

#     if popular_ids:
#         if request.user.is_authenticated and request.user.role == 'CUSTOMER':
#             user_whistles_ref = Whistle.objects.filter(
#                 user=request.user, product=OuterRef('pk')
#             )
#             highly_searched = Product.objects.filter(
#                 id__in=popular_ids, stock__gt=0
#             ).annotate(is_whistle=Exists(user_whistles_ref))
#         else:
#             highly_searched = Product.objects.filter(
#                 id__in=popular_ids, stock__gt=0
#             ).annotate(is_whistle=Value(False, output_field=BooleanField()))

#         id_order = {pid: idx for idx, pid in enumerate(popular_ids)}
#         highly_searched = sorted(highly_searched, key=lambda p: id_order.get(p.id, 99))
#     else:
#         # fallback to DB order count
#         highly_searched = Product.objects.annotate(
#             num_sales=Count('order')
#         ).order_by('-num_sales')[:10]

    
    
#     # २. Popular Discovery / Recommended 
#     recommended_products = None
#     if not query and request.user.is_authenticated and request.user.role == 'CUSTOMER':
#         user_whistles_ref = Whistle.objects.filter(
#             user=request.user, product=OuterRef('pk')
#         )

#         try:
#             user_rec = UserRecommendation.objects.get(user=request.user)
#             product_ids = user_rec.product_ids[:10] #8
#             is_cold = user_rec.is_cold_start

#             if product_ids and not is_cold:
#                 # Personalized from DB cache
#                 recommended_products = Product.objects.filter(
#                     id__in=product_ids, stock__gt=0
#                 ).annotate(is_whistle=Exists(user_whistles_ref))
#                 id_order = {pid: idx for idx, pid in enumerate(product_ids)}
#                 recommended_products = sorted(
#                     recommended_products,
#                     key=lambda p: id_order.get(p.id, 99)
#                 )
#             else:
#                 raise ValueError("cold start")

#         except (UserRecommendation.DoesNotExist, ValueError):
#             # No cache yet — fallback to interest filter
#             if request.user.interests.exists():
#                 interest_names = list(
#                     request.user.interests.values_list('name', flat=True)
#                 )
#                 # Try popular cache filtered by interests
#                 pop_cache = PopularProducts.objects.first()
#                 pop_ids = pop_cache.product_ids if pop_cache else []

#                 if pop_ids:
#                     recommended_products = Product.objects.filter(
#                         id__in=pop_ids,
#                         category__name__in=interest_names,
#                         stock__gt=0
#                     ).annotate(
#                         is_whistle=Exists(user_whistles_ref)
#                     ).distinct()[:10] #8

#                 if not recommended_products:
#                     # Final fallback — direct DB interest filter
#                     recommended_products = Product.objects.filter(
#                         category__name__in=interest_names,
#                         stock__gt=0
#                     ).annotate(
#                         is_whistle=Exists(user_whistles_ref)
#                     ).distinct().order_by('-id')[:10] #8 #10    

#     # 3. Main Product List (Search or Featured)
#     if query:
#         words = query.split()
#         search_filter = Q()
#         for word in words:
#             search_filter |= Q(name__icontains=word) | Q(description__icontains=word) | Q(category__name__icontains=word)
        
#         base_query = Product.objects.filter(search_filter).distinct().order_by('-id')
#         message = f"Search Results for '{query}'"
        
#         # Log Activity
#         if request.user.is_authenticated and request.user.role == 'CUSTOMER':
#             CustomerActivity.objects.create(user=request.user, action="search", extra_info=f"Searched for: {query}")
#     else:
#         # Normal Featured Products
#         base_query = Product.objects.all().order_by('-id')
#         message = "Featured Products"

#     # --- 4. Private Wishlist Annotation (The Secret Sauce) ---
#     # यसले गर्दा मात्र Customer A को मुटु Customer B कोमा रातो देखिँदैन
#     if request.user.is_authenticated and request.user.role == 'CUSTOMER':
#         user_whistles = Whistle.objects.filter(
#             user=request.user, 
#             product=OuterRef('pk')
#         )
#         product_list = base_query.annotate(
#             is_whistle=Exists(user_whistles)
#         ).order_by('-id')
#     else:
#         # गेस्ट वा सेलरका लागि सबै मुटु सेतो (False) बनाउने
#         product_list = base_query.annotate(
#             is_whistle=Value(False, output_field=BooleanField())
#         ).order_by('-id')

#     # 4. Pagination
#     paginator = Paginator(product_list, 15)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         return render(request, 'components/product_list_ajax.html', {'page_obj': page_obj})

#     return render(request, 'pages/home.html', {
#         'page_obj': page_obj,
#         'recommended_products': recommended_products,
#         'highly_searched': highly_searched,
#         # 'categories': all_categories,
#         'query': query,
#         'message': message
#     })


def home(request):
    if request.user.is_authenticated and not (request.user.is_superuser or request.user.is_staff or request.user.role == 'SELLER'):
        if request.user.role == 'CUSTOMER' and not request.user.has_set_interests:
            return redirect('select_interest')

    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page')

    # --- Whistle IDs (1 query) ---
    whistle_ids = set()
    if request.user.is_authenticated and request.user.role == 'CUSTOMER':
        whistle_ids = set(Whistle.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True))

    # --- Highly Searched ---
    highly_searched = cache.get('highly_searched_products')
    if not highly_searched:
        try:
            pop_cache = PopularProducts.objects.first()
            popular_ids = pop_cache.product_ids[:10] if pop_cache else []
        except Exception:
            popular_ids = []

        if popular_ids:
            highly_searched = list(Product.objects.filter(
                id__in=popular_ids, stock__gt=0
            ).annotate(is_whistle=Value(False, output_field=BooleanField())))
            id_order = {pid: idx for idx, pid in enumerate(popular_ids)}
            highly_searched = sorted(highly_searched, key=lambda p: id_order.get(p.id, 99))
        else:
            highly_searched = list(Product.objects.annotate(
                num_sales=Count('order')
            ).order_by('-num_sales')[:10].annotate(
                is_whistle=Value(False, output_field=BooleanField())
            ))

        cache.set('highly_searched_products', highly_searched, 60 * 10)

    for p in highly_searched:
        p.is_whistle = p.id in whistle_ids

    # --- Recommended Products ---
    recommended_products = None
    if not query and request.user.is_authenticated and request.user.role == 'CUSTOMER':
        rec_cache_key = f'rec_{request.user.id}'
        recommended_products = cache.get(rec_cache_key)

        if not recommended_products:
            try:
                user_rec = UserRecommendation.objects.get(user=request.user)
                product_ids = user_rec.product_ids[:10]
                is_cold = user_rec.is_cold_start

                if product_ids and not is_cold:
                    recommended_products = list(Product.objects.filter(
                        id__in=product_ids, stock__gt=0
                    ).annotate(is_whistle=Value(False, output_field=BooleanField())))
                    id_order = {pid: idx for idx, pid in enumerate(product_ids)}
                    recommended_products = sorted(
                        recommended_products,
                        key=lambda p: id_order.get(p.id, 99)
                    )
                else:
                    raise ValueError("cold start")

            except (UserRecommendation.DoesNotExist, ValueError):
                if request.user.interests.exists():
                    interest_names = list(
                        request.user.interests.values_list('name', flat=True)
                    )
                    try:
                        pop_obj = PopularProducts.objects.first()
                        pop_ids = pop_obj.product_ids if pop_obj else []
                    except Exception:
                        pop_ids = []

                    if pop_ids:
                        recommended_products = list(Product.objects.filter(
                            id__in=pop_ids,
                            category__name__in=interest_names,
                            stock__gt=0
                        ).annotate(
                            is_whistle=Value(False, output_field=BooleanField())
                        ).distinct()[:10])

                    if not recommended_products:
                        recommended_products = list(Product.objects.filter(
                            category__name__in=interest_names,
                            stock__gt=0
                        ).annotate(
                            is_whistle=Value(False, output_field=BooleanField())
                        ).distinct().order_by('-id')[:10])

            if recommended_products:
                cache.set(rec_cache_key, recommended_products, 60 * 10)

        if recommended_products:
            for p in recommended_products:
                p.is_whistle = p.id in whistle_ids

    # --- Main Product List ---
    if query:
        words = query.split()
        search_filter = Q()
        for word in words:
            search_filter |= Q(name__icontains=word) | Q(description__icontains=word) | Q(category__name__icontains=word)
        base_query = Product.objects.filter(search_filter).distinct().order_by('-id')
        message = f"Search Results for '{query}'"
        if request.user.is_authenticated and request.user.role == 'CUSTOMER':
            CustomerActivity.objects.create(user=request.user, action="search", extra_info=f"Searched for: {query}")
    else:
        base_query = Product.objects.all().order_by('-id')
        message = "Featured Products"

    if request.user.is_authenticated and request.user.role == 'CUSTOMER':
        user_whistles = Whistle.objects.filter(user=request.user, product=OuterRef('pk'))
        product_list = base_query.annotate(is_whistle=Exists(user_whistles)).order_by('-id')
    else:
        product_list = base_query.annotate(
            is_whistle=Value(False, output_field=BooleanField())
        ).order_by('-id')

    paginator = Paginator(product_list, 15)

    # Guest + no search + page 1 = cache
    if not query and not request.user.is_authenticated and not page_number:
        page_obj = cache.get('home_page1_guest')
        if not page_obj:
            page_obj = paginator.get_page(1)
            cache.set('home_page1_guest', page_obj, 60 * 5)
    else:
        page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'components/product_list_ajax.html', {'page_obj': page_obj})

    return render(request, 'pages/home.html', {
        'page_obj': page_obj,
        'recommended_products': recommended_products,
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
    # all_categories = Category.objects.all() 

    base_query = Product.objects.filter(category=category)


    if request.user.is_authenticated and request.user.role == 'CUSTOMER':
        user_whistles = Whistle.objects.filter(user=request.user, product=OuterRef('pk'))
        product_list = base_query.annotate(is_whistle=Exists(user_whistles)).order_by('-id')
    else:
        product_list = base_query.annotate(is_whistle=Value(False, output_field=BooleanField())).order_by('-id')
    
    # --- ACTIVITY LOG: View Category ---
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(user=request.user, action='view_category', extra_info=f"Category: {category.name}")

    paginator = Paginator(product_list, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':

        return render(request, 'components/product_list_ajax.html', {'page_obj': page_obj})

    return render(request, 'pages/home.html', {
        'page_obj': page_obj,
        # 'categories': all_categories, 
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
        new_category_name = request.POST.get("new_category_name")
        image = request.FILES.get("image")
        if image and image.size > 1 * 1024 * 1024: # 1MB भन्दा ठुलो भएमा
            messages.error(request, "Image size must be less than 1MB!")
            return render(request, 'pages/add_product.html', {'categories': categories})
        brand = request.POST.get("brand")
        stock = request.POST.get("stock")
        sku = request.POST.get("sku")
        
        # ✅ 'discountage_price' लाई फेरेर 'discount_percentage' राखियो
        # जुन तिम्रो HTML को input field को 'name' सँग मिल्नुपर्छ
        discount_val = request.POST.get("discount_percentage") 
        
        discount_perc = float(discount_val) if discount_val and discount_val.strip() != "" else 0.0

        try:
        
            if category_id == 'new_category' and new_category_name:
        
                category_obj, created = Category.objects.get_or_create(name=new_category_name)

                from accounts.models import Interest
                Interest.objects.get_or_create(name=new_category_name)
            else:
                
                category_obj = Category.objects.get(id=category_id)
            Product.objects.create(
                seller=request.user,
                name=name,
                price=float(price) if price else 0.0,
                discount_percentage=discount_perc, 
                brand=brand,
                stock=int(stock) if stock else 0,
                description=description,
                category=category_obj,
                image=image,
                sku=sku
            )
            messages.success(request, "Product added successfully!")
            return redirect('dashboard')
        except (Category.DoesNotExist, ValueError):
            messages.error(request, "Data is invalid. Please check your inputs.")
            return render(request, 'pages/add_product.html', {'categories': categories})

    return render(request, 'pages/add_product.html', {'categories': categories})


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id, seller=request.user)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get("name")
        product.brand = request.POST.get("brand")
        product.description = request.POST.get("description")
        product.sku = request.POST.get("sku") 
        product.price = float(request.POST.get("price") or 0)
        product.stock = int(request.POST.get("stock") or 0)
        
        discount_val = request.POST.get("discount_percentage")
        product.discount_percentage = float(discount_val) if discount_val else 0
        
        category_id = request.POST.get("category")
        new_category_name = request.POST.get("new_category_name")

        if category_id == 'new_category' and new_category_name:
            # नयाँ क्याटेगोरी बनाएर असाइन गर्ने
            category_obj, created = Category.objects.get_or_create(name=new_category_name)

            from accounts.models import Interest
            Interest.objects.get_or_create(name=new_category_name)

            product.category = category_obj
        elif category_id:
            # पुरानै क्याटेगोरी आईडीबाट तान्ने
            product.category = get_object_or_404(Category, id=category_id)
        
        if request.FILES.get("image"):
            product.image = request.FILES.get("image")
            
        product.save()
        messages.success(request, f"Product '{product.name}' updated successfully!")
        return redirect('dashboard')

    return render(request, 'pages/edit_product.html', {'product': product, 'categories': categories})


@login_required
def delete_product(request, product_id):
    # सुरक्षाको लागि आफ्नो प्रोडक्ट हो कि हैन चेक गर्ने
    product = get_object_or_404(Product, pk=product_id, seller=request.user)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.warning(request, f"Product '{product_name}' deleted successfully.")
        return redirect('dashboard')
        
    return render(request, 'pages/confirm_delete.html', {'product': product})

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
    
    # १. डिफल्ट सेलर छान्ने (Superuser वा पहिलो युजर)
    seller = CustomerUser.objects.filter(is_superuser=True).first() or CustomerUser.objects.first()
    
    if not seller:
        return HttpResponse("Error: No user found in database to assign as seller.")

    try:
        total_added = 0
        # २०० वटा सम्म डेटा तान्ने
        prod_response = requests.get(f"{base_url}?limit=200", headers=headers, timeout=15)
        products_data = prod_response.json().get('products', [])

        for item in products_data:
            # २. क्याटगोरी र इन्ट्रेस्ट मिलाउने
            raw_cat = item.get('category', 'General')
            cat_name = raw_cat.replace("-", " ").capitalize()
            category_obj, _ = Category.objects.get_or_create(name=cat_name)
            Interest.objects.get_or_create(name=cat_name)

            # ३. यदि प्रोडक्ट पहिले नै छैन भने मात्र थप्ने
            if not Product.objects.filter(name=item['title']).exists():
                p = Product(
                    name=item['title'],
                    price=round(item['price'] * 130, 2), # USD to NPR
                    description=item.get('description', ''),
                    category=category_obj,
                    seller=seller,
                    
                    # --- नयाँ फिल्डहरू अटोमेटिक भर्ने ---
                    rating=item.get('rating', 0.0),
                    stock=item.get('stock', 0),
                    brand=item.get('brand', ''),
                    sku=item.get('sku', ''),
                    discount_percentage=item.get('discountPercentage', 0.0),
                    
                    # सिधै URL प्रयोग गर्ने (डाउनलोड गर्नु परेन)
                    image_url=item.get('thumbnail') 
                )
                
                # नोट: यदि कसैलाई पुरानो तरिकाले इमेज डाउनलोड नै गर्नु छ भने मात्र यो चाहिन्छ:
                # तर अहिले हामीले image_url प्रयोग गरेका छौँ जुन धेरै फास्ट हुन्छ।
                
                p.save()
                total_added += 1
                
        return HttpResponse(f"""
            <div style="font-family: sans-serif; padding: 20px; border: 2px solid #f85606; border-radius: 10px; width: fit-content;">
                <h1 style="color: #f85606;">✅ Success!</h1>
                <p style="font-size: 18px;">Added <strong>{total_added}</strong> new products.</p>
                <p>Ratings, Stock, and External Image URLs are now synced.</p>
                <a href="/" style="color: #2196F3;">Go to Home</a>
            </div>
        """)

    except Exception as e:
        return HttpResponse(f"<h1 style='color:red;'>Error occurred</h1><p>{str(e)}</p>")