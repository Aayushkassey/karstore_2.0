# context_processors.py
from django.core.cache import cache
from products.models import Category, Product
from django.db.models import Prefetch

def category_context(request):
    categories = cache.get('nav_categories')
    
    if not categories:
        products_prefetch = Prefetch(
            'product_set',
            queryset=Product.objects.all(),
            to_attr='prefetched_products'
        )
        categories = list(Category.objects.prefetch_related(products_prefetch))
        
        for cat in categories:
            seen = set()
            unique_brands = []
            for p in cat.prefetched_products:
                if p.brand and p.brand not in seen:
                    seen.add(p.brand)
                    unique_brands.append(p.brand)
            cat.unique_brands = unique_brands
        
        cache.set('nav_categories', categories, 60 * 15)
    
    return {'categories': categories}