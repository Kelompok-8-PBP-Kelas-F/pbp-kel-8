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
        self.assertContains(response, 'id="forum-search-button"')
        self.assertContains(response, 'id="forum-search-input"')
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

    def test_posts_api_filter_by_title(self):
        Forum.objects.create(author_username="user1", title="Jaket Vintage Denim", content="Konten 1", category="OOTD")
        Forum.objects.create(author_username="user2", title="Sepatu Kulit Murah", content="Konten 2", category="DISCUSSION")

        # Match "Vintage" with title param
        res = self.client.get(reverse("forum:get_posts_api"), {"title": "vintage"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["title"], "Jaket Vintage Denim")

        # Match "Kulit" with q param
        res = self.client.get(reverse("forum:get_posts_api"), {"q": "KULIT"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["title"], "Sepatu Kulit Murah")

        # Match author username with @
        res = self.client.get(reverse("forum:get_posts_api"), {"q": "@user1"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["title"], "Jaket Vintage Denim")

        # No match
        res = self.client.get(reverse("forum:get_posts_api"), {"title": "tidak ada"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 0)

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

    def test_create_api_requires_authentication(self):
        self.client.logout()
        response = self.client.post(
            reverse("forum:create_post_api"),
            {
                "title": "Post by Guest",
                "content": "Should be rejected.",
                "category": "QUESTION",
            },
        )
        self.assertEqual(response.status_code, 401)
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
        self.assertTrue(response.context["can_manage"])
        self.assertContains(response, "Post Detail")
        self.assertContains(response, "Konten Detail")
        self.assertContains(response, "Kembali ke Forum")
        self.assertContains(response, 'id="tulis-komentar"')
        self.assertContains(response, 'id="comments-heading"')
        self.assertContains(response, 'id="menu-edit-post-btn"')
        self.assertContains(response, 'id="menu-delete-post-btn"')
        self.assertContains(response, 'id="forum-edit-modal"')

    def test_forum_detail_view_non_owner_and_guest(self):
        post = Forum.objects.create(
            author_username="another-author",
            title="Post By Other",
            content="Konten Lain",
        )
        # Logged in as non-owner (self.user)
        response = self.client.get(reverse("forum:forum_detail", args=[post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_manage"])
        self.assertNotContains(response, 'id="menu-edit-post-btn"')
        self.assertNotContains(response, 'id="menu-delete-post-btn"')
        self.assertNotContains(response, 'id="forum-edit-modal"')

        # Guest (unauthenticated)
        self.client.logout()
        res_guest = self.client.get(reverse("forum:forum_detail", args=[post.id]))
        self.assertEqual(res_guest.status_code, 200)
        self.assertFalse(res_guest.context["can_manage"])
        self.assertNotContains(res_guest, 'id="menu-edit-post-btn"')
        self.assertNotContains(res_guest, 'id="menu-delete-post-btn"')

    def test_forum_detail_view_superuser(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin-user",
            password="admin-password",
        )
        self.client.force_login(admin_user)
        post = Forum.objects.create(
            author_username="some-user",
            title="Admin Viewing",
            content="Content",
        )
        response = self.client.get(reverse("forum:forum_detail", args=[post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_manage"])
        self.assertContains(response, 'id="menu-edit-post-btn"')
        self.assertContains(response, 'id="menu-delete-post-btn"')

    def test_edit_post_api_authorization(self):
        from urllib.parse import urlencode

        post = Forum.objects.create(
            author_username="original-owner",
            title="Old Title",
            content="Old Content",
        )

        # 1. Unauthenticated -> 401
        self.client.logout()
        res_unauth = self.client.put(
            reverse("forum:edit_post_api", args=[post.id]),
            data=urlencode({"title": "Hack Title", "content": "Hack Content", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(res_unauth.status_code, 401)

        # 2. Authenticated as non-owner (self.user) -> 403
        self.client.force_login(self.user)
        res_forbidden = self.client.put(
            reverse("forum:edit_post_api", args=[post.id]),
            data=urlencode({"title": "Other User Title", "content": "Other User Content", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(res_forbidden.status_code, 403)

        # 3. Authenticated as owner -> 200
        owner_user = get_user_model().objects.create_user(
            username="original-owner",
            password="owner-password",
        )
        self.client.force_login(owner_user)
        res_owner = self.client.put(
            reverse("forum:edit_post_api", args=[post.id]),
            data=urlencode({"title": "Owner Updated Title", "content": "Updated Content", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(res_owner.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, "Owner Updated Title")

        # 4. Superuser -> 200 (can edit any post)
        admin_user = get_user_model().objects.create_superuser(
            username="super-admin",
            password="admin-password",
        )
        self.client.force_login(admin_user)
        res_admin = self.client.put(
            reverse("forum:edit_post_api", args=[post.id]),
            data=urlencode({"title": "Superuser Overwrite", "content": "Admin Content", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(res_admin.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, "Superuser Overwrite")

    def test_delete_post_api_authorization(self):
        post = Forum.objects.create(
            author_username="post-owner",
            title="To Delete",
            content="Content",
        )

        # 1. Unauthenticated -> 401
        self.client.logout()
        res_unauth = self.client.delete(reverse("forum:delete_post_api", args=[post.id]))
        self.assertEqual(res_unauth.status_code, 401)
        self.assertTrue(Forum.objects.filter(pk=post.id).exists())

        # 2. Authenticated as non-owner (self.user) -> 403
        self.client.force_login(self.user)
        res_forbidden = self.client.delete(reverse("forum:delete_post_api", args=[post.id]))
        self.assertEqual(res_forbidden.status_code, 403)
        self.assertTrue(Forum.objects.filter(pk=post.id).exists())

        # 3. Authenticated as owner -> 200
        owner_user = get_user_model().objects.create_user(
            username="post-owner",
            password="owner-password",
        )
        self.client.force_login(owner_user)
        res_owner = self.client.delete(reverse("forum:delete_post_api", args=[post.id]))
        self.assertEqual(res_owner.status_code, 200)
        self.assertFalse(Forum.objects.filter(pk=post.id).exists())

        # 4. Superuser can delete any post -> 200
        another_post = Forum.objects.create(
            author_username="someone-else",
            title="Post for Superuser to Delete",
            content="Content",
        )
        admin_user = get_user_model().objects.create_superuser(
            username="super-admin-deleter",
            password="admin-password",
        )
        self.client.force_login(admin_user)
        res_admin = self.client.delete(reverse("forum:delete_post_api", args=[another_post.id]))
        self.assertEqual(res_admin.status_code, 200)
        self.assertFalse(Forum.objects.filter(pk=another_post.id).exists())

    def test_like_api_requires_authentication(self):
        post = Forum.objects.create(
            author_username="someone",
            title="Post to Like",
            content="Content",
        )
        self.client.logout()
        response = self.client.post(reverse("forum:like_post_api", args=[post.id]))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "Authentication required. Silakan masuk terlebih dahulu.")
        post.refresh_from_db()
        self.assertEqual(post.total_likes, 0)

    def test_like_api_toggle_and_total_likes(self):
        post = Forum.objects.create(
            author_username="author-1",
            title="Post for Like Toggle",
            content="Content for like toggle",
        )
        self.client.force_login(self.user)

        # 1. First like -> liked=True, total_likes=1
        res1 = self.client.post(reverse("forum:like_post_api", args=[post.id]))
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json()["liked"])
        self.assertEqual(res1.json()["total_likes"], 1)
        post.refresh_from_db()
        self.assertEqual(post.total_likes, 1)
        self.assertTrue(post.liked_by.filter(pk=self.user.pk).exists())

        # 2. Second like (unlike) -> liked=False, total_likes=0
        res2 = self.client.post(reverse("forum:like_post_api", args=[post.id]))
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(res2.json()["liked"])
        self.assertEqual(res2.json()["total_likes"], 0)
        post.refresh_from_db()
        self.assertEqual(post.total_likes, 0)
        self.assertFalse(post.liked_by.filter(pk=self.user.pk).exists())

    def test_like_api_multiple_users(self):
        post = Forum.objects.create(
            author_username="author-1",
            title="Multi-user Like",
            content="Testing multi-user likes",
        )
        user2 = get_user_model().objects.create_user(
            username="second-user",
            password="test-password-2",
        )

        # User 1 likes
        self.client.force_login(self.user)
        res1 = self.client.post(reverse("forum:like_post_api", args=[post.id]))
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["total_likes"], 1)

        # User 2 likes
        self.client.force_login(user2)
        res2 = self.client.post(reverse("forum:like_post_api", args=[post.id]))
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["total_likes"], 2)

        post.refresh_from_db()
        self.assertEqual(post.total_likes, 2)
        self.assertEqual(post.liked_by.count(), 2)

    def test_like_api_invalid_method(self):
        post = Forum.objects.create(
            author_username="someone",
            title="Invalid Method Post",
            content="Content",
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("forum:like_post_api", args=[post.id]))
        self.assertEqual(response.status_code, 405)

    def test_like_api_not_found(self):
        import uuid
        self.client.force_login(self.user)
        random_id = uuid.uuid4()
        response = self.client.post(reverse("forum:like_post_api", args=[random_id]))
        self.assertEqual(response.status_code, 404)

    def test_posts_api_includes_is_liked_flag(self):
        post1 = Forum.objects.create(
            author_username="user1",
            title="Liked Post",
            content="Content 1",
        )
        post2 = Forum.objects.create(
            author_username="user2",
            title="Unliked Post",
            content="Content 2",
        )
        post1.liked_by.add(self.user)
        post1.total_likes = 1
        post1.save()

        # When logged in as self.user
        self.client.force_login(self.user)
        res = self.client.get(reverse("forum:get_posts_api"))
        self.assertEqual(res.status_code, 200)
        posts_data = {p["title"]: p for p in res.json()}
        self.assertTrue(posts_data["Liked Post"]["is_liked"])
        self.assertFalse(posts_data["Unliked Post"]["is_liked"])

        # When guest
        self.client.logout()
        res_guest = self.client.get(reverse("forum:get_posts_api"))
        self.assertEqual(res_guest.status_code, 200)
        for p in res_guest.json():
            self.assertFalse(p["is_liked"])

    def test_forum_main_sort_buttons_no_diikuti(self):
        response = self.client.get(reverse("forum:forum_main"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="sort-terbaru-btn"')
        self.assertContains(response, 'id="sort-trending-btn"')
        self.assertNotContains(response, "Diikuti")

    def test_posts_api_sort_by_latest_and_trending(self):
        import time
        from django.utils import timezone
        from datetime import timedelta

        # Create older post with more likes
        post_older = Forum.objects.create(
            author_username="user1",
            title="Older Trending Post",
            content="Content",
            total_likes=10,
        )
        # Manually backdate created_at
        Forum.objects.filter(pk=post_older.pk).update(created_at=timezone.now() - timedelta(days=2))

        # Create newer post with fewer likes
        post_newer = Forum.objects.create(
            author_username="user2",
            title="Newer Post",
            content="Content",
            total_likes=1,
        )

        # 1. Sort by latest -> newer post first
        res_latest = self.client.get(reverse("forum:get_posts_api"), {"sort": "latest"})
        self.assertEqual(res_latest.status_code, 200)
        json_latest = res_latest.json()
        self.assertEqual(json_latest[0]["title"], "Newer Post")
        self.assertEqual(json_latest[1]["title"], "Older Trending Post")

        # 2. Sort by trending -> post with more likes first
        res_trending = self.client.get(reverse("forum:get_posts_api"), {"sort": "trending"})
        self.assertEqual(res_trending.status_code, 200)
        json_trending = res_trending.json()
        self.assertEqual(json_trending[0]["title"], "Older Trending Post")
        self.assertEqual(json_trending[1]["title"], "Newer Post")


