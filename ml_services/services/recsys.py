import requests
from ml_services.services.preprocessor import build_user_features

RECSYS_API_URL = "https://srs-api-3ndl.onrender.com/recommend/"
RECSYS_USER_URL = "https://srs-api-3ndl.onrender.com/recommend/user/{user_id}"
POPULAR_API_URL = "https://srs-api-3ndl.onrender.com/popular/"


def get_recommendations(user_id: int, top_n: int = 5) -> dict:
    """
    Get personalized recommendations via POST /recommend/
    Falls back to popular products if this fails.
    """
    raw = build_user_features(user_id)

    if not raw:
        return get_popular_products(top_n)

    payload = _build_recsys_payload(raw, top_n)

    try:
        response = requests.post(
            RECSYS_API_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        return {
            "user_id": user_id,
            "recommendations": data.get("recommendations", []),
            "source": "personalized",
            "error": None
        }

    except requests.exceptions.RequestException:
        return get_popular_products(top_n)


def get_recommendations_by_id(user_id: int) -> dict:
    """
    Get recommendations via GET /recommend/user/{user_id}
    Lighter call — no feature payload needed.
    """
    try:
        response = requests.get(
            RECSYS_USER_URL.format(user_id=user_id),
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        return {
            "user_id": user_id,
            "recommendations": data.get("recommendations", []),
            "source": "personalized",
            "error": None
        }

    except requests.exceptions.RequestException:
        return get_popular_products()


def get_popular_products(top_n: int = 5) -> dict:
    """
    GET /popular/ — fallback for new users or API failures.
    """
    try:
        response = requests.get(POPULAR_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        products = data.get("popular_products", data) \
            if isinstance(data, dict) else data

        return {
            "user_id": None,
            "recommendations": products[:top_n],
            "source": "popular",
            "error": None
        }

    except requests.exceptions.RequestException as e:
        return {
            "user_id": None,
            "recommendations": [],
            "source": "popular",
            "error": str(e)
        }


def _build_recsys_payload(raw: dict, top_n: int = 5) -> dict:
    """
    Map preprocessor output to exactly what LightFM expects.
    Feature strings must match training format precisely.
    """
    age_group = _get_age_group(raw["age"])
    tenure_band = _get_tenure_band(raw["days_since_joined"])
    gender = raw["gender"].lower() if raw["gender"] else "unknown"

    return {
        "user_id": raw["user_id"],
        "top_n": top_n,

        # Must match training prefix format exactly
        "gender": f"gender:{gender}",
        "age_group": f"age:{age_group}",
        "tenure_band": f"tenure:{tenure_band}",
        "interests": [f"interest:{i.lower()}" for i in raw["interests"]],
    }


def _get_age_group(age: int) -> str:
    """
    Must match training code exactly:
    bins=[0, 25, 35, 45, 60, inf]
    labels=["18_25", "26_35", "36_45", "46_60", "60+"]
    """
    if age <= 0:
        return "unknown"
    elif age <= 25:
        return "18_25"
    elif age <= 35:
        return "26_35"
    elif age <= 45:
        return "36_45"
    elif age <= 60:
        return "46_60"
    else:
        return "60+"


def _get_tenure_band(days: int) -> str:
    """
    Must match training code exactly:
    bins=[0, 15, 30, 90, 270, inf]
    labels=["new", "early", "growing", "established", "loyal"]
    """
    if days <= 15:
        return "new"
    elif days <= 30:
        return "early"
    elif days <= 90:
        return "growing"
    elif days <= 270:
        return "established"
    else:
        return "loyal"