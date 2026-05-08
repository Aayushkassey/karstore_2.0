# from urllib import request

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

        # ── EXISTING ──────────────────────────────────────────────────────────
        all_payments = Payment.objects.all()
        total_p      = all_payments.count()
        s_count = all_payments.filter(status__icontains='complete').count()
        if s_count == 0:
            s_count = all_payments.filter(status__icontains='success').count()
        f_count = all_payments.filter(status__icontains='fail').count()
        if f_count == 0:
            f_count = all_payments.filter(status__icontains='cancel').count()
        p_count = total_p - (s_count + f_count)

        extra_context['payment_count']    = total_p
        extra_context['success_payments'] = s_count
        extra_context['failed_payments']  = f_count
        extra_context['pending_payments'] = max(0, p_count)
        extra_context['user_count']       = CustomerUser.objects.filter(
            role='CUSTOMER'
        ).exclude(email__endswith='@synthetic.karstore.com').count()
        extra_context['product_count']    = Product.objects.count()
        extra_context['activity_count']   = CustomerActivity.objects.exclude(
            user__email__endswith='@synthetic.karstore.com'
        ).count()

# ──     CHURN DATA ────────────────────────────────────────────────────────
        from django.db.models import Max
        from django.utils import timezone
        from retention.models import ChurnRecord

        latest = (
            ChurnRecord.objects
            .exclude(user__email__endswith='@synthetic.karstore.com')
            .values('user')
            .annotate(latest=Max('scored_at'))
        )

        high = medium = low = 0
        for entry in latest:
            record = ChurnRecord.objects.filter(
                user_id   = entry['user'],
                scored_at = entry['latest']
            ).first()
            if not record:
                continue
            if record.risk_level == 'high':
                high += 1
            elif record.risk_level == 'medium':
                medium += 1
            else:
                low += 1

        extra_context['churn_high']   = high
        extra_context['churn_medium'] = medium
        extra_context['churn_low']    = low

        # ── 7 DAY TREND ───────────────────────────────────────────────────────
        now = timezone.now()
        trend_labels = []
        trend_values = []

        for i in range(6, -1, -1):
            day       = now - timezone.timedelta(days=i)
            day_start = day.replace(hour=0,  minute=0,  second=0,  microsecond=0)
            day_end   = day.replace(hour=23, minute=59, second=59)

            records = ChurnRecord.objects.filter(
                scored_at__range=(day_start, day_end)
            ).exclude(user__email__endswith='@synthetic.karstore.com')

            avg = 0.0
            if records.exists():
                avg = round(
                    sum(r.churn_probability for r in records) / records.count(), 2
                )

            trend_labels.append(day_start.strftime("%b %d"))
            trend_values.append(avg)

        extra_context['trend_labels'] = trend_labels
        extra_context['trend_values'] = trend_values

        return super().index(request, extra_context)
    
admin.site.__class__ = KarStoreAdminSite