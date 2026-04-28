from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views

# Views import
from .views import login, register, select_interest, logout_view, check_username, check_email, skip_interests

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Main Home Path (Products app bata aauchha)
    path('', include('products.urls')), 
    path('orders/', include('orders.urls')), # Orders app ko URL include gareko
    path('payment/', include('payment.urls')), # Payment app ko URL include gareko
    path('accounts/', include('accounts.urls')), # Accounts app ko URL include gareko
    
    # 2. Authentication Paths (Accounts logic)
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    

    # --- यहाँ Password Reset को Paths हरु थप ---
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
         name='password_reset_complete'),
    # ------------------------------------------

    # 3. Interests & Error Fix Path
    path('select-interest/', select_interest, name='select_interest'),
    path('skip-interests/', skip_interests, name='skip_interests'), # Terminal error fix garna

    # 4. AJAX Validation (karstore/views.py bata)
    path('check-username/', check_username, name='check_username'),
    path('check-email/', check_email, name='check_email'),

]

# Static ra Media handling
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)