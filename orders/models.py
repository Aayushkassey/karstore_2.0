from django.db import models
from django.conf import settings
from products.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from payment.models import Payment

# 1. Cart: User ko active shopping session
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.user.username}"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

# 2. CartItem: Cart bhitra ko individual products
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.product.discounted_price * self.quantity

# 3. Order: Checkout garepachi banne record (Timro existing model ali modify gareko)
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.status})"
    
@receiver(post_save, sender=Order)
def sync_status_to_payment(sender, instance, **kwargs):
    # अर्डरसँग जोडिएको पछिल्लो पेमेन्ट खोज्ने
    payment = Payment.objects.filter(user=instance.user).last()
    
    if payment:
        new_status = 'Pending'
        if instance.status == 'Completed':
            new_status = 'Completed'
        elif instance.status == 'Cancelled':
            new_status = 'FAILED'
        

        Payment.objects.filter(id=payment.id).update(status=new_status)

class Whistle(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') 

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"