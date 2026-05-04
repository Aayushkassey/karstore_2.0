# from django.db.models import Count
# from django.utils import timezone
# from datetime import timedelta
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.conf import settings
# from .models import CustomerActivity, CustomerUser as User
# from products.models import Product

# def get_recommendations(user):
#     # १. पहिले युजरको रिसेन्ट एक्टिभिटी (Clicks/Views) हेर्ने
#     active_categories = CustomerActivity.objects.filter(user=user) \
#         .values('product__category') \
#         .annotate(count=Count('product__category')) \
#         .order_by('-count')

#     if active_categories.exists():
#         top_category_ids = [item['product__category'] for item in active_categories[:3]]
#         return Product.objects.filter(category_id__in=top_category_ids)[:8]

#     # २. एक्टिभिटी छैन भने युजरले सुरुमा रोजेको 'Interests' हेर्ने
#     if user.interests.exists():
#         interest_names = user.interests.values_list('name', flat=True)
#         return Product.objects.filter(category__name__in=interest_names).distinct().order_by('-id')[:8]

#     # ३. केही छैन भने 'Highly Searched' (धेरै अर्डर भएको) सामान देखाउने
#     highly_searched = Product.objects.annotate(
#         num_sales=Count('order')
#     ).order_by('-num_sales')[:8]

#     # ४. यदि अर्डर नै छैन भने र्‍यान्डम सामान देखाउने
#     if not highly_searched.exists() or highly_searched[0].num_sales == 0:
#         return Product.objects.all().order_by('?')[:8]

#     return highly_searched

# # २. इमेल पठाउने लोजिक
# def send_retention_email(user):
#     products = get_recommendations(user)
#     if not products:
#         return

#     subject = f"We Miss You, {user.username}! Check out these products"
#     context = {'user': user, 'products': products}
    
#     html_message = render_to_string('emails/retention_email.html', context)
    
#     send_mail(
#         subject,
#         "Check out our latest products!",
#         settings.EMAIL_HOST_USER,
#         [user.email],
#         html_message=html_message,
#         fail_silently=False,
#     )

# # ३. Churn हुन लागेका युजर पत्ता लगाउने र इमेल ट्रिगर गर्ने लोजिक
# def check_and_send_retention_emails():
#     # ७ दिनदेखि लगइन नगरेका युजरहरू (Churn Risk)
#     threshold_date = timezone.now() - timedelta(days=7)
#     inactive_users = User.objects.filter(last_login__lte=threshold_date, is_active=True)
    
#     for user in inactive_users:
#         send_retention_email(user)