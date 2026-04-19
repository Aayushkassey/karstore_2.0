from django.contrib.auth.models import AbstractUser
from django.db import models
# Create your models here.

class CustomerUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('SELLER', 'Seller'),
        ('CUSTOMER', 'Customer'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    
    interests= models.ManyToManyField('Interest', blank=True)

    def __str__(self):
        return self.username
    
class Interest(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class CustomerActivity(models.Model):

    ACTION_CHOICES = [
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('view_home', 'View Home'),
            ('view_dashboard', 'View Dashboard'),
            ('view_product', 'View Product'),
            ('view_category', 'View Category'),
            ('view_orders', 'View Orders'),
            ('delete_order', 'Delete Order'),
            ('search', 'Search'),
            ('add_to_cart', 'Add To Cart'),
            ('remove_from_cart', 'Remove From Cart'),
            ('checkout', 'Checkout'),
            ('purchase_success', 'Purchase Success'),
            ('purchase_failed', 'Purchase Failed'),
            ('update_profile', 'Update Profile'),
            ('view_whistles', 'View Whistles'),
            ('toggle_whistle', 'Toggle Whistle'),
    ]

    user = models.ForeignKey(
        CustomerUser, 
        on_delete=models.CASCADE,
        db_column='user_id'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return f"{self.user} - {self.action}"
    
    class Meta:
        verbose_name_plural = 'Customer Activities'