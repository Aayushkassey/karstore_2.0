# accounts/context_processors.py
from products.models import Category

def category_context(request):
    return {
        'categories': Category.objects.all()
    }