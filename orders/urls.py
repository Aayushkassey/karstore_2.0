from django.urls import path
from .views import *

urlpatterns = [
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_detail, name='cart_detail'), 
    path('remove-from-cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('update-cart-qty/<int:product_id>/', update_cart_qty, name='update_cart_qty'),
    path('my-orders/', orders_view, name='orders'),
    path('update-order-status/', update_order_status, name='update_order_status'),
    path('delete-order/<int:order_id>/', delete_order, name='delete_order'),
    path('products/', product_list, name='products'),
    path('whistles/', whistles_view, name='whistles'),
    path('toggle-whistle/<int:product_id>/', toggle_whistle, name='toggle_whistle'),
]