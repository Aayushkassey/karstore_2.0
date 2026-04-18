from django.db import models
from django.conf import settings

class Payment(models.Model):
    # eSewa ko transaction_uuid ko lagi yo use huncha
    uuid = models.CharField(max_length=255, unique=True)
    
    # User track garna (accounts app sanga link huncha)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    
    # Financial Details (eSewa v2 parameters)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Product Price
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2) # Sum of all above
    
    # Tracking
    product_id = models.CharField(max_length=255) # Multiple ID handle garna CharField ramro
    status = models.CharField(max_length=20, default='PENDING') # PENDING, COMPLETE, FAILED
    created_at = models.DateTimeField(auto_now_add=True)
    
    # eSewa le dine unique ref_id (Verification ko bela kaam lagcha)
    ref_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Payment {self.uuid} - {self.status}"