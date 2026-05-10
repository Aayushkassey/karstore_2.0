from django.contrib import admin
from django.db import models
from django.db.models import Max, Avg, Count, Q, Subquery, OuterRef
from django.utils import timezone
from .models import CustomerUser, Interest, CustomerActivity
from payment.models import Payment
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from products.models import Product
from orders.models import Order
from retention.models import ChurnRecord

# 1. Activity Admin
class CustomerActivityAdmin(admin.ModelAdmin):
    list_select_related = ('user',)
    list_display = ('user', 'display_action', 'product_id', 'timestamp', 'transaction_id')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'transaction_id')

# 2. User Admin
class CustomerUserAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('interests')

    list_display = ('username', 'email', 'role', 'gender', 'display_interests', 'age')
    list_filter = ('role', 'gender')
    search_fields = ('username', 'email')
    filter_horizontal = ('interests',)

    def display_interests(self, obj):
        return ", ".join([interest.name for interest in obj.interests.all()])
    display_interests.short_description = 'Interests'

# 3. Payment Admin
class PaymentAdmin(admin.ModelAdmin):
    list_select_related = ('user',)
    list_display = ('user', 'amount', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'transaction_id')

# 4. Custom Admin Site
class KarStoreAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Synthetic User Filters (Fixed: use user__email for models with foreign keys)
        synthetic_user_filter = Q(email__endswith='@synthetic.karstore.com')
        synthetic_activity_filter = Q(user__email__endswith='@synthetic.karstore.com')

        # --- A. Payment Stats ---
        payments_stats = Payment.objects.aggregate(
            total=Count('id'),
            success=Count('id', filter=Q(status__icontains='complete') | Q(status__icontains='success')),
            failed=Count('id', filter=Q(status__icontains='fail') | Q(status__icontains='cancel'))
        )
        extra_context['payment_count'] = payments_stats['total']
        extra_context['success_payments'] = payments_stats['success']
        extra_context['failed_payments'] = payments_stats['failed']
        extra_context['pending_payments'] = max(0, payments_stats['total'] - (payments_stats['success'] + payments_stats['failed']))

        # --- B. Counts (Fixed filters) ---
        extra_context['user_count'] = CustomerUser.objects.filter(role='CUSTOMER').exclude(synthetic_user_filter).count()
        extra_context['product_count'] = Product.objects.count()
        extra_context['activity_count'] = CustomerActivity.objects.exclude(synthetic_activity_filter).count()

        # --- C. CHURN PIE CHART (LATEST RECORD ONLY) ---
        # Fixed: Filter by user__email
        latest_ids_subquery = ChurnRecord.objects.exclude(
            user__email__endswith='@synthetic.karstore.com'
        ).values('user').annotate(
            latest_id=Max('id')
        ).values('latest_id')

        churn_stats = ChurnRecord.objects.filter(id__in=Subquery(latest_ids_subquery)).values('risk_level').annotate(
            count=Count('id')
        )

        risk_map = {item['risk_level']: item['count'] for item in churn_stats}
        extra_context['churn_high'] = risk_map.get('high', 0)
        extra_context['churn_medium'] = risk_map.get('medium', 0)
        extra_context['churn_low'] = risk_map.get('low', 0)

        # --- D. 7 DAY TREND ---
        now = timezone.now()
        seven_days_ago = now - timezone.timedelta(days=7)
        
        trend_data = ChurnRecord.objects.filter(
            scored_at__gte=seven_days_ago
        ).exclude(user__email__endswith='@synthetic.karstore.com').values('scored_at__date').annotate(
            avg_prob=Avg('churn_probability')
        ).order_by('scored_at__date')

        extra_context['trend_labels'] = [d['scored_at__date'].strftime("%b %d") for d in trend_data]
        extra_context['trend_values'] = [round(d['avg_prob'], 2) for d in trend_data]

        return super().index(request, extra_context)

# Admin Configuration
admin.site.__class__ = KarStoreAdminSite
admin.site.site_header = "KarStore Admin"
admin.site.site_title = "KarStore Admin Portal"
admin.site.index_title = "Welcome to KarStore Admin Portal"

# Registration
admin.site.register(Interest)
admin.site.register(CustomerActivity, CustomerActivityAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(CustomerUser, CustomerUserAdmin)