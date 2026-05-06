import csv
import os
import django
import sys  
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

#Load .env from the root
load_dotenv(os.path.join(BASE_DIR, ".env"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "karstore.settings")
django.setup()

from accounts.models import CustomerUser, CustomerActivity
from products.models import Product

OUTPUT_DIR = "ml_services/automation/data"

ACTION_MAP = {
    'view_product':     'view',
    'add_whistle':      'wishlist',
    'add_to_cart':      'cart',
    'purchase_success': 'purchase',
}

def export_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    export_interactions()
    export_users()
    export_products()
    print("\nAll CSVs exported successfully.")

def export_interactions():
    path = os.path.join(OUTPUT_DIR, "interactions_export.csv")
    print("Exporting interactions...")

    activities = CustomerActivity.objects.filter(
        action__in=ACTION_MAP.keys(),
        product__isnull=False
    ).select_related('user', 'product').iterator(chunk_size=1000)

    count = 0
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'user_id', 'product_id',
            'event_type', 'interaction_timestamp'
        ])
        for a in activities:
            writer.writerow([
                f"U{a.user.id:06d}",
                a.product.id,
                ACTION_MAP[a.action],
                a.timestamp.isoformat()
            ])
            count += 1

    print(f"  Interactions exported: {count}")
    return path

def export_users():
    path = os.path.join(OUTPUT_DIR, "users_export.csv")
    print("Exporting users...")

    customers = CustomerUser.objects.filter(
        role='CUSTOMER'
    ).prefetch_related('interests').iterator(chunk_size=500)

    count = 0
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'user_id', 'gender', 'age',
            'interests', 'registration_date'
        ])
        for u in customers:
            interests = list(u.interests.values_list('name', flat=True))
            writer.writerow([
                f"U{u.id:06d}",
                u.gender.lower() if u.gender else 'unknown',
                u.age or 0,
                str(interests),
                u.date_joined.isoformat()
            ])
            count += 1

    print(f"  Users exported: {count}")
    return path

def export_products():
    path = os.path.join(OUTPUT_DIR, "products_export.csv")
    print("Exporting products...")

    count = 0
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'name', 'category',
            'brand', 'price', 'rating'
        ])
        for p in Product.objects.select_related('category').iterator():
            writer.writerow([
                p.id,
                p.name,
                p.category.name.lower() if p.category else 'other',
                p.brand.lower() if p.brand else 'unknown',
                p.price,
                p.rating
            ])
            count += 1

    print(f"  Products exported: {count}")
    return path

if __name__ == "__main__":
    export_all()