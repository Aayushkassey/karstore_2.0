from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Models Import
from accounts.models import CustomerUser, CustomerActivity, Interest

def login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = CustomerUser.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                auth_login(request, user)

                # --- FIX STARTS HERE ---
                # Admin/Seller ko activity record nagarne ra Unique Error hataune
                if user.is_authenticated and not user.is_superuser and not user.is_staff and not user.role=='SELLER' and user.role == 'CUSTOMER':
                    CustomerActivity.objects.create(user=user, action='login')
                # --- FIX ENDS HERE ---

                if user.role == 'SELLER':
                    return redirect('dashboard')
                
                if not user.interests.exists():
                    return redirect('select_interest')
                
                return redirect('home')
            else:
                return render(request, 'pages/login.html', {"error": "Invalid password."})
        except CustomerUser.DoesNotExist:
            return render(request, 'pages/login.html', {"error": "No account with this email."})

    return render(request, 'pages/login.html')

def register(request):
    if request.method == 'POST':
        u_name = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "CUSTOMER")

        if CustomerUser.objects.filter(username=u_name).exists():
            return render(request, 'pages/register.html', {"error": "Username taken."})

        CustomerUser.objects.create(
            username=u_name,
            email=email,
            password=make_password(password),
            role=role
        )
        return redirect('login')
    return render(request, 'pages/register.html')

@login_required
def logout_view(request):
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user, 
            action='logout'
        )
    logout(request)
    return redirect('home')

@login_required
def select_interest(request):
    interests = Interest.objects.all()
    if request.method == "POST":
        selected_ids = request.POST.getlist("interests")
        if selected_ids:
            request.user.interests.set(selected_ids)
            return redirect("home")
    return render(request, "pages/select_interest.html", {"interests": interests})

def skip_interests(request):
    """Terminal error fix garna ko lagi, aba yo URL ma hit garda pani home ma jancha."""
    return redirect('home')

# AJAX Validation Utils
def check_username(request):
    value = request.GET.get('value', '').strip()
    exists = CustomerUser.objects.filter(username__iexact=value).exists()
    status = "<span style='color:red;'>Taken!</span>" if exists else "<span style='color:green;'>Available</span>"
    return HttpResponse(status)

def check_email(request):
    value = request.GET.get('value', '').strip()
    exists = CustomerUser.objects.filter(email__iexact=value).exists()
    status = "<span style='color:red;'>Registered!</span>" if exists else "<span style='color:green;'>Available</span>"
    return HttpResponse(status)