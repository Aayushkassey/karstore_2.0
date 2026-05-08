from django.contrib import admin
from retention.models import ChurnRecord, RetentionEmail


@admin.register(ChurnRecord)
class ChurnRecordAdmin(admin.ModelAdmin):
    list_display  = ['user', 'churn_probability', 'risk_level', 'will_churn', 'scored_at']
    list_filter   = ['risk_level', 'will_churn', 'scored_at']
    search_fields = ['user__username', 'user__email']
    ordering      = ['-scored_at']
    readonly_fields = ['user', 'churn_probability', 'risk_level', 'will_churn', 'scored_at']

    def has_add_permission(self, request):
        return False  # only created by scheduler, not manually


@admin.register(RetentionEmail)
class RetentionEmailAdmin(admin.ModelAdmin):
    list_display  = ['user', 'email_type', 'was_sent', 'sent_at', 'error']
    list_filter   = ['email_type', 'was_sent', 'sent_at']
    search_fields = ['user__username', 'user__email']
    ordering      = ['-sent_at']
    readonly_fields = ['user', 'email_type', 'was_sent', 'sent_at', 'error']

    def has_add_permission(self, request):
        return False