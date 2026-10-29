from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import NewsAPIError


class NewsSearchTests(TestCase):
    @patch("news.views.fetch_fashion_articles")
    def test_search_filters_articles_case_insensitively(self, fetch_articles):
        fetch_articles.return_value = [
            {
                "title": "Vintage denim returns",
                "description": "A story about sustainable clothes.",
                "source": {"name": "Style Daily"},
            },
            {
                "title": "Local market opens",
                "description": "Community news.",
                "source": {"name": "City News"},
            },
        ]

        response = self.client.get(reverse("news:news_page"), {"q": "DENIM"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vintage denim returns")
        self.assertNotContains(response, "Local market opens")
        self.assertContains(response, 'value="DENIM"')

    @patch("news.views.fetch_fashion_articles")
    def test_empty_query_displays_all_articles(self, fetch_articles):
        fetch_articles.return_value = [
            {"title": "Vintage denim returns", "url": "https://example.com/article"},
            {"title": "Local market opens"},
        ]

        response = self.client.get(reverse("news:news_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vintage denim returns")
        self.assertContains(response, "Local market opens")
        self.assertContains(response, "Anda akan membuka website lain")
        self.assertContains(response, "news-article-link")
        self.assertContains(response, "news-warning-continue")

    @patch("news.views.fetch_fashion_articles")
    def test_no_matches_show_search_empty_state(self, fetch_articles):
        fetch_articles.return_value = [{"title": "Vintage denim returns"}]

        response = self.client.get(reverse("news:news_page"), {"q": "shoes"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tidak ada berita yang cocok")

    @patch("news.views.fetch_fashion_articles", side_effect=NewsAPIError("offline"))
    def test_api_error_displays_error_message(self, fetch_articles):
        response = self.client.get(reverse("news:news_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Berita fashion tidak tersedia saat ini")
