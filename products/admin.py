# products/admin.py

from django.contrib import admin
from django.db.models import Sum
from .models import Product, Category

from django.utils.html import format_html

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_select_related = ('category', 'seller')
    readonly_fields = ('total_sales_display', 'image_preview')

    fields = (
        'name', 'seller', 'category',
        'total_sales_display', 'sku', 'brand', 'discount_percentage',
        'description', 'price', 'stock', 'rating', 'image', 'image_url', 'image_preview'
    )

    list_display = (
        'id', 'name', 'price', 'total_sales_display', 'category',
        'rating', 'stock', 'brand', 'sku',
    )

    list_filter = ('category', 'rating', 'stock')
    search_fields = ('name', 'sku')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            total_sales_annotated=Sum('order__quantity')
        )

    def total_sales_display(self, obj):
        total = getattr(obj, 'total_sales_annotated', None) or 0
        return f"{total} Units"
    total_sales_display.short_description = 'Total Sales'
    total_sales_display.admin_order_field = 'total_sales_annotated'

    def image_preview(self, obj):
        url = obj.display_image
        if url:
            return format_html('<img src="{}" width="150" style="object-fit:contain; border-radius:8px;">', url)
        return "No Image"
    image_preview.short_description = 'Image Preview'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)