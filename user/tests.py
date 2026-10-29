from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="TestUser",
            password="S3cure!VeryLongTiger",
        )
        self.url = reverse("user:login")

    def test_get_displays_login_form_and_next_query(self):
        response = self.client.get(self.url, {"next": "/news/"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/user/login.html")
        self.assertEqual(response.context["next_url"], "/news/")
        self.assertEqual(response.context["username"], "")
        self.assertEqual(response.context["error"], "")

    def test_authenticated_user_is_redirected(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("core:landing_page"))

    def test_invalid_credentials_keep_username_and_display_error(self):
        for username, password in (
            ("missing-user", "any-password"),
            ("TestUser", "incorrect-password"),
        ):
            with self.subTest(username=username):
                response = self.client.post(
                    self.url,
                    {"username": username, "password": password},
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["username"], username)
                self.assertEqual(
                    response.context["error"],
                    "Username atau password salah.",
                )
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_successful_login_is_case_insensitive_and_remembers_session(self):
        response = self.client.post(
            self.url,
            {
                "username": "  testuser ",
                "password": "S3cure!VeryLongTiger",
                "remember_me": "on",
                "next": "/news/",
            },
        )

        self.assertRedirects(response, "/news/")
        self.assertEqual(
            self.client.session.get_expiry_age(),
            60 * 60 * 24 * 14,
        )
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.user.pk,
        )

    def test_login_without_remembering_uses_browser_session(self):
        response = self.client.post(
            self.url,
            {
                "username": "TestUser",
                "password": "S3cure!VeryLongTiger",
            },
        )

        self.assertRedirects(response, reverse("core:landing_page"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_unsafe_next_url_falls_back_to_landing_page(self):
        response = self.client.post(
            self.url,
            {
                "username": "TestUser",
                "password": "S3cure!VeryLongTiger",
                "next": "https://evil.example/steal-session",
            },
        )

        self.assertRedirects(response, reverse("core:landing_page"))

    def test_post_next_url_takes_precedence_over_query_string(self):
        response = self.client.post(
            f"{self.url}?next=/forum/",
            {
                "username": "TestUser",
                "password": "S3cure!VeryLongTiger",
                "next": "/news/",
            },
        )

        self.assertRedirects(response, "/news/")


class RegisterTests(TestCase):
    def setUp(self):
        self.url = reverse("user:register")

    def test_get_displays_registration_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/user/register.html")
        self.assertEqual(response.context["username"], "")
        self.assertEqual(response.context["error"], "")

    def test_authenticated_user_is_redirected(self):
        user = User.objects.create_user(username="already-logged-in")
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("core:landing_page"))

    def test_blank_or_too_long_username_is_rejected(self):
        for username in ("   ", "u" * 151):
            with self.subTest(username_length=len(username)):
                response = self.client.post(
                    self.url,
                    {
                        "username": username,
                        "password": "S3cure!VeryLongTiger",
                        "password_confirm": "S3cure!VeryLongTiger",
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.context["error"],
                    "Username tidak boleh kosong.",
                )
                self.assertFalse(User.objects.exists())

    def test_duplicate_username_is_rejected_case_insensitively(self):
        User.objects.create_user(username="ExistingUser")

        response = self.client.post(
            self.url,
            {
                "username": "existinguser",
                "password": "S3cure!VeryLongTiger",
                "password_confirm": "S3cure!VeryLongTiger",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["error"],
            "Username sudah digunakan.",
        )
        self.assertEqual(User.objects.count(), 1)

    def test_password_confirmation_must_match(self):
        response = self.client.post(
            self.url,
            {
                "username": "new-user",
                "password": "S3cure!VeryLongTiger",
                "password_confirm": "different-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["error"],
            "Konfirmasi password tidak cocok.",
        )
        self.assertFalse(User.objects.exists())

    def test_password_validation_error_is_displayed(self):
        response = self.client.post(
            self.url,
            {
                "username": "new-user",
                "password": "password",
                "password_confirm": "password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["error"])
        self.assertFalse(User.objects.exists())

    def test_valid_registration_creates_and_logs_in_user(self):
        response = self.client.post(
            self.url,
            {
                "username": "  new-user ",
                "password": "S3cure!VeryLongTiger",
                "password_confirm": "S3cure!VeryLongTiger",
            },
        )

        user = User.objects.get(username="new-user")
        self.assertRedirects(response, reverse("core:landing_page"))
        self.assertTrue(user.check_password("S3cure!VeryLongTiger"))
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.pk,
        )


class LogoutTests(TestCase):
    def test_logout_clears_authenticated_session_and_redirects(self):
        user = User.objects.create_user(username="signed-in")
        self.client.force_login(user)

        response = self.client.get(reverse("user:logout"))

        self.assertRedirects(response, reverse("core:landing_page"))
        self.assertNotIn("_auth_user_id", self.client.session)
