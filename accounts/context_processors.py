from products.models import Category, Product
from django.db.models import Count

def category_context(request):
    categories = Category.objects.all()
    
    # हरेक क्याटेगोरीका लागि ब्रान्डहरू छुट्टै लिस्टमा हाल्ने
    for category in categories:
        # यो क्याटेगोरीका सामानहरूबाट ब्रान्डको नाम तान्ने (Distinct गरेर)
        category.available_brands = Product.objects.filter(
            category=category
        ).values_list('brand', flat=True).distinct()[:6] # टप ६ वटा मात्र देखाउनz
        
    return {
        'categories': categories
    }