from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
# Models Import
from accounts.models import CustomerUser, CustomerActivity, Interest

def login(request):

    cutoff_time = timezone.now() - timedelta(hours=24)
    CustomerUser.objects.filter(is_active=False, date_joined__lt=cutoff_time).delete()

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = CustomerUser.objects.get(email=email)
            if not user_obj.is_active:
                return render(request, 'pages/login.html', {"error": "Account not activated. Please check your email."})

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
                
                if not user.has_set_interests:
                    return redirect('select_interest')
                
                return redirect('home')
            else:
                return render(request, 'pages/login.html', {"error": "Invalid password."})
        except CustomerUser.DoesNotExist:
            return render(request, 'pages/login.html', {"error": "No account with this email."})

    return render(request, 'pages/login.html')

import re
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .tokens import generate_token
from django.contrib import messages

def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        u_name = request.POST.get("username")
        if ' ' in u_name:
            return render(request, 'pages/register.html', {"error": "Username cannot contain spaces."})
        email = request.POST.get("email").lower().strip()
        password = request.POST.get("password")
        role = request.POST.get("role", "CUSTOMER")
        gender = request.POST.get("gender")
        age = request.POST.get("age")

        email_regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_regex, email):
            return render(request, 'pages/register.html', {"error": "Invalid email format."})

        allowed_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
        domain = email.split('@')[-1]
        if domain not in allowed_domains:
            return render(request, 'pages/register.html', {"error": "Please use a real email (Gmail, Yahoo, etc.)"})

        if CustomerUser.objects.filter(username__iexact=u_name).exists():
            return render(request, 'pages/register.html', {"error": "Username already taken."})
        
        existing_user = CustomerUser.objects.filter(email__iexact=email).first()

        if existing_user:
            if not existing_user.is_active:
                return render(request, 'pages/login.html', {
                    "error": "Please activate your account first. We have sent you an activation email. If you didn't receive it, please check your spam folder or register again with the same email."
                })
            else:
                return render(request, 'pages/register.html', {
                    "error": "This email is already registered. Please login instead."
                })

        user = CustomerUser.objects.create(
            username=u_name,
            email=email,
            password=make_password(password),
            role=role,
            gender=gender,
            age=age,
            is_active=False 
        )

        current_site = get_current_site(request)
        mail_subject = 'Activate your KAR Store account'
        message = render_to_string('pages/acc_active_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': generate_token.make_token(user),
        })
        
        try:
            email_message = EmailMessage(mail_subject, message, to=[email])
            email_message.send(fail_silently=True)
        except Exception as e:
    
            print(f"Registration Email failed: {e}")

        return render(request, 'pages/login.html', {
            "success": "Registration successful! Please check your email to verify your account."
        })

    return render(request, 'pages/register.html')

def activate(request, uidb64, token):
    try:
        # १. UID डिकोड गर्ने
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomerUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomerUser.DoesNotExist):
        user = None

    # २. टोकन चेक गर्ने र युजर एक्टिभेट गर्ने
    if user is not None and generate_token.check_token(user, token):
        user.is_active = True
        user.save()
        
        auth_login(request, user)
        
        if user.role == 'SELLER':
            return redirect('dashboard')
        else:
            return redirect('select_interest')
    else:
        messages.error(request, "Activation link is invalid or expired!")
        return redirect('login')
    
@login_required
def logout_view(request):
    if request.user.is_authenticated and not request.user.is_superuser and not request.user.is_staff and not request.user.role=='SELLER' and request.user.role == 'CUSTOMER':
        CustomerActivity.objects.create(
            user=request.user, 
            action='logout'
        )
    logout(request)
    return redirect('login')

@login_required
def select_interest(request):
    interests = Interest.objects.all()
    if request.method == "POST":
        selected_ids = request.POST.getlist("interests")
        if selected_ids:
            request.user.interests.set(selected_ids)
        

        request.user.has_set_interests = True
        request.user.save()
        return redirect("home")
    return render(request, "pages/select_interest.html", {"interests": interests})

def skip_interests(request):
    if request.user.is_authenticated:

        request.user.has_set_interests = True
        request.user.save()
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


def about(request):
    return render(request, 'pages/about.html')