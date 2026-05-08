from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Max, Count
from django.utils import timezone

from accounts.models import CustomerUser
from products.models import Product
from retention.models import ChurnRecord, RetentionEmail
from ml_services.services.churn import get_churn_score
from ml_services.services.recsys import get_recommendations, get_popular_products


# DASHBOARD 
@staff_member_required
@require_GET
def dashboard_data(request):
    """
    GET /api/retention/dashboard/
    Feeds churn distribution data to Jazzmin admin charts.
    """
    # Latest churn record per real user
    latest = (
        ChurnRecord.objects
        .exclude(user__email__endswith='@synthetic.karstore.com')
        .values('user')
        .annotate(latest=Max('scored_at'))
    )

    high   = 0
    medium = 0
    low    = 0

    for entry in latest:
        record = ChurnRecord.objects.filter(
            user_id   = entry['user'],
            scored_at = entry['latest']
        ).first()

        if not record:
            continue

        if record.risk_level == 'high':
            high += 1
        elif record.risk_level == 'medium':
            medium += 1
        else:
            low += 1

    total_real_users = CustomerUser.objects.filter(
        role='CUSTOMER',
        is_active=True
    ).exclude(email__endswith='@synthetic.karstore.com').count()

    # Trend — last 7 days average churn probability
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    trend = []
    for i in range(7):
        day = timezone.now() - timezone.timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = day.replace(hour=23, minute=59, second=59)

        records = ChurnRecord.objects.filter(
            scored_at__range=(day_start, day_end)
        ).exclude(user__email__endswith='@synthetic.karstore.com')

        avg = 0.0
        if records.exists():
            avg = round(
                sum(r.churn_probability for r in records) / records.count(), 4
            )

        trend.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "avg_churn": avg,
            "count": records.count()
        })

    # Recent emails sent
    recent_emails = RetentionEmail.objects.filter(
        was_sent=True
    ).exclude(
        user__email__endswith='@synthetic.karstore.com'
    ).order_by('-sent_at')[:5].values(
        'user__username', 'email_type', 'sent_at'
    )

    return JsonResponse({
        "total_users": total_real_users,
        "scored_users": high + medium + low,
        "risk_distribution": {
            "high":   high,
            "medium": medium,
            "low":    low,
        },
        "trend": list(reversed(trend)),
        "recent_emails": list(recent_emails),
    })


# BANNER API
@require_GET
def banner_data(request):
    """
    GET /api/retention/banner/
    Called when a user logs in to determine what banner to show.
    Returns banner type and recommended products.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"show": False})

    user = request.user

    # Skip synthetic users
    if user.email.endswith('@synthetic.karstore.com'):
        return JsonResponse({"show": False})

    # Get churn score
    result = get_churn_score(user.id)

    if result.get('error') or result.get('churn_probability') is None:
        return JsonResponse({"show": False})

    churn_prob = result['churn_probability']
    risk_level = result['risk_level']

    # Low risk — no banner
    if risk_level == 'low':
        return JsonResponse({"show": False, "risk_level": "low"})

    # Get recommendations
    recs = get_recommendations(user.id, top_n=5)
    product_ids = recs.get('recommendations', [])

    if not product_ids:
        recs = get_popular_products(top_n=5)
        product_ids = recs.get('recommendations', [])

    # Fetch product details from DB
    products = Product.objects.filter(
        id__in=product_ids,
        stock__gt=0
    ).values(
        'id', 'name', 'price',
        'discount_percentage', 'image_url'
    )[:5]

    product_list = []
    for p in products:
        product_list.append({
            "id":                  p['id'],
            "name":                p['name'],
            "price":               p['price'],
            "discount_percentage": p['discount_percentage'],
        })

    # High risk — discount banner
    if risk_level == 'high':
        return JsonResponse({
            "show":             True,
            "type":             "discount",
            "risk_level":       "high",
            "churn_probability": churn_prob,
            "message":          "We miss you! Here are some deals picked just for you.",
            "recommendations":  product_list,
        })

    # Medium risk — recommendations banner
    return JsonResponse({
        "show":             True,
        "type":             "recommendations",
        "risk_level":       "medium",
        "churn_probability": churn_prob,
        "message":          "Products we think you'll love.",
        "recommendations":  product_list,
    })

@staff_member_required
@require_POST
def trigger_retention_emails(request):
    from retention.tasks import send_retention_emails
    result = send_retention_emails()
    return JsonResponse(result)