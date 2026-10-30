import requests
from django.conf import settings

NEWS_API_URL = "https://newsapi.org/v2/everything"

FASHION_QUERY = (
    "fashion OR clothing OR apparel OR outfit OR textile "
    "OR fesyen OR pakaian OR busana OR baju OR gaya OR preloved OR thrift OR thrifting"
)

class NewsAPIError(Exception):
    """Raised when NewsAPI is unavailable or returns an error."""

def fetch_fashion_articles():
    api_key = settings.NEWS_API_KEY
    if not api_key:
        raise NewsAPIError("NEWS_API_KEY is not configured.")

    try:
        response = requests.get(
            NEWS_API_URL,
            headers={"X-Api-Key": api_key},
            params={
                "q": FASHION_QUERY,
                "searchIn": "title",
                "language": "en",
                "excludeDomains": "katalogpromosi.com",
                "sortBy": "popularity",
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

    return articles