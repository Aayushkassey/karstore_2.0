from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('category/<int:id>/', category_products, name='category_products'),
    path('dashboard/', dashboard, name='dashboard'),
    path('update_payment_status/<uuid:uuid>/', update_payment_status, name='update_payment_status'),
    path('add-product/', add_product, name='add_product'),
    path('edit-product/<int:product_id>/', edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', delete_product, name='delete_product'),
    path('import-dummy-inventory/', seed_dummy_json_inventory, name='seed_dummy_json_inventory'),
    path('search-suggestions/', search_suggestions, name='search_suggestions'),
    path('product_detail/<int:product_id>/', product_detail, name='product_detail'),
    path('log-product-view/<int:product_id>/', log_product_view, name='log_product_view'),
]