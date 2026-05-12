import requests
from ml_services.services.preprocessor import build_user_features

CHURN_API_URL = "https://srs-api-3ndl.onrender.com/predict/churn"


def get_churn_score(user_id: int) -> dict:
    """
    Get churn prediction for a single user.
    Sends only the 12 features the XGBoost model was trained on.
    """
    raw = build_user_features(user_id)

    if not raw:
        return {
            "user_id": user_id,
            "churn_probability": None,
            "will_churn": None,
            "risk_level": None,
            "error": "User not found or no activity data"
        }

    # Build exactly what the model expects
    # payload = _build_churn_payload(raw)
    payload = {
        "user_id": user_id,
        "features": _build_churn_payload(raw)
    }

    try:
        response = requests.post(
            CHURN_API_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        return {
            "user_id": user_id,
            "churn_probability": float(data.get("churn_probability", 0.0)),
            "will_churn": data.get("will_churn", False),
            # "risk_level": data.get("risk_level", "low"),  # API returns this directly
            "risk_level": _get_risk_level(float(data.get("churn_probability", 0.0))),  # API returns this directly
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "user_id": user_id,
            "churn_probability": None,
            "will_churn": None,
            "risk_level": None,
            "error": "ML API timeout"
        }
    except requests.exceptions.RequestException as e:
        return {
            "user_id": user_id,
            "churn_probability": None,
            "will_churn": None,
            "risk_level": None,
            "error": str(e)
        }


def get_churn_scores_bulk(user_ids: list) -> list:
    """
    Get churn scores for multiple users.
    Used by the daily scoring job.
    """
    return [get_churn_score(uid) for uid in user_ids]


def _build_churn_payload(raw: dict) -> dict:
    """
    Map preprocessor output to the exact 12 features
    the XGBoost churn model was trained on.
    Ratios use Laplace smoothing (+1) to match training exactly.
    """
    view_count      = raw["total_product_views"]
    wishlist_count  = raw["total_whistles"]        # Whistle DB count
    cart_count      = raw["total_add_to_cart"]
    purchase_count  = raw["total_purchases"]

    total_interactions = (
        raw["total_sessions"] +
        view_count +
        raw["total_searches"] +
        cart_count +
        purchase_count +
        raw["total_whistles_added"]
    )

    activity_span_days = max(raw["activity_span_days"], 0)

    # All ratios use +1 Laplace smoothing — must match training
    view_to_purchase_ratio = view_count / (purchase_count + 1)

    cart_to_purchase_ratio = cart_count / (purchase_count + 1)

    wishlist_to_purchase_ratio = wishlist_count / (purchase_count + 1)

    cart_abandonment_rate = cart_count / (cart_count + purchase_count + 1)

    interactions_per_day = total_interactions / (activity_span_days + 1)

    # Weighted sum: view=1, wishlist=2, cart=3, purchase=5
    total_weight = (
        view_count      * 1 +
        wishlist_count  * 2 +
        cart_count      * 3 +
        purchase_count  * 5
    )

    return {
        "activity_span_days":       activity_span_days,
        "total_interactions":       total_interactions,
        "unique_products":          raw["unique_products_viewed"],
        "view_count":               view_count,
        "total_weight":             total_weight,
        "view_to_purchase_ratio":   round(view_to_purchase_ratio, 4),
        "cart_count":               cart_count,
        "cart_to_purchase_ratio":   round(cart_to_purchase_ratio, 4),
        "cart_abandonment_rate":    round(cart_abandonment_rate, 4),
        "wishlist_count":           wishlist_count,
        "interactions_per_day":     round(interactions_per_day, 4),
        "wishlist_to_purchase_ratio": round(wishlist_to_purchase_ratio, 4),
    }

def _get_risk_level(score: float) -> str:
    """
    Classify churn probability into risk buckets.
    high   >= 0.80  → send retention email + show discount banner
    medium >= 0.55  → show recommendations banner
    low    <  0.55  → normal experience
    """
    if score >= 0.80:
        return "high"
    elif score >= 0.55:
        return "medium"
    else:
        return "low"