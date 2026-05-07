from urllib import request

from django.contrib import admin


from django.db import models
from .models import CustomerUser, Interest, CustomerActivity
from payment.models import Payment
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from products.models import Product
from orders.models import Order

# Register your models here.

class CustomerActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_action', 'product_id', 'timestamp', 'transaction_id')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'transaction_id')



class CustomerUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomerUser
        # यहाँ पासवर्ड फिल्डहरू राख्नु पर्दैन, UserCreationForm ले आफैँ मिलाउँछ
        fields = ('username', 'email', 'role', 'gender', 'age', 'interests')

# २. एडमिन क्लास
class CustomerUserAdmin(BaseUserAdmin):
    add_form = CustomerUserCreationForm
    
    list_display = ('username', 'email', 'role', 'gender', 'display_interests', 'age')
    list_filter = ('role', 'gender', 'id')
    search_fields = ('username', 'email')
    filter_horizontal = ('interests',)

    # युजर Edit गर्दा देखिने फिल्डहरू
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Extra Info', {'fields': ('role', 'gender', 'age', 'interests')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    # ✅ नयाँ युजर थप्दा देखिने फिल्डहरू (यहाँ 'usable_password' कतै पनि नराख्ने)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'role', 'gender', 'age', 'interests'),
        }),
    )

    def display_interests(self, obj):
        return ", ".join([interest.name for interest in obj.interests.all()])
    
    display_interests.short_description = 'Interests'

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status')
    list_filter = ('user__username', 'status')
    search_fields = ('user__username', 'transaction_id')

admin.site.register(Interest)
admin.site.register(CustomerActivity, CustomerActivityAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(CustomerUser, CustomerUserAdmin)



admin.site.site_header = "KarStore Admin"
admin.site.site_title = "KarStore Admin Portal"
admin.site.index_title = "Welcome to KarStore Admin Portal"




class KarStoreAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # १. बक्सको लागि Total (यसले ८२ देखाउँछ)
        all_payments = Payment.objects.all()
        total_p = all_payments.count()
        extra_context['payment_count'] = total_p

        # २. चार्टको लागि: सिधै Payment मोडलको status हेर्ने (Order होइन)
        # यसले ३७ र ४५ को हिसाब ठ्याक्कै मिलाउँछ
        s_count = all_payments.filter(status__icontains='complete').count()
        if s_count == 0:
            s_count = all_payments.filter(status__icontains='success').count()

        f_count = all_payments.filter(status__icontains='fail').count()
        if f_count == 0:
            f_count = all_payments.filter(status__icontains='cancel').count()

        # ३. पेन्डिङको हिसाब: ८२ - (३७ + ४५) = ०
        # नयाँ पर्चेज गर्दा १ वटा पेमेन्ट थपिन्छ र त्यो यहाँ पेन्डिङमा देखिन्छ
        p_count = total_p - (s_count + f_count)

        extra_context['success_payments'] = s_count
        extra_context['failed_payments'] = f_count
        extra_context['pending_payments'] = max(0, p_count)

        # ४. अन्य काउन्टहरू
        extra_context['user_count'] = CustomerUser.objects.count()
        extra_context['product_count'] = Product.objects.count()
        extra_context['activity_count'] = CustomerActivity.objects.count()

        return super().index(request, extra_context)
    
admin.site.__class__ = KarStoreAdminSite