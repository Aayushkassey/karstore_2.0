from django.urls import path
from .views import *

app_name = 'account'
urlpatterns = [
    path('profile/', view_profile, name='view_profile'),
    path('update_profile/', update_profile, name='update_profile'),
]