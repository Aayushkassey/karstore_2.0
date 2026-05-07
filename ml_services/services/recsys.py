import requests
# from ml_services.services.preprocessor import build_user_features

RECSYS_API_URL = "https://srs-api-3ndl.onrender.com/recommend/"
RECSYS_USER_URL = "https://srs-api-3ndl.onrender.com/recommend/user/{user_id}"
POPULAR_API_URL = "https://srs-api-3ndl.onrender.com/popular/"

def _format_user_id(user_id: int) -> str:
    """Convert Django integer user_id to ML model format: 17 → 'R000017'"""
    return f"R{user_id:06d}"

def get_recommendations(user_id: int, top_n: int = 5, exclude_seen: list = None) -> dict:
    """
    POST /recommend/
    API handles all LightFM features internally — we just send user_id.
    """
    payload = {
        "user_id":  _format_user_id(user_id),  # was: str(user_id)
        "top_n": top_n,
        "exclude_seen": exclude_seen or []
    }

    try:
        response = requests.post(
            RECSYS_API_URL,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        return {
            "user_id": user_id,
            "recommendations": data.get("recommendations", []),
            "is_cold_start": data.get("is_cold_start", False),
            "source": data.get("source", "personalized"),
            "error": None
        }

    except requests.exceptions.RequestException as e:
        return get_popular_products(top_n)


def get_recommendations_by_id(user_id: int, top_n: int = 5) -> dict:
    """
    GET /recommend/user/{user_id}
    Lighter call for quick lookups.
    """
    try:
        response = requests.get(
            RECSYS_USER_URL.format(user_id=_format_user_id(user_id)),
            params={"top_n": top_n},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        return {
            "user_id": user_id,
            "recommendations": data.get("recommendations", []),
            "is_cold_start": data.get("is_cold_start", False),
            "source": data.get("source", "personalized"),
            "error": None
        }

    except requests.exceptions.RequestException:
        return get_popular_products(top_n)

def get_popular_products(top_n: int = 5) -> dict:
    """
    GET /popular/
    Fallback for failures. No user needed.
    """
    try:
        response = requests.get(POPULAR_API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()

        product_ids = data.get("product_ids", [])

        return {
            "user_id": None,
            "recommendations": product_ids[:top_n],
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
