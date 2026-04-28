from django.contrib import admin
from .models import CustomerUser, Interest, CustomerActivity
from payment.models import Payment
# Register your models here.

class CustomerActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_action', 'product_id', 'timestamp', 'transaction_id')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'transaction_id')



class CustomerUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'gender', 'display_interests','age')
    list_filter = ('role', 'gender')
    search_fields = ('username', 'email')

    def display_interests(self, obj):
        return ", ".join([interest.name for interest in obj.interests.all()])



admin.site.register(Interest)
admin.site.register(CustomerActivity, CustomerActivityAdmin)
admin.site.register(Payment)
admin.site.register(CustomerUser, CustomerUserAdmin)



admin.site.site_header = "KarStore Admin"
admin.site.site_title = "KarStore Admin Portal"
admin.site.index_title = "Welcome to KarStore Admin Portal"