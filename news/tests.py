from unittest.mock import patch

import requests
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    FASHION_QUERY,
    NEWS_API_URL,
    NewsAPIError,
    fetch_fashion_articles,
)


class NewsSearchTests(TestCase):
    url = reverse("news:news_page")

    @patch("news.views.fetch_fashion_articles")
    def test_search_filters_all_supported_fields_case_insensitively(
        self, fetch_articles
    ):
        fetch_articles.return_value = [
            {"title": "DENIM jacket"},
            {"description": "A story about denim."},
            {"content": "The rise of denim."},
            {"source": {"name": "Denim Daily"}},
            {"title": "Unrelated", "source": "Denim Daily"},
            {"title": "Local market opens"},
        ]

        response = self.client.get(self.url, {"q": "  DENIM "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["title_query"], "DENIM")
        self.assertEqual(
            len(response.context["articles"]),
            4,
        )
        self.assertContains(response, 'value="DENIM"')
        self.assertContains(response, "Hapus pencarian")
        self.assertNotContains(response, "Local market opens")

    @patch("news.views.fetch_fashion_articles")
    def test_empty_query_displays_all_articles_and_top_story_controls(
        self, fetch_articles
    ):
        fetch_articles.return_value = [
            {
                "title": f"Fashion article {number}",
                "url": f"https://example.com/{number}",
                "source": {"name": "Style Daily"},
            }
            for number in range(1, 6)
        ]

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["articles"]), 5)
        self.assertContains(response, "Fashion article 1")
        self.assertContains(response, "Fashion article 5")
        self.assertContains(response, "Anda akan membuka website lain")
        self.assertContains(response, "news-article-link")
        self.assertContains(response, "news-warning-continue")
        self.assertContains(response, "Berita Lainnya")

    @patch("news.views.fetch_fashion_articles")
    def test_search_with_no_match_shows_empty_state(self, fetch_articles):
        fetch_articles.return_value = [{"title": "Vintage denim returns"}]

        response = self.client.get(self.url, {"q": "shoes"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tidak ada berita yang cocok")

    @patch("news.views.fetch_fashion_articles")
    def test_empty_api_results_show_default_empty_state(self, fetch_articles):
        fetch_articles.return_value = []

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belum ada artikel fashion")

    @patch(
        "news.views.fetch_fashion_articles",
        side_effect=NewsAPIError("offline"),
    )
    def test_api_error_displays_friendly_error(self, fetch_articles):
        with self.assertLogs("news.views", level="ERROR"):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Berita fashion tidak tersedia saat ini",
        )
        self.assertEqual(response.context["articles"], [])
        self.assertEqual(
            response.context["error_message"],
            "Berita fashion tidak tersedia saat ini. Silakan coba lagi nanti.",
        )


class FetchFashionArticlesTests(TestCase):
    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_fetches_articles_with_api_request_parameters(self, get_request):
        articles = [
            {"title": "New clothing trends"},
            {"title": "Tren pakaian terbaru"},
        ]
        get_request.return_value.json.return_value = {
            "status": "ok",
            "articles": articles,
        }

        result = fetch_fashion_articles()

        self.assertEqual(result, articles)
        get_request.assert_called_once_with(
            NEWS_API_URL,
            headers={"X-Api-Key": "test-api-key"},
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

    @override_settings(NEWS_API_KEY="")
    def test_missing_api_key_raises_news_api_error_without_request(self):
        with patch("news.models.requests.get") as get_request:
            with self.assertRaisesMessage(
                NewsAPIError,
                "NEWS_API_KEY is not configured.",
            ):
                fetch_fashion_articles()

        get_request.assert_not_called()

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch(
        "news.models.requests.get",
        side_effect=requests.Timeout("request timed out"),
    )
    def test_request_exception_is_wrapped(self, get_request):
        with self.assertRaisesMessage(
            NewsAPIError,
            "Could not reach NewsAPI.",
        ) as raised:
            fetch_fashion_articles()

        self.assertIsInstance(raised.exception.__cause__, requests.Timeout)

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_http_error_is_wrapped(self, get_request):
        get_request.return_value.raise_for_status.side_effect = (
            requests.HTTPError("bad response")
        )

        with self.assertRaisesMessage(
            NewsAPIError,
            "Could not reach NewsAPI.",
        ) as raised:
            fetch_fashion_articles()

        self.assertIsInstance(raised.exception.__cause__, requests.HTTPError)

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_invalid_json_is_wrapped(self, get_request):
        get_request.return_value.json.side_effect = ValueError("invalid json")

        with self.assertRaisesMessage(
            NewsAPIError,
            "NewsAPI returned an invalid response.",
        ) as raised:
            fetch_fashion_articles()

        self.assertIsInstance(raised.exception.__cause__, ValueError)

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_non_object_response_is_rejected(self, get_request):
        get_request.return_value.json.return_value = ["not", "an", "object"]

        with self.assertRaisesMessage(
            NewsAPIError,
            "NewsAPI returned an unexpected response.",
        ):
            fetch_fashion_articles()

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_api_error_message_is_propagated(self, get_request):
        get_request.return_value.json.return_value = {
            "status": "error",
            "message": "API quota exceeded",
        }

        with self.assertRaisesMessage(NewsAPIError, "API quota exceeded"):
            fetch_fashion_articles()

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_api_error_without_message_uses_fallback(self, get_request):
        get_request.return_value.json.return_value = {"status": "error"}

        with self.assertRaisesMessage(
            NewsAPIError,
            "NewsAPI returned an error.",
        ):
            fetch_fashion_articles()

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_non_list_articles_are_rejected(self, get_request):
        get_request.return_value.json.return_value = {
            "status": "ok",
            "articles": {},
        }

        with self.assertRaisesMessage(
            NewsAPIError,
            "NewsAPI returned an invalid articles list.",
        ):
            fetch_fashion_articles()

    @override_settings(NEWS_API_KEY="test-api-key")
    @patch("news.models.requests.get")
    def test_missing_articles_field_defaults_to_empty_list(self, get_request):
        get_request.return_value.json.return_value = {"status": "ok"}

        self.assertEqual(fetch_fashion_articles(), [])
