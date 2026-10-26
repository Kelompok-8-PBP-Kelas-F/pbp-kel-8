import requests
from django.conf import settings

NEWS_API_URL = "https://newsapi.org/v2/everything"

# Updated to include Indonesian terms for the API query
FASHION_QUERY = "fashion OR fesyen OR pakaian OR busana"

# Strict local filtering list updated with Indonesian keywords
FASHION_TERMS = (
    "fashion",
    "fesyen",
    "pakaian",
    "baju",
    "busana",
    "garmen",
    "tekstil",
    "pakaian bekas", # thrift
    "thrift",
    "streetwear",
)

class NewsAPIError(Exception):
    """Raised when NewsAPI is unavailable or returns an error."""

def fetch_fashion_articles():
    # Recommended: Use settings.NEWS_API_KEY instead of hardcoding
    api_key = "1b451d39abef44c5b93e5f02f4c77f47"
    if not api_key:
        raise NewsAPIError("NEWS_API_KEY is not configured.")

    try:
        response = requests.get(
            NEWS_API_URL,
            headers={"X-Api-Key": api_key},
            params={
                "q": FASHION_QUERY,
                "searchIn": "title,description",  
                "language": "id",  
                "excludeDomains": "katalogpromosi.com",
                "sortBy": "publishedAt",
                "pageSize": 100,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise NewsAPIError("Could not reach NewsAPI.") from exc
    except ValueError as exc:
        raise NewsAPIError("NewsAPI returned an invalid response.") from exc

    if not isinstance(payload, dict):
        raise NewsAPIError("NewsAPI returned an unexpected response.")

    if payload.get("status") != "ok":
        raise NewsAPIError(payload.get("message", "NewsAPI returned an error."))

    articles = payload.get("articles", [])
    if not isinstance(articles, list):
        raise NewsAPIError("NewsAPI returned an invalid articles list.")

    fashion_articles = []
    for article in articles:
        text = " ".join(
            str(article.get(field) or "")
            for field in ("title", "description", "content")
        ).lower()

        if any(term in text for term in FASHION_TERMS):
            fashion_articles.append(article)

    return fashion_articles