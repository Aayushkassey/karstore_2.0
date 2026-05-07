from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import CustomerUser
from products.models import Product
from retention.models import ChurnRecord, RetentionEmail
from ml_services.services.churn import get_churn_score
from ml_services.services.recsys import get_recommendations, get_popular_products


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
        recently_emailed = RetentionEmail.objects.filter(
            user      = user,
            sent_at__gte = seven_days_ago,
            was_sent  = True
        ).exists()

        if recently_emailed:
            skipped += 1
            continue

        # Get recommendations for email
        recs = get_recommendations(user.id, top_n=3)
        product_ids = recs.get('recommendations', [])

        if not product_ids:
            recs = get_popular_products(top_n=3)
            product_ids = recs.get('recommendations', [])

        products = Product.objects.filter(
            id__in  = product_ids,
            stock__gt = 0
        )[:3]

        # Send email
        success = _send_retention_email(user, products, record.churn_probability)

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


def _send_retention_email(user, products, churn_probability):
    """
    Send personalized retention email with discount + recommendations.
    """
    try:
        product_lines = ""
        for p in products:
            if p.discount_percentage and p.discount_percentage > 0: 
                product_lines += f"  • {p.name} - Get {p.discount_percentage:.0f}% off!\n"
            else:
                product_lines += f"  • {p.name} — Rs. {p.price:.0f}\n"  

        if not product_lines:
            product_lines = "  • Check out our latest products!\n"

        risk_pct = int(churn_probability * 100)

        subject = "We miss you at KAR Store - Here's a special offer just for you!"

        message = f"""
Hi {user.username},

We noticed you haven't visited us in a while and we miss you!

Products we think you'll love:
{product_lines}

Don't miss out — this offer is valid for 7 days only.

Shop now at KAR Store!

Best regards,
KAR Store Team
        """.strip()

        send_mail(
            subject         = subject,
            message         = message,
            from_email      = settings.DEFAULT_FROM_EMAIL,
            recipient_list  = [user.email],
            fail_silently   = False,
        )
        return True

    except Exception as e:
        print(f"  Email failed for {user.username}: {e}")
        return False