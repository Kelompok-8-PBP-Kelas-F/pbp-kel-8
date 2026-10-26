from django.db import models
import requests
from django.conf import settings

NEWS_API_URL = "https://newsapi.org/v2/everything"

FASHION_QUERY = (
    'fashion OR clothing OR apparel OR garment OR textile OR runway OR couture '
    'OR "slow fashion" OR "sustainable fashion" OR thrift OR streetwear'
)

FASHION_TERMS = (
    "fashion",
    "clothing",
    "apparel",
    "garment",
    "textile",
    "runway",
    "couture",
    "slow fashion",
    "sustainable fashion",
    "thrift",
    "streetwear",
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
                "searchIn": "title,description,content",
                "language": "en",
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
