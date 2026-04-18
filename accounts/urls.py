from django.urls import path
from .views import *

app_name = 'account'
urlpatterns = [
    path('update_profile/', update_profile, name='update_profile'),
]