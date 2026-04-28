# products/admin.py

from django.contrib import admin
from .models import Product, Category

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ('total_sales_display',)

    fields = (
        'name', 'seller', 'category', 
        'total_sales_display','sku', 'brand', 'discount_percentage',
        'description', 'price', 'stock', 'rating', 'image'
    )
    
    list_display = (
        'id', 'name', 'description', 'price', 'total_sales_display', 'category', 
        'rating', 'stock', 'brand','discount_percentage', 'sku', 
    )
    
    list_filter = ('name', 'category', 'rating', 'stock', 'price', 'total_sales',)
    
    def total_sales_display(self, obj):
        count= obj.get_total_sales()
        return f"{obj.get_total_sales()} Units"
    
    total_sales_display.short_description = 'Total Sales'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)