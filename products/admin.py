# products/admin.py

from django.contrib import admin
from django.db.models import Sum
from .models import Product, Category

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_select_related = ('category', 'seller')
    readonly_fields = ('total_sales_display',)

    fields = (
        'name', 'seller', 'category',
        'total_sales_display', 'sku', 'brand', 'discount_percentage',
        'description', 'price', 'stock', 'rating', 'image'
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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)