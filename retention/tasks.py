from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import CustomerUser
from products.models import Product
from retention.models import ChurnRecord, RetentionEmail
from ml_services.services.churn import get_churn_score
from ml_services.services.recsys import get_recommendations, get_popular_products
import time
import requests
from retention.models import UserRecommendation, PopularProducts

def wake_ml_api(max_wait=240, interval=15):
    """
    Ping ML API health endpoint until it wakes up.
    Render free tier takes ~30-60s cold start.
    max_wait: maximum seconds to wait (default 4 minutes)
    interval: seconds between pings (default 15s)
    """

    HEALTH_URL = "https://srs-api-3ndl.onrender.com/health"
    print(f"[{timezone.now()}] Waking ML API...")

    waited = 0
    while waited < max_wait:
        try:
            response = requests.get(HEALTH_URL, timeout=10)
            if response.status_code == 200:
                print(f"  ML API is awake after {waited}s")
                return True
        except Exception:
            pass

        print(f"  API sleeping... retrying in {interval}s (waited {waited}s)")
        time.sleep(interval)
        waited += interval

    print(f"  ML API did not wake after {max_wait}s — proceeding anyway")
    return False

def precompute_all():
    """
    Daily job — runs after scoring:
    1. Score all users (churn) → ChurnRecord
    2. Get recommendations for all users → UserRecommendation
    3. Get popular products → PopularProducts
    """
    print(f"[{timezone.now()}] Starting daily precomputation...")

    # Wake API first before any ML calls
    wake_ml_api(max_wait=240, interval=15)

    # ── 1. SCORE ALL USERS ────────────────────────────────────────────────
    score_all_users()

    # ── 2. RECOMMENDATIONS PER USER ───────────────────────────────────────
    customers = CustomerUser.objects.filter(
        role='CUSTOMER',
        is_active=True
    ).exclude(email__endswith='@synthetic.karstore.com')

    pop_cache = PopularProducts.objects.first()
    pop_ids   = pop_cache.product_ids if pop_cache else []

    SYNTHETIC_MAX_ID = 1100
    rec_updated = 0

    for user in customers:
        try:
            recs       = get_recommendations(user.id, top_n=10)
            product_ids = recs.get('recommendations', [])
            is_cold    = recs.get('is_cold_start', True)

            # New real users (added after synthetic injection)
            # model doesn't know them yet → force interest filter
            is_new_real_user = user.id > SYNTHETIC_MAX_ID

            if is_cold or not product_ids or is_new_real_user:
                if user.interests.exists():
                    interest_names = list(
                        user.interests.values_list('name', flat=True)
                    )
                    # Query DB directly — not limited to popular list
                    interest_product_ids = list(
                        Product.objects.filter(
                            category__name__in=interest_names,
                            stock__gt=0
                        ).order_by('-rating').values_list('id', flat=True)[:10]
                    )
                    product_ids = interest_product_ids if interest_product_ids else pop_ids[:10]
                else:
                    product_ids = pop_ids[:10]
                is_cold = True  # mark as cold start

            UserRecommendation.objects.update_or_create(
                user=user,
                defaults={
                    'product_ids':   product_ids,
                    'is_cold_start': is_cold,
                    'source':        recs.get('source', 'popular'),
                }
            )
            rec_updated += 1

        except Exception as e:
            print(f"  Rec failed for {user.username}: {e}")

    print(f"  Recommendations updated: {rec_updated}")

    # ── 3. POPULAR PRODUCTS ───────────────────────────────────────────────
    try:
        popular     = get_popular_products(top_n=200)
        product_ids = popular.get('recommendations', [])
        if product_ids:
            obj = PopularProducts.objects.first()
            if obj:
                obj.product_ids = product_ids
                obj.save()
            else:
                PopularProducts.objects.create(product_ids=product_ids)
            print(f"  Popular products updated: {len(product_ids)} items")
    except Exception as e:
        print(f"  Popular update failed: {e}")

    print(f"[{timezone.now()}] Precomputation complete.")

def score_all_users():
    """
    Daily job: score every customer and save to ChurnRecord.
    """
    print(f"[{timezone.now()}] Starting daily churn scoring...")

    customers = CustomerUser.objects.filter(
        role='CUSTOMER',
        is_active=True
    ).exclude(email__endswith='@synthetic.karstore.com')  # skip synthetic users

    scored   = 0
    failed   = 0
    skipped  = 0

    for user in customers:
        result = get_churn_score(user.id)

        if result.get('error') or result.get('churn_probability') is None:
            failed += 1
            continue

        ChurnRecord.objects.create(
            user              = user,
            churn_probability = result['churn_probability'],
            will_churn        = result['will_churn'],
            risk_level        = result['risk_level'],
        )
        scored += 1

    print(f"  Scored: {scored}, Failed: {failed}, Skipped: {skipped}")
    return {"scored": scored, "failed": failed}


def send_retention_emails():
    """
    Weekly job: send retention emails to high risk users.
    Max one email per user per 7 days.
    Only sends to real users (not synthetic).
    """
    print(f"[{timezone.now()}] Starting retention email job...")

    seven_days_ago = timezone.now() - timezone.timedelta(days=7)

    # Get latest churn record per user
    from django.db.models import Max
    latest_scores = (
        ChurnRecord.objects
        .exclude(user__email__endswith='@synthetic.karstore.com')
        .values('user')
        .annotate(latest=Max('scored_at'))
    )

    sent    = 0
    skipped = 0

    for entry in latest_scores:
        record = ChurnRecord.objects.filter(
            user_id    = entry['user'],
            scored_at  = entry['latest']
        ).first()

        if not record:
            continue

        # Only email high risk users
        if record.risk_level != 'high':
            skipped += 1
            continue

        user = record.user

        # Skip synthetic users
        if user.email.endswith('@synthetic.karstore.com'):
            skipped += 1
            continue

        # Check if already emailed in last 7 days
        # recently_emailed = RetentionEmail.objects.filter(
        #     user      = user,
        #     sent_at__gte = seven_days_ago,
        #     was_sent  = True
        # ).exists()    

        # if recently_emailed:
        #     skipped += 1
        #     continue

        # # Get recommendations for email
        # recs = get_recommendations(user.id, top_n=3)
        # product_ids = recs.get('recommendations', [])

        # if not product_ids:
        #     recs = get_popular_products(top_n=3)
        #     product_ids = recs.get('recommendations', [])

        # Get recommendations from DB cache (no API call)
        
        try:
            user_rec = UserRecommendation.objects.get(user=user)
            product_ids = user_rec.product_ids[:3]
            is_cold = user_rec.is_cold_start
        except UserRecommendation.DoesNotExist:
            product_ids = []
            is_cold = True  

        products = Product.objects.filter(
            id__in  = product_ids,
            stock__gt = 0
        )[:3]

        if is_cold or not product_ids:
            pop_cache = PopularProducts.objects.first()
            pop_ids = pop_cache.product_ids if pop_cache else []
            if pop_ids and user.interests.exists():
                interest_names = list(user.interests.values_list('name', flat=True))
                interest_products = Product.objects.filter(
                    id__in=pop_ids,
                    category__name__in=interest_names,
                    stock__gt=0
                ).values_list('id', flat=True)[:3]
                product_ids = list(interest_products)
            elif pop_ids:
                product_ids = pop_ids[:3]

        

        # Send email
        success = _send_retention_email(user, products, record.churn_probability, is_cold_start=is_cold)

        RetentionEmail.objects.create(
            user       = user,
            email_type = 'discount',
            was_sent   = success,
            error      = None if success else 'Email send failed'
        )

        if success:
            sent += 1
        else:
            skipped += 1

    print(f"  Sent: {sent}, Skipped: {skipped}")
    return {"sent": sent, "skipped": skipped}

def _send_retention_email(user, products, churn_probability, is_cold_start=False):
    try:
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives

        SITE_URL = "http://127.0.0.1:8000"  # change after deploy

        subject = (
            "Welcome to KAR Store — Products picked for you! 🎁"
            if is_cold_start else
            "We miss you at KAR Store — Deals just for you 🎁"
        )

        html_content = render_to_string('emails/retention_email.html', {
            'user':          user,
            'products':      products,
            'is_cold_start': is_cold_start,
            'SITE_URL':      SITE_URL,
        })

        email = EmailMultiAlternatives(
            subject    = subject,
            body       = f"Hi {user.username}, visit KAR Store for personalized deals!",
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True

    except Exception as e:
        print(f"  Email failed for {user.username}: {e}")
        return False