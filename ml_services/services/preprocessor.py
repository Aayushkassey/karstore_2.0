from django.utils import timezone
from django.db.models import Count, Sum, Q
from accounts.models import CustomerUser, CustomerActivity
from orders.models import Order, Whistle


def build_user_features(user_id: int) -> dict:
    """
    Build feature dictionary for a single user.
    This is fed directly to the churn and recsys ML APIs.
    """
    try:
        user = CustomerUser.objects.get(id=user_id, role='CUSTOMER')
    except CustomerUser.DoesNotExist:
        return {}

    now = timezone.now()

    # --- Activity querysets ---
    activities = CustomerActivity.objects.filter(user=user)

    # --- Session / login signals ---
    total_sessions = activities.filter(action='login').count()
    last_login = user.last_login
    days_since_last_login = (now - last_login).days if last_login else 999

    # --- Product view signals ---
    total_product_views = activities.filter(action='view_product').count()
    unique_products_viewed = (
        activities.filter(action='view_product', product__isnull=False)
        .values('product')
        .distinct()
        .count()
    )

    # --- Search signals ---
    total_searches = activities.filter(action='search').count()

    # --- Cart signals ---
    total_add_to_cart = activities.filter(action='add_to_cart').count()
    total_remove_from_cart = activities.filter(action='remove_from_cart').count()
    cart_abandonment_rate = (
        round(total_remove_from_cart / total_add_to_cart, 2)
        if total_add_to_cart > 0 else 0.0
    )

    # --- Purchase signals ---
    total_checkouts = activities.filter(action='checkout').count()
    total_purchases = activities.filter(action='purchase_success').count()
    total_failed_purchases = activities.filter(action='purchase_failed').count()
    checkout_to_purchase_rate = (
        round(total_purchases / total_checkouts, 2)
        if total_checkouts > 0 else 0.0
    )

    # --- Order signals (from Order model) ---
    completed_orders = Order.objects.filter(user=user, status='Completed')
    total_completed_orders = completed_orders.count()
    total_spend = float(
        completed_orders.aggregate(total=Sum('final_price'))['total'] or 0.0
    )
    last_order = completed_orders.order_by('-created_at').first()
    days_since_last_purchase = (
        (now - last_order.created_at).days if last_order else 999
    )

    # --- Whistle (wishlist) signals ---
    total_whistles = Whistle.objects.filter(user=user).count()
    total_whistles_added = activities.filter(action='add_whistle').count()
    total_whistles_removed = activities.filter(action='remove_whistles').count()

    # --- Account signals ---
    days_since_joined = (now - user.date_joined).days if user.date_joined else 0
    interests = list(user.interests.values_list('name', flat=True))

    return {
        # Identity
        "user_id": user.id,
        "age": user.age or 0,
        "gender": user.gender or "unknown",
        "interests": interests,
        "days_since_joined": days_since_joined,

        # Engagement
        "total_sessions": total_sessions,
        "days_since_last_login": days_since_last_login,
        "total_product_views": total_product_views,
        "unique_products_viewed": unique_products_viewed,
        "total_searches": total_searches,

        # Cart
        "total_add_to_cart": total_add_to_cart,
        "total_remove_from_cart": total_remove_from_cart,
        "cart_abandonment_rate": cart_abandonment_rate,

        # Purchase
        "total_checkouts": total_checkouts,
        "total_purchases": total_purchases,
        "total_failed_purchases": total_failed_purchases,
        "checkout_to_purchase_rate": checkout_to_purchase_rate,
        "total_completed_orders": total_completed_orders,
        "total_spend": total_spend,
        "days_since_last_purchase": days_since_last_purchase,

        # Wishlist
        "total_whistles": total_whistles,
        "total_whistles_added": total_whistles_added,
        "total_whistles_removed": total_whistles_removed,
    }


def build_all_users_features() -> list:
    """
    Build features for ALL customers.
    Used by the daily scoring job.
    """
    customers = CustomerUser.objects.filter(role='CUSTOMER', is_active=True)
    return [
        features
        for user in customers
        if (features := build_user_features(user.id))
    ]