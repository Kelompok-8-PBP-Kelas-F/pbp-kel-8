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



    def test_posts_api_returns_json(self):
        post = Forum.objects.create(
            author_username=self.user.username,
            title="Forum API",
            content="Post dari endpoint API.",
        )

        response = self.client.get(reverse("forum:get_posts_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["title"], "Forum API")
        self.assertEqual(response.json()[0]["category"], "Discussion")
        self.assertEqual(response.json()[0]["detail_url"], reverse("forum:forum_detail", args=[post.id]))

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

    def test_forum_detail_view(self):
        post = Forum.objects.create(
            author_username=self.user.username,
            title="Post Detail",
            content="Konten Detail",
        )
        response = self.client.get(reverse("forum:forum_detail", args=[post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post"], post)
        self.assertContains(response, "Post Detail")
        self.assertContains(response, "Konten Detail")
        self.assertContains(response, "Kembali ke Forum")
        self.assertContains(response, 'id="tulis-komentar"')
        self.assertContains(response, 'id="comments-heading"')
        self.assertContains(response, 'id="menu-edit-post-btn"')
        self.assertContains(response, 'id="menu-delete-post-btn"')
        self.assertContains(response, 'id="forum-edit-modal"')

    def test_edit_post_api_put(self):
        from urllib.parse import urlencode
        post = Forum.objects.create(
            author_username="someone",
            title="Old Title",
            content="Old Content",
        )
        self.client.logout()  # Unauthenticated to verify no auth check
        response = self.client.put(
            reverse("forum:edit_post_api", args=[post.id]),
            data=urlencode({"title": "Updated Title", "content": "Updated Content", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, "Updated Title")

    def test_delete_post_api_delete(self):
        post = Forum.objects.create(
            author_username="someone",
            title="To Delete",
            content="Content",
        )
        self.client.logout()  # Unauthenticated to verify no auth check
        response = self.client.delete(reverse("forum:delete_post_api", args=[post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Forum.objects.filter(pk=post.id).exists())
