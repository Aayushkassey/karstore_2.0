from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

class CustomerUser(AbstractUser):
    ROLE_CHOICES = (
        ('SELLER', 'Seller'),
        ('CUSTOMER', 'Customer'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    
    interests= models.ManyToManyField('Interest', blank=True)
    gender = models.CharField(max_length=10, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(100)])
    
    has_set_interests = models.BooleanField(default=False)


    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name_plural = 'All Users'
    
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
            ('reduce_cart_qty', 'Reduce Cart Quantity'),
            ('remove_from_cart', 'Remove From Cart'),
            ('checkout', 'Checkout'),
            ('purchase_success', 'Purchase Success'),
            ('purchase_failed', 'Purchase Failed'),
            ('update_profile', 'Update Profile'),
            ('view_whistles', 'View Whistles'),
            ('add_whistle', 'Add Whistle'),
            ('remove_whistles', 'Remove Whistles'),
    ]

    user = models.ForeignKey(
        CustomerUser, 
        on_delete=models.CASCADE,
        db_column='user_id'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    def display_action(self):
        if self.action == 'search' and self.extra_info:
            return self.extra_info # यसले "Search query: Ultima Watch" दिन्छ
        if self.action == 'view_product' and self.product:
            return f"Viewed Product: {self.product.name}"
        if self.action == 'view_category' and self.extra_info:
            return f"Viewed {self.extra_info}"
        return self.get_action_display()

    display_action.short_description = 'Action' # टेबलको हेडिङ 'Action' नै रहन्छ

    extra_info = models.CharField(max_length=255,blank=True, null=True)

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

