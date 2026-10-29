import logging

from django.shortcuts import render

from .models import NewsAPIError, fetch_fashion_articles

logger = logging.getLogger(__name__)


def news_index(request):
    query = request.GET.get("q", "").strip()

    try:
        articles = fetch_fashion_articles()
        error_message = None
    except NewsAPIError:
        logger.exception("Unable to load fashion news")
        articles = []
        error_message = "Berita fashion tidak tersedia saat ini. Silakan coba lagi nanti."

    if query:
        normalized_query = query.casefold()
        articles = [
            article
            for article in articles
            if normalized_query
            in " ".join(
                str(value or "")
                for value in (
                    article.get("title"),
                    article.get("description"),
                    article.get("content"),
                    (article.get("source") or {}).get("name")
                    if isinstance(article.get("source"), dict)
                    else "",
                )
            ).casefold()
        ]

    return render(
        request,
        "pages/news/news.html",
        {
            "articles": articles,
            "title_query": query,
            "error_message": error_message,
        },
    )
