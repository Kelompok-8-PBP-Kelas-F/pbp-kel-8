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
        self.assertContains(response, 'data-open-forum-create')
        self.assertContains(response, "Tag")

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
                "image_url": "",
            },
        )

        self.assertRedirects(response, reverse("forum:forum_main"))
        post = Forum.objects.get()
        self.assertEqual(post.title, "Tips thrifting")
        self.assertEqual(post.author_username, self.user.username)
