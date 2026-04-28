from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Interest 


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# class Product(models.Model):
#     seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)

#     name = models.CharField(max_length=100)
#     description = models.TextField()

#     price = models.FloatField()
#     image = models.ImageField(upload_to='products/')

#     total_sales = models.IntegerField(default=0)
#     is_whistle = models.BooleanField(default=False)

#     def __str__(self):
#         return self.name


    
class Product(models.Model):

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_sales = models.IntegerField(default=0)

    # ProductTable बाट ल्याइएका नयाँ फिल्डहरू
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.FloatField()

    brand = models.CharField(max_length=100, blank=True, null=True)
    rating = models.FloatField(default=3.0)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    discount_percentage = models.FloatField(default=0.0, null=True, blank=True) # नयाँ
    # warranty_information = models.CharField(max_length=200, blank=True, null=True)
    # weight = models.FloatField(null=True, blank=True)
    # dimensions = models.CharField(max_length=100, null=True, blank=True)
    # tags = models.JSONField(default=list, blank=True) # JSONField को लागि Postgres वा नयाँ Django चाहिन्छ
    # availability_status = models.CharField(max_length=50, null=True, blank=True)
    # reviews = models.JSONField(default=list, blank=True) # JSONField को लागि Postgres वा नयाँ Django चाहिन्छ
    # return_policy = models.CharField(max_length=200, blank=True, null=True)
    # minimum_order_quantity = models.IntegerField(default=1)
    # maximum_order_quantity = models.IntegerField(default=100)
    # meta = models.JSONField(default=dict, blank=True) # JSONField को लागि Postgres वा नयाँ Django चाहिन्छ
    # shipping_information = models.TextField(blank=True, null=True)
    
    
    image = models.ImageField(upload_to='products/' ,null=True, blank=True)
    image_url = models.URLField(max_length=500,blank=True, null=True)
    # thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)

    def __str__(self):
        return self.name
    
    def get_total_sales(self):
        from orders.models import Order 
        
        orders = Order.objects.filter(product=self, status='Completed')
        total = sum(order.quantity for order in orders)
        return total
    
    @property
    def discounted_price(self):
        """डिस्काउन्ट पछिको वास्तविक मूल्य निकाल्ने"""
        if self.discount_percentage > 0:
            discount_amount = (self.price * self.discount_percentage) / 100
            return self.price - discount_amount
        return self.price
    
    class Meta:
        verbose_name_plural = "Products Table"

@receiver(post_save, sender=Category)
def sync_category_to_interest(sender, instance, created, **kwargs):
    if created:
        try:
            
            Interest.objects.get_or_create(name=instance.name)
        except Exception as e:
            print(f"Error syncing interest: {e}")