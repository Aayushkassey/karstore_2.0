from django.db import models
from django.conf import settings


class ChurnRecord(models.Model):
    """
    Stores daily churn score for each user.
    Allows trend tracking over time.
    """
    RISK_CHOICES = [
        ('high',   'High'),
        ('medium', 'Medium'),
        ('low',    'Low'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='churn_records'
    )
    churn_probability = models.FloatField()
    will_churn        = models.BooleanField(default=False)
    risk_level        = models.CharField(max_length=10, choices=RISK_CHOICES)
    scored_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scored_at']
        verbose_name_plural = 'Churn Records'

    def __str__(self):
        return f"{self.user.username} — {self.risk_level} ({self.churn_probability:.2f}) @ {self.scored_at.date()}"


class RetentionEmail(models.Model):
    """
    Tracks retention emails sent to users.
    Prevents spamming — max one email per 7 days per user.
    """
    EMAIL_TYPE_CHOICES = [
        ('discount',        'Discount Offer'),
        ('recommendations', 'Product Recommendations'),
        ('winback',         'Win Back'),
    ]

    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='retention_emails'
    )
    email_type  = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    sent_at     = models.DateTimeField(auto_now_add=True)
    was_sent    = models.BooleanField(default=True)
    error       = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name_plural = 'Retention Emails'

    def __str__(self):
        return f"{self.user.username} — {self.email_type} @ {self.sent_at.date()}"

class UserRecommendation(models.Model):
    """
    Stores daily precomputed recommendations per user.
    Updated by daily scheduler. Read by home page view.
    """
    user         = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendation'
    )
    product_ids  = models.JSONField(default=list)
    is_cold_start = models.BooleanField(default=True)
    source       = models.CharField(max_length=20, default='popular')
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User Recommendations'

    def __str__(self):
        return f"{self.user.username} — {self.source} ({self.updated_at.date()})"
    
class PopularProducts(models.Model):
    """
    Stores latest popular product IDs.
    Single row, updated daily.
    """
    product_ids = models.JSONField(default=list)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Popular Products Cache'

    def __str__(self):
        return f"Popular products — {self.updated_at.date()}"