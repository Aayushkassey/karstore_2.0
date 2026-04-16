from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    description = models.TextField()

    price = models.FloatField()
    image = models.ImageField(upload_to='products/')

    total_sales = models.IntegerField(default=0)
    is_whistle = models.BooleanField(default=False)

    def __str__(self):
        return self.name