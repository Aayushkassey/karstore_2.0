from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Views import
from .views import login, register, select_interest, logout_view, check_username, check_email, skip_interests

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Main Home Path (Products app bata aauchha)
    path('', include('products.urls')), 
    path('orders/', include('orders.urls')), # Orders app ko URL include gareko
    
    # 2. Authentication Paths (Accounts logic)
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    
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