from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Forum


class ForumCreateModalTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="forum-member",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_forum_main_renders_create_modal(self):
        response = self.client.get(reverse("forum:forum_main"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="forum-create-modal"')
        self.assertContains(response, 'popovertarget="forum-create-modal"')
        self.assertContains(response, "Tag")
        self.assertContains(response, 'id="title-char-counter"')
        self.assertContains(response, 'id="content-char-counter"')
        self.assertContains(response, 'id="form-image-preview-container"')
        self.assertContains(response, 'id="sidebar-image-preview-container"')
        self.assertContains(response, 'id="preview-post-title"')
        self.assertContains(response, 'id="preview-post-content"')

    def test_invalid_post_rerenders_modal_with_errors(self):
        response = self.client.post(
            reverse("forum:forum_main"),
            {"title": "", "content": "", "category": "DISCUSSION"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="forum-create-modal"')
        self.assertContains(response, "This field is required.")
        self.assertTrue(response.context["show_create_modal"])
        self.assertEqual(Forum.objects.count(), 0)

    def test_valid_post_creates_forum_post(self):
        response = self.client.post(
            reverse("forum:forum_main"),
            {
                "title": "Tips thrifting",
                "content": "Bagikan tips memilih pakaian vintage.",
                "category": "DISCUSSION",
                "image_url": "https://example.com/jacket.jpg",
                "image_caption": "Foto jaket denim",
            },
        )

        self.assertRedirects(response, reverse("forum:forum_main"))
        post = Forum.objects.get()
        self.assertEqual(post.title, "Tips thrifting")
        self.assertEqual(post.author_username, self.user.username)
        self.assertEqual(post.image_caption, "Foto jaket denim")

    def test_posts_api_returns_json(self):
        Forum.objects.create(
            author_username=self.user.username,
            title="Forum API",
            content="Post dari endpoint API.",
        )

        response = self.client.get(reverse("forum:get_posts_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["title"], "Forum API")
        self.assertEqual(response.json()[0]["category"], "Discussion")

    def test_create_api_returns_json_and_saves_post(self):
        response = self.client.post(
            reverse("forum:create_post_api"),
            {
                "title": "Post via API",
                "content": "Isi post dari JavaScript.",
                "category": "QUESTION",
                "image_url": "",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["post"]["category"], "Question")
        self.assertEqual(Forum.objects.get().author_username, self.user.username)

    def test_create_api_returns_json_validation_errors(self):
        response = self.client.post(
            reverse("forum:create_post_api"),
            {"title": "", "content": "", "category": "INVALID"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertEqual(Forum.objects.count(), 0)
