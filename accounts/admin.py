from django.contrib import admin
from .models import CustomerUser, Interest, CustomerActivity

# Register your models here.

class CustomerActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'product_id', 'timestamp', 'transaction_id')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'transaction_id')

# Products ko lagi extra columns dekhauna (Optional but helpful)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'id')
    search_fields = ('name',)

admin.site.register(CustomerUser)
admin.site.register(Interest)
admin.site.register(CustomerActivity, CustomerActivityAdmin)


admin.site.site_header = "Karstore Admin"
admin.site.site_title = "Karstore Admin Portal"
admin.site.index_title = "Welcome to Karstore Admin Portal"