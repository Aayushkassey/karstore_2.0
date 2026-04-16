from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required

# Models import
from accounts.models import CustomerUser, CustomerActivity, Interest
from products.models import Product, Category 

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')

    query = request.GET.get('q', '')
    all_categories = Category.objects.all() # Navbar ko lagi
    
    if query:
        product_list = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).distinct().order_by('-id')
    else:
        product_list = Product.objects.all().order_by('-id')

    paginator = Paginator(product_list, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/landing.html', {
        'page_obj': page_obj,
        'products': page_obj, 
        'categories': all_categories, # Navbar ma black strip dekhinchha
        'query': query
    })

def login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = CustomerUser.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                auth_login(request, user)
                CustomerActivity.objects.create(user=user, action='login')
                
                if user.role == 'SELLER':
                    return redirect('dashboard')
                if not user.interests.exists():
                    return redirect('select_interest')
                return redirect('home')
            else:
                return render(request, 'pages/login.html', {"error": "Invalid email or password"})
        except CustomerUser.DoesNotExist:
            return render(request, 'pages/login.html', {"error": "Invalid email or password"})

    return render(request, 'pages/login.html')

@login_required
def home(request):
    all_categories = Category.objects.all()
    user_interests = request.user.interests.values_list('name', flat=True)
    
    if user_interests:
        product_list = Product.objects.filter(category__name__in=user_interests).distinct().order_by('-id')
        message = "Recommended for You"
    else:
        product_list = Product.objects.all().order_by('-id')
        message = "Popular Products"

    paginator = Paginator(product_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/home.html', {
        'page_obj': page_obj, 
        'message': message,
        'categories': all_categories # Navbar fix garna
    })