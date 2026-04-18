from django.urls import path
from .views import *

app_name = 'payment'
urlpatterns = [
    path('checkout/', checkout_process, name='checkout_process'),
    path('initiate-esewa/<uuid:uuid>/', initiate_esewa, name='initiate_esewa'),
    path('success/<uuid:uuid>/', payment_success, name='payment_success'),
    path('failure/<uuid:uuid>/', payment_failure, name='payment_failure'),
]