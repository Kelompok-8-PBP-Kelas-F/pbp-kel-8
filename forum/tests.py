import json
import uuid
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from .forms import CommentForm, ForumForm
from .models import Comment, Forum
from .views import (
    add_comment_api,
    create_post_api,
    delete_comment_api,
    delete_post_api,
    edit_post_api,
    forum_detail,
    forum_main,
    get_comments_api,
    get_posts_api,
    like_post_api,
    serialize_comment,
    serialize_post,
)

User = get_user_model()


class ForumModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="model_user",
            password="password123",
        )
        self.forum = Forum.objects.create(
            author_username=self.user.username,
            title="Judul Forum Model",
            content="Konten diskusi untuk pengetesan model.",
            category="DISCUSSION",
        )

    def test_forum_creation_and_defaults(self):
        self.assertIsInstance(self.forum.id, uuid.UUID)
        self.assertEqual(self.forum.title, "Judul Forum Model")
        self.assertEqual(self.forum.category, "DISCUSSION")
        self.assertEqual(self.forum.total_likes, 0)
        self.assertEqual(self.forum.total_comments, 0)
        self.assertEqual(self.forum.image_count, 0)
        self.assertIsNone(self.forum.image_url)
        self.assertIsNone(self.forum.image_caption)
        self.assertIsNotNone(self.forum.created_at)
        self.assertIsNotNone(self.forum.updated_at)

    def test_forum_str_representation(self):
        self.assertEqual(str(self.forum), "Judul Forum Model")

    def test_forum_category_choices(self):
        categories = ["DISCUSSION", "QUESTION", "OOTD", "INSPO"]
        for cat in categories:
            post = Forum.objects.create(
                author_username=self.user.username,
                title=f"Post {cat}",
                content="Konten kategori",
                category=cat,
            )
            self.assertEqual(post.category, cat)

    def test_forum_is_liked_by(self):
        # Anonymous or None user
        self.assertFalse(self.forum.is_liked_by(None))
        self.assertFalse(self.forum.is_liked_by(AnonymousUser()))

        # Authenticated user who has not liked yet
        self.assertFalse(self.forum.is_liked_by(self.user))

        # Authenticated user who liked
        self.forum.liked_by.add(self.user)
        self.assertTrue(self.forum.is_liked_by(self.user))

        # After removing user
        self.forum.liked_by.remove(self.user)
        self.assertFalse(self.forum.is_liked_by(self.user))

    def test_forum_cascade_deletes_comments(self):
        Comment.objects.create(
            forum=self.forum,
            user=self.user,
            author_username=self.user.username,
            content="Komentar yang akan terhapus cascade",
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.forum.delete()
        self.assertEqual(Comment.objects.count(), 0)


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="comment_user",
            password="password123",
        )
        self.forum = Forum.objects.create(
            author_username="forum_author",
            title="Forum untuk Komentar",
            content="Isi forum",
        )

    def test_comment_creation_and_str(self):
        comment = Comment.objects.create(
            forum=self.forum,
            user=self.user,
            author_username=self.user.username,
            content="Komentar pengetesan",
        )
        self.assertIsInstance(comment.id, uuid.UUID)
        self.assertEqual(comment.forum, self.forum)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(
            str(comment),
            f"Komentar oleh @{self.user.username} di {self.forum.title}",
        )

    def test_comment_ordering(self):
        comment1 = Comment.objects.create(
            forum=self.forum,
            user=self.user,
            author_username=self.user.username,
            content="Komentar 1",
        )
        comment2 = Comment.objects.create(
            forum=self.forum,
            user=self.user,
            author_username=self.user.username,
            content="Komentar 2",
        )
        comments = list(Comment.objects.filter(forum=self.forum))
        self.assertEqual(comments, [comment1, comment2])

    def test_comment_nullable_user(self):
        comment = Comment.objects.create(
            forum=self.forum,
            user=None,
            author_username="anonymous_handle",
            content="Komentar tanpa akun terikat",
        )
        self.assertIsNone(comment.user)
        self.assertEqual(comment.author_username, "anonymous_handle")

    def test_comment_cascade_on_user_delete(self):
        Comment.objects.create(
            forum=self.forum,
            user=self.user,
            author_username=self.user.username,
            content="Komentar terkait user",
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.user.delete()
        self.assertEqual(Comment.objects.count(), 0)


class ForumFormTests(TestCase):
    def test_forum_form_valid_data(self):
        data = {
            "title": "Tips Memilih Pakaian Vintage",
            "content": "Pastikan memeriksa jahitan dan bahan pakaian secara detail.",
            "category": "DISCUSSION",
            "image_url": "https://images.unsplash.com/photo-1",
            "image_caption": "Foto jaket vintage",
        }
        form = ForumForm(data=data)
        self.assertTrue(form.is_valid())

    def test_forum_form_all_category_choices(self):
        for choice in ["DISCUSSION", "QUESTION", "OOTD", "INSPO"]:
            form = ForumForm(
                data={
                    "title": "Judul Kategori",
                    "content": "Konten valid",
                    "category": choice,
                }
            )
            self.assertTrue(form.is_valid())

    def test_forum_form_invalid_category(self):
        form = ForumForm(
            data={
                "title": "Judul",
                "content": "Konten",
                "category": "INVALID_TAG",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)

    def test_forum_form_invalid_image_url(self):
        form = ForumForm(
            data={
                "title": "Judul",
                "content": "Konten",
                "category": "OOTD",
                "image_url": "bukan-sebuah-url",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("image_url", form.errors)

    def test_forum_form_missing_required_fields(self):
        form = ForumForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("content", form.errors)

    def test_forum_form_optional_fields(self):
        form = ForumForm(
            data={
                "title": "Hanya Judul dan Konten",
                "content": "Isi tanpa gambar.",
                "category": "DISCUSSION",
            }
        )
        self.assertTrue(form.is_valid())
        post = form.save(commit=False)
        self.assertIn(post.image_url, ("", None))
        self.assertIn(post.image_caption, ("", None))

    def test_forum_form_xss_escaping(self):
        form = ForumForm(
            data={
                "title": "<script>alert('XSS Title')</script>",
                "content": "<p>Konten <b>berbahaya</b></p>",
                "category": "DISCUSSION",
                "image_caption": "<i>Caption</i>",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["title"], "&lt;script&gt;alert(&#x27;XSS Title&#x27;)&lt;/script&gt;")
        self.assertEqual(form.cleaned_data["content"], "&lt;p&gt;Konten &lt;b&gt;berbahaya&lt;/b&gt;&lt;/p&gt;")
        self.assertEqual(form.cleaned_data["image_caption"], "&lt;i&gt;Caption&lt;/i&gt;")


class CommentFormTests(TestCase):
    def test_comment_form_valid_data(self):
        form = CommentForm(data={"content": "Komentar yang valid dan membangun."})
        self.assertTrue(form.is_valid())

    def test_comment_form_xss_escaping(self):
        form = CommentForm(data={"content": "<script>alert('XSS Comment')</script>"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["content"], "&lt;script&gt;alert(&#x27;XSS Comment&#x27;)&lt;/script&gt;")

    def test_comment_form_empty_content(self):
        form = CommentForm(data={"content": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_comment_form_widget_attributes(self):
        form = CommentForm()
        widget = form.fields["content"].widget
        self.assertEqual(widget.attrs.get("id"), "comment-textarea")
        self.assertEqual(widget.attrs.get("maxlength"), 2000)
        self.assertEqual(widget.attrs.get("rows"), 3)


class ForumSerializationTests(TestCase):
    def setUp(self):
        self.post_author = User.objects.create_user(
            username="post_author",
            password="password123",
        )
        self.comment_author = User.objects.create_user(
            username="comment_author",
            password="password123",
        )
        self.admin_user = User.objects.create_superuser(
            username="super_user",
            password="password123",
        )
        self.stranger_user = User.objects.create_user(
            username="stranger",
            password="password123",
        )
        self.post = Forum.objects.create(
            author_username=self.post_author.username,
            title="Judul Serialisasi",
            content="Konten serialisasi",
            category="OOTD",
            image_url="https://example.com/img.jpg",
            image_caption="Caption gambar",
            image_count=1,
            total_likes=5,
            total_comments=2,
        )
        self.comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar serialisasi",
        )

    def test_serialize_post_fields(self):
        data = serialize_post(self.post, is_liked=True)
        self.assertEqual(data["id"], str(self.post.id))
        self.assertEqual(data["detail_url"], reverse("forum:forum_detail", kwargs={"id": self.post.id}))
        self.assertEqual(data["author_username"], "post_author")
        self.assertEqual(data["title"], "Judul Serialisasi")
        self.assertEqual(data["content"], "Konten serialisasi")
        self.assertEqual(data["category"], "OOTD")
        self.assertEqual(data["image_url"], "https://example.com/img.jpg")
        self.assertEqual(data["image_caption"], "Caption gambar")
        self.assertEqual(data["image_count"], 1)
        self.assertEqual(data["total_likes"], 5)
        self.assertEqual(data["total_comments"], 2)
        self.assertTrue(data["is_liked"])

    def test_serialize_comment_permissions(self):
        # 1. Anonymous or None user
        data_none = serialize_comment(self.comment, None)
        self.assertFalse(data_none["can_delete"])
        data_anon = serialize_comment(self.comment, AnonymousUser())
        self.assertFalse(data_anon["can_delete"])

        # 2. Comment author can delete
        data_comment_author = serialize_comment(self.comment, self.comment_author)
        self.assertTrue(data_comment_author["can_delete"])
        self.assertFalse(data_comment_author["is_post_author"])

        # 3. Post author can delete comment on their post (moderation)
        data_post_author = serialize_comment(self.comment, self.post_author)
        self.assertTrue(data_post_author["can_delete"])

        # 4. Superuser can delete
        data_super = serialize_comment(self.comment, self.admin_user)
        self.assertTrue(data_super["can_delete"])

        # 5. Stranger cannot delete
        data_stranger = serialize_comment(self.comment, self.stranger_user)
        self.assertFalse(data_stranger["can_delete"])

    def test_serialize_comment_is_post_author_flag(self):
        # Comment made by the post's author
        post_author_comment = Comment.objects.create(
            forum=self.post,
            user=self.post_author,
            author_username=self.post_author.username,
            content="Komentar dari pembuat post",
        )
        data = serialize_comment(post_author_comment, self.post_author)
        self.assertTrue(data["is_post_author"])
        self.assertTrue(data["can_delete"])


class ForumViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="viewer_user",
            password="password123",
        )
        self.post = Forum.objects.create(
            author_username=self.user.username,
            title="Post untuk View Detail",
            content="Konten view detail",
        )

    def test_forum_main_renders_template_and_form(self):
        response = self.client.get(reverse("forum:forum_main"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/forum/forum_main.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], ForumForm)

    def test_forum_main_renders_ui_elements(self):
        response = self.client.get(reverse("forum:forum_main"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="forum-create-modal"')
        self.assertContains(response, 'popovertarget="forum-create-modal"')
        self.assertContains(response, 'id="forum-search-button"')
        self.assertContains(response, 'id="forum-search-input"')
        self.assertContains(response, 'id="sort-terbaru-btn"')
        self.assertContains(response, 'id="sort-trending-btn"')

    def test_forum_detail_view_authenticated_author(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("forum:forum_detail", args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/forum/forum_detail.html")
        self.assertEqual(response.context["post"], self.post)
        self.assertTrue(response.context["can_manage"])
        self.assertFalse(response.context["is_liked"])
        self.assertIn("comment_form", response.context)
        self.assertContains(response, "Post untuk View Detail")
        self.assertContains(response, 'id="menu-edit-post-btn"')
        self.assertContains(response, 'id="menu-delete-post-btn"')
        self.assertContains(response, 'id="forum-edit-modal"')

    def test_forum_detail_view_guest_and_non_author(self):
        # Guest
        response_guest = self.client.get(reverse("forum:forum_detail", args=[self.post.id]))
        self.assertEqual(response_guest.status_code, 200)
        self.assertFalse(response_guest.context["can_manage"])
        self.assertNotContains(response_guest, 'id="menu-edit-post-btn"')
        self.assertNotContains(response_guest, 'id="menu-delete-post-btn"')

        # Other authenticated user
        other_user = User.objects.create_user(username="other_viewer", password="password123")
        self.client.force_login(other_user)
        response_other = self.client.get(reverse("forum:forum_detail", args=[self.post.id]))
        self.assertEqual(response_other.status_code, 200)
        self.assertFalse(response_other.context["can_manage"])
        self.assertNotContains(response_other, 'id="menu-edit-post-btn"')

    def test_forum_detail_view_superuser(self):
        admin = User.objects.create_superuser(username="admin_viewer", password="password123")
        self.client.force_login(admin)
        response = self.client.get(reverse("forum:forum_detail", args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_manage"])
        self.assertContains(response, 'id="menu-edit-post-btn"')
        self.assertContains(response, 'id="menu-delete-post-btn"')

    def test_forum_detail_view_not_found(self):
        random_uuid = uuid.uuid4()
        response = self.client.get(reverse("forum:forum_detail", args=[random_uuid]))
        self.assertEqual(response.status_code, 404)


class ForumGetPostsAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api_user",
            password="password123",
        )
        self.post1 = Forum.objects.create(
            author_username="denim_lover",
            title="Jaket Denim Klasik",
            content="Koleksi vintage 90-an.",
            category="OOTD",
            total_likes=10,
        )
        self.post2 = Forum.objects.create(
            author_username="leather_guru",
            title="Sepatu Kulit Oxford",
            content="Panduan merawat sepatu kulit asli.",
            category="DISCUSSION",
            total_likes=25,
        )

    def test_get_posts_api_returns_all_posts(self):
        response = self.client.get(reverse("forum:get_posts_api"))
        self.assertEqual(response.status_code, 200)
        posts_data = response.json()
        self.assertEqual(len(posts_data), 2)

    def test_get_posts_api_filter_by_title_param(self):
        response = self.client.get(reverse("forum:get_posts_api"), {"title": "denim"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Jaket Denim Klasik")

    def test_get_posts_api_filter_by_q_param(self):
        # Match title
        res_q1 = self.client.get(reverse("forum:get_posts_api"), {"q": "Sepatu"})
        self.assertEqual(len(res_q1.json()), 1)
        self.assertEqual(res_q1.json()[0]["title"], "Sepatu Kulit Oxford")

        # Match category
        res_q2 = self.client.get(reverse("forum:get_posts_api"), {"q": "OOTD"})
        self.assertEqual(len(res_q2.json()), 1)
        self.assertEqual(res_q2.json()[0]["title"], "Jaket Denim Klasik")

        # Match author with '@'
        res_q3 = self.client.get(reverse("forum:get_posts_api"), {"q": "@leather_guru"})
        self.assertEqual(len(res_q3.json()), 1)
        self.assertEqual(res_q3.json()[0]["title"], "Sepatu Kulit Oxford")

        # No match
        res_q4 = self.client.get(reverse("forum:get_posts_api"), {"q": "TidakAdaKecocokan"})
        self.assertEqual(len(res_q4.json()), 0)

    def test_get_posts_api_sort_latest_and_trending(self):
        # Manually backdate post2 to be older than post1
        Forum.objects.filter(pk=self.post2.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )

        # 1. Sort latest: newest created_at first (post1)
        res_latest = self.client.get(reverse("forum:get_posts_api"), {"sort": "latest"})
        self.assertEqual(res_latest.status_code, 200)
        self.assertEqual(res_latest.json()[0]["title"], "Jaket Denim Klasik")

        # 2. Sort trending: highest total_likes first (post2 with 25 likes)
        res_trending = self.client.get(reverse("forum:get_posts_api"), {"sort": "trending"})
        self.assertEqual(res_trending.status_code, 200)
        self.assertEqual(res_trending.json()[0]["title"], "Sepatu Kulit Oxford")

        # 3. Sort popular: alias for trending
        res_popular = self.client.get(reverse("forum:get_posts_api"), {"sort": "popular"})
        self.assertEqual(res_popular.status_code, 200)
        self.assertEqual(res_popular.json()[0]["title"], "Sepatu Kulit Oxford")

    def test_get_posts_api_is_liked_flag(self):
        self.post1.liked_by.add(self.user)

        # Logged in: post1 has is_liked=True, post2 has is_liked=False
        self.client.force_login(self.user)
        res_auth = self.client.get(reverse("forum:get_posts_api"))
        data = {p["title"]: p["is_liked"] for p in res_auth.json()}
        self.assertTrue(data["Jaket Denim Klasik"])
        self.assertFalse(data["Sepatu Kulit Oxford"])

        # Guest: all is_liked are False
        self.client.logout()
        res_guest = self.client.get(reverse("forum:get_posts_api"))
        for p in res_guest.json():
            self.assertFalse(p["is_liked"])

    def test_get_posts_api_invalid_method(self):
        response = self.client.post(reverse("forum:get_posts_api"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["error"], "Invalid request method")


class ForumCreatePostAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="author_creator",
            password="password123",
        )
        self.url = reverse("forum:create_post_api")

    def test_create_post_api_success(self):
        self.client.force_login(self.user)
        payload = {
            "title": "Post Baru via API",
            "content": "Konten diskusi lengkap melalui AJAX/fetch.",
            "category": "QUESTION",
            "image_url": "https://example.com/item.png",
            "image_caption": "Caption gambar item",
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["message"], "Post created successfully")
        self.assertEqual(data["post"]["title"], "Post Baru via API")
        self.assertEqual(data["post"]["author_username"], self.user.username)
        self.assertEqual(data["post"]["category"], "Question")

        # Verify database record
        post = Forum.objects.get(pk=data["post"]["id"])
        self.assertEqual(post.author_username, self.user.username)
        self.assertEqual(post.title, "Post Baru via API")

    def test_create_post_api_unauthenticated(self):
        response = self.client.post(
            self.url,
            {"title": "Judul Anonim", "content": "Konten", "category": "DISCUSSION"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Forum.objects.count(), 0)

    def test_create_post_api_validation_errors(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {"title": "", "content": "", "category": "INVALID_CAT"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertEqual(Forum.objects.count(), 0)

    def test_create_post_api_invalid_method(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_create_post_api_escapes_xss_tags(self):
        self.client.force_login(self.user)
        payload = {
            "title": "<script>alert('xss')</script>",
            "content": "<h1>Test Header</h1>",
            "category": "DISCUSSION",
        }
        res = self.client.post(self.url, data=payload)
        self.assertEqual(res.status_code, 201)
        post = Forum.objects.get(pk=res.json()["post"]["id"])
        self.assertEqual(post.title, "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;")
        self.assertEqual(post.content, "&lt;h1&gt;Test Header&lt;/h1&gt;")


class ForumEditPostAPITests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="original_author",
            password="password123",
        )
        self.stranger = User.objects.create_user(
            username="other_person",
            password="password123",
        )
        self.admin = User.objects.create_superuser(
            username="admin_editor",
            password="password123",
        )
        self.post = Forum.objects.create(
            author_username=self.owner.username,
            title="Judul Asli",
            content="Konten asli sebelum diedit.",
            category="DISCUSSION",
        )
        self.url = reverse("forum:edit_post_api", args=[self.post.id])

    def test_edit_post_api_owner_success_urlencoded(self):
        self.client.force_login(self.owner)
        payload = {
            "title": "Judul Terupdate",
            "content": "Konten terupdate.",
            "category": "INSPO",
            "image_url": "https://example.com/updated.jpg",
            "image_caption": "Caption baru",
        }
        response = self.client.put(
            self.url,
            data=urlencode(payload),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Judul Terupdate")
        self.assertEqual(self.post.category, "INSPO")

    def test_edit_post_api_owner_success_json(self):
        self.client.force_login(self.owner)
        payload = {
            "title": "Judul Terupdate JSON",
            "content": "Konten via JSON body.",
            "category": "OOTD",
            "image_url": "",
            "image_caption": "",
        }
        response = self.client.put(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Judul Terupdate JSON")

    def test_edit_post_api_superuser_success(self):
        self.client.force_login(self.admin)
        response = self.client.put(
            self.url,
            data=urlencode({"title": "Admin Override", "content": "Konten admin", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Admin Override")

    def test_edit_post_api_unauthenticated(self):
        response = self.client.put(
            self.url,
            data=urlencode({"title": "Edit Anonim", "content": "Konten", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 401)

    def test_edit_post_api_forbidden_stranger(self):
        self.client.force_login(self.stranger)
        response = self.client.put(
            self.url,
            data=urlencode({"title": "Hacker Edit", "content": "Konten", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Judul Asli")

    def test_edit_post_api_not_found(self):
        self.client.force_login(self.owner)
        random_uuid = uuid.uuid4()
        response = self.client.put(
            reverse("forum:edit_post_api", args=[random_uuid]),
            data=urlencode({"title": "X", "content": "Y", "category": "DISCUSSION"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_post_api_validation_errors(self):
        self.client.force_login(self.owner)
        response = self.client.put(
            self.url,
            data=urlencode({"title": "", "content": "", "category": "INVALID"}),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())

    def test_edit_post_api_malformed_json(self):
        self.client.force_login(self.owner)
        response = self.client.put(
            self.url,
            data="invalid-json-content",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_post_api_invalid_method(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url, data={"title": "Test"})
        self.assertEqual(response.status_code, 405)


class ForumDeletePostAPITests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_to_delete",
            password="password123",
        )
        self.stranger = User.objects.create_user(
            username="stranger_deleter",
            password="password123",
        )
        self.admin = User.objects.create_superuser(
            username="admin_deleter",
            password="password123",
        )
        self.post = Forum.objects.create(
            author_username=self.owner.username,
            title="Post Akan Dihapus",
            content="Konten post",
        )
        self.url = reverse("forum:delete_post_api", args=[self.post.id])

    def test_delete_post_api_owner_success(self):
        self.client.force_login(self.owner)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Post deleted successfully")
        self.assertFalse(Forum.objects.filter(pk=self.post.id).exists())

    def test_delete_post_api_superuser_success(self):
        self.client.force_login(self.admin)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Forum.objects.filter(pk=self.post.id).exists())

    def test_delete_post_api_unauthenticated(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Forum.objects.filter(pk=self.post.id).exists())

    def test_delete_post_api_forbidden_stranger(self):
        self.client.force_login(self.stranger)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Forum.objects.filter(pk=self.post.id).exists())

    def test_delete_post_api_not_found(self):
        self.client.force_login(self.owner)
        random_uuid = uuid.uuid4()
        response = self.client.delete(reverse("forum:delete_post_api", args=[random_uuid]))
        self.assertEqual(response.status_code, 404)

    def test_delete_post_api_invalid_method(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class ForumLikeAPITests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="liker1", password="password123")
        self.user2 = User.objects.create_user(username="liker2", password="password123")
        self.post = Forum.objects.create(
            author_username="post_author",
            title="Post Interaktif",
            content="Konten interaktif",
        )
        self.url = reverse("forum:like_post_api", args=[self.post.id])

    def test_like_post_api_toggle(self):
        self.client.force_login(self.user1)

        # 1. First like -> liked=True, total_likes=1
        res1 = self.client.post(self.url)
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json()["liked"])
        self.assertEqual(res1.json()["total_likes"], 1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.total_likes, 1)
        self.assertTrue(self.post.is_liked_by(self.user1))

        # 2. Second like (unlike) -> liked=False, total_likes=0
        res2 = self.client.post(self.url)
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(res2.json()["liked"])
        self.assertEqual(res2.json()["total_likes"], 0)
        self.post.refresh_from_db()
        self.assertEqual(self.post.total_likes, 0)
        self.assertFalse(self.post.is_liked_by(self.user1))

    def test_like_post_api_multiple_users(self):
        # User 1 likes
        self.client.force_login(self.user1)
        self.client.post(self.url)

        # User 2 likes
        self.client.force_login(self.user2)
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total_likes"], 2)

        self.post.refresh_from_db()
        self.assertEqual(self.post.total_likes, 2)
        self.assertEqual(self.post.liked_by.count(), 2)

    def test_like_post_api_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "Authentication required. Silakan masuk terlebih dahulu.")

    def test_like_post_api_not_found(self):
        self.client.force_login(self.user1)
        random_uuid = uuid.uuid4()
        response = self.client.post(reverse("forum:like_post_api", args=[random_uuid]))
        self.assertEqual(response.status_code, 404)

    def test_like_post_api_invalid_method(self):
        self.client.force_login(self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class ForumCommentAPITests(TestCase):
    def setUp(self):
        self.post_author = User.objects.create_user(
            username="author_of_post",
            password="password123",
        )
        self.comment_author = User.objects.create_user(
            username="author_of_comment",
            password="password123",
        )
        self.stranger = User.objects.create_user(
            username="stranger_commenter",
            password="password123",
        )
        self.admin = User.objects.create_superuser(
            username="admin_commenter",
            password="password123",
        )
        self.post = Forum.objects.create(
            author_username=self.post_author.username,
            title="Post Diskusi Komentar",
            content="Konten diskusi",
        )
        self.add_comment_url = reverse("forum:add_comment_api", args=[self.post.id])
        self.get_comments_url = reverse("forum:get_comments_api", args=[self.post.id])

    def test_add_comment_api_success_json(self):
        self.client.force_login(self.comment_author)
        payload = {"content": "Ini komentar pertama via JSON"}
        response = self.client.post(
            self.add_comment_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["comment"]["content"], "Ini komentar pertama via JSON")
        self.assertEqual(data["comment"]["author_username"], self.comment_author.username)
        self.assertEqual(data["total_comments"], 1)

        self.post.refresh_from_db()
        self.assertEqual(self.post.total_comments, 1)

    def test_add_comment_api_success_form_data(self):
        self.client.force_login(self.comment_author)
        response = self.client.post(
            self.add_comment_url,
            data={"content": "Komentar via form POST"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["comment"]["content"], "Komentar via form POST")

        self.post.refresh_from_db()
        self.assertEqual(self.post.total_comments, 1)

    def test_add_comment_api_escapes_xss_tags(self):
        self.client.force_login(self.comment_author)
        payload = {"content": "<script>alert('hack')</script>"}
        res = self.client.post(
            self.add_comment_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        comment = Comment.objects.get(pk=res.json()["comment"]["id"])
        self.assertEqual(comment.content, "&lt;script&gt;alert(&#x27;hack&#x27;)&lt;/script&gt;")

    def test_add_comment_api_unauthenticated(self):
        response = self.client.post(
            self.add_comment_url,
            data=json.dumps({"content": "Komentar anonim"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Comment.objects.count(), 0)

    def test_add_comment_api_not_found(self):
        self.client.force_login(self.comment_author)
        random_uuid = uuid.uuid4()
        response = self.client.post(
            reverse("forum:add_comment_api", args=[random_uuid]),
            data=json.dumps({"content": "Komentar"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_add_comment_api_empty_and_whitespace(self):
        self.client.force_login(self.comment_author)
        for empty_val in ["", "    ", "\n\t"]:
            res = self.client.post(
                self.add_comment_url,
                data=json.dumps({"content": empty_val}),
                content_type="application/json",
            )
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["error"], "Komentar tidak boleh kosong.")

    def test_add_comment_api_max_length_exceeded(self):
        self.client.force_login(self.comment_author)
        long_content = "x" * 2001
        response = self.client.post(
            self.add_comment_url,
            data=json.dumps({"content": long_content}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Komentar maksimal 2.000 karakter.")

    def test_add_comment_api_malformed_json(self):
        self.client.force_login(self.comment_author)
        response = self.client.post(
            self.add_comment_url,
            data="not a json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Komentar tidak boleh kosong.")

    def test_add_comment_api_invalid_method(self):
        self.client.force_login(self.comment_author)
        response = self.client.get(self.add_comment_url)
        self.assertEqual(response.status_code, 405)

    def test_get_comments_api_sorting_newest_and_oldest(self):
        c1 = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar Awal",
        )
        c2 = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar Belakangan",
        )
        # Update timestamp of c1 to be strictly earlier
        Comment.objects.filter(pk=c1.pk).update(
            created_at=timezone.now() - timedelta(minutes=10)
        )

        # 1. Default (newest): c2 first
        res_newest = self.client.get(self.get_comments_url)
        self.assertEqual(res_newest.status_code, 200)
        self.assertEqual(res_newest.json()["comments"][0]["content"], "Komentar Belakangan")
        self.assertEqual(res_newest.json()["total_comments"], 2)

        # 2. Sort oldest: c1 first
        res_oldest = self.client.get(self.get_comments_url, {"sort": "oldest"})
        self.assertEqual(res_oldest.status_code, 200)
        self.assertEqual(res_oldest.json()["comments"][0]["content"], "Komentar Awal")

    def test_get_comments_api_not_found(self):
        random_uuid = uuid.uuid4()
        response = self.client.get(reverse("forum:get_comments_api", args=[random_uuid]))
        self.assertEqual(response.status_code, 404)

    def test_get_comments_api_invalid_method(self):
        response = self.client.post(self.get_comments_url)
        self.assertEqual(response.status_code, 405)

    def test_delete_comment_api_by_comment_author(self):
        comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar akan dihapus",
        )
        self.post.total_comments = 1
        self.post.save()

        del_url = reverse("forum:delete_comment_api", args=[comment.id])
        self.client.force_login(self.comment_author)
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_comments"], 0)
        self.assertFalse(Comment.objects.filter(pk=comment.id).exists())

        self.post.refresh_from_db()
        self.assertEqual(self.post.total_comments, 0)

    def test_delete_comment_api_by_post_author_moderation(self):
        # Post author can moderate/delete any comment on their post
        comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar dari user lain",
        )
        del_url = reverse("forum:delete_comment_api", args=[comment.id])
        self.client.force_login(self.post_author)
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(pk=comment.id).exists())

    def test_delete_comment_api_by_superuser(self):
        comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar",
        )
        del_url = reverse("forum:delete_comment_api", args=[comment.id])
        self.client.force_login(self.admin)
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(pk=comment.id).exists())

    def test_delete_comment_api_using_post_method(self):
        comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar via POST delete",
        )
        del_url = reverse("forum:delete_comment_api", args=[comment.id])
        self.client.force_login(self.comment_author)
        response = self.client.post(del_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(pk=comment.id).exists())

    def test_delete_comment_api_unauthenticated(self):
        comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar",
        )
        del_url = reverse("forum:delete_comment_api", args=[comment.id])
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Comment.objects.filter(pk=comment.id).exists())

    def test_delete_comment_api_forbidden_stranger(self):
        comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar orang lain",
        )
        del_url = reverse("forum:delete_comment_api", args=[comment.id])
        self.client.force_login(self.stranger)
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.id).exists())

    def test_delete_comment_api_not_found(self):
        self.client.force_login(self.comment_author)
        random_uuid = uuid.uuid4()
        del_url = reverse("forum:delete_comment_api", args=[random_uuid])
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, 404)

    def test_delete_comment_api_invalid_method(self):
        comment = Comment.objects.create(
            forum=self.post,
            user=self.comment_author,
            author_username=self.comment_author.username,
            content="Komentar",
        )
        del_url = reverse("forum:delete_comment_api", args=[comment.id])
        self.client.force_login(self.comment_author)
        response = self.client.get(del_url)
        self.assertEqual(response.status_code, 405)


class ForumUrlTests(TestCase):
    def test_forum_urls_resolve_to_views(self):
        test_uuid = uuid.uuid4()
        url_views = [
            ("forum:forum_main", [], forum_main),
            ("forum:forum_detail", [test_uuid], forum_detail),
            ("forum:get_posts_api", [], get_posts_api),
            ("forum:create_post_api", [], create_post_api),
            ("forum:edit_post_api", [test_uuid], edit_post_api),
            ("forum:delete_post_api", [test_uuid], delete_post_api),
            ("forum:like_post_api", [test_uuid], like_post_api),
            ("forum:add_comment_api", [test_uuid], add_comment_api),
            ("forum:get_comments_api", [test_uuid], get_comments_api),
            ("forum:delete_comment_api", [test_uuid], delete_comment_api),
        ]
        for url_name, args, expected_view in url_views:
            path = reverse(url_name, args=args)
            match = resolve(path)
            self.assertEqual(match.func, expected_view)


# Backwards compatibility class for existing suites
class ForumCreateModalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
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
