import logging

from django.shortcuts import render

from .models import NewsAPIError, fetch_fashion_articles

logger = logging.getLogger(__name__)


def news_index(request):
    try:
        articles = fetch_fashion_articles()
        error_message = None
    except NewsAPIError:
        logger.exception("Unable to load fashion news")
        articles = []
        error_message = "Berita fashion tidak tersedia saat ini. Silakan coba lagi nanti."

    return render(
        request,
        "pages/news/news.html",
        {
            "articles": articles,
            "error_message": error_message,
        },
    )