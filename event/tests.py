from decimal import Decimal
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .forms import EventForm
from .models import Event


class EventPageTests(TestCase):
    def test_event_page_renders_openstreetmap_and_agenda(self):
        response = self.client.get(reverse("event:event_page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Referrer-Policy"],
            "strict-origin-when-cross-origin",
        )
        self.assertContains(response, "dark:bg-[#151a15]")
        self.assertContains(response, "dark:brightness-75")
        self.assertContains(response, "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.assertContains(response, "https://tile.openstreetmap.de/{z}/{x}/{y}.png")
        self.assertNotContains(response, "Pasar Tukar Pakaian Bandung")
        self.assertContains(response, "Event mendatang &amp; rekomendasi")
        self.assertEqual(response.context["events"], [])

    def test_persisted_events_link_to_their_detail_page(self):
        organizer = get_user_model().objects.create_user(username="page-organizer")
        event = Event.objects.create(
            name="Acara komunitas",
            organizer=organizer,
            category="Swap",
            desc="Tukar pakaian bersama.",
            date="2026-11-10",
            time="10:00",
            location="Bandung",
            latitude="-7.7956",
            longitude="110.3695",
        )
        event.refresh_from_db()

        response = self.client.get(reverse("event:event_page"))

        self.assertContains(response, f"/event/{event.pk}/")
        self.assertContains(response, event.name)
        self.assertEqual(
            response.context["events"],
            [
                {
                    "id": str(event.pk),
                    "name": event.name,
                    "tag": "SWAP",
                    "category": "Fashion sirkular",
                    "type": "Swap",
                    "date": event.date.isoformat(),
                    "time": "10.00",
                    "location": event.location,
                    "distance": None,
                    "latitude": -7.7956,
                    "longitude": 110.3695,
                    "description": event.desc,
                    "detail_url": reverse("event:event_detail", args=[event.pk]),
                }
            ],
        )

    def test_authenticated_user_profile_location_is_the_default_map_location(self):
        user = get_user_model().objects.create_user(username="location-owner")
        user.profile.location = "Yogyakarta"
        user.profile.save()
        self.client.force_login(user)

        response = self.client.get(reverse("event:event_page"))

        self.assertEqual(response.context["user_location"], "Yogyakarta")
        self.assertContains(response, 'value="Yogyakarta"')


class EventModelTests(TestCase):
    def setUp(self):
        self.organizer = get_user_model().objects.create_user(username="organizer")
        self.event = Event.objects.create(
            name="Kelas reparasi",
            organizer=self.organizer,
            desc="Belajar memperbaiki pakaian.",
            date="2026-11-01",
            time="10:00",
            location="Bandung",
        )

    def test_distance_uses_placeholder_when_user_or_event_coordinates_are_missing(self):
        self.assertEqual(self.event.distance_from_user(), "—")
        self.event.latitude = 0
        self.event.longitude = 0
        self.assertEqual(self.event.distance_from_user(0, None), "—")

    def test_distance_is_calculated_from_user_coordinates(self):
        self.event.latitude = 0
        self.event.longitude = 1

        self.assertEqual(self.event.distance_from_user(0, 0), "111.2 km")


class EventDetailTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organizer = user_model.objects.create_user(username="detail-organizer")
        self.attendee = user_model.objects.create_user(username="detail-attendee")
        self.event = Event.objects.create(
            name="Pasar Tukar Pakaian Bandung",
            organizer=self.organizer,
            category="Swap",
            desc="Tukar pakaian layak pakai bersama komunitas.",
            rules="Pastikan pakaian bersih.",
            preparation_notes="Bawa tas belanja sendiri.",
            date="2026-11-10",
            time="10:00",
            end_time="17:00",
            location="Gedung Sate, Bandung",
            latitude="-6.902500",
            longitude="107.618800",
            max_attendees=2,
        )

    def test_event_detail_shows_event_information_and_openstreetmap(self):
        response = self.client.get(
            reverse("event:event_detail", args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.name)
        self.assertContains(response, "Aturan Umum")
        self.assertContains(response, "Bawa tas belanja sendiri.")
        self.assertContains(response, "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.assertContains(response, "Selasa, 10 Nov 2026")
        self.assertContains(response, "Petunjuk arah")

    def test_event_detail_shows_a_friendly_message_if_coordinates_are_missing(self):
        self.event.latitude = None
        self.event.longitude = None
        self.event.save()

        response = self.client.get(
            reverse("event:event_detail", args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Koordinat peta belum tersedia")
        self.assertContains(response, "Cari di peta")

    def test_authenticated_user_can_register_and_cancel_registration(self):
        self.client.force_login(self.attendee)
        url = reverse("event:register_for_event", args=[self.event.pk])

        response = self.client.post(url, {"action": "join"})
        self.assertRedirects(
            response,
            reverse("event:event_detail", args=[self.event.pk]),
        )
        self.assertTrue(self.event.attendees.filter(pk=self.attendee.pk).exists())

        response = self.client.post(url, {"action": "leave"})
        self.assertRedirects(
            response,
            reverse("event:event_detail", args=[self.event.pk]),
        )
        self.assertFalse(self.event.attendees.filter(pk=self.attendee.pk).exists())

    def test_registration_is_rejected_when_event_is_full(self):
        other_attendee = get_user_model().objects.create_user(username="other-attendee")
        self.event.attendees.add(self.organizer, other_attendee)
        self.client.force_login(self.attendee)

        self.client.post(
            reverse("event:register_for_event", args=[self.event.pk]),
            {"action": "join"},
        )

        self.assertFalse(self.event.attendees.filter(pk=self.attendee.pk).exists())
        response = self.client.get(
            reverse("event:event_detail", args=[self.event.pk])
        )
        self.assertContains(response, "Kuota sudah penuh")

    def test_guest_registration_redirects_to_login(self):
        response = self.client.post(
            reverse("event:register_for_event", args=[self.event.pk]),
            {"action": "join"},
        )

        self.assertRedirects(
            response,
            f"{reverse('user:login')}?next="
            f"{reverse('event:register_for_event', args=[self.event.pk])}",
            fetch_redirect_response=False,
        )


class EventCrudTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="event-owner")
        self.other_user = user_model.objects.create_user(username="other-user")
        self.event = Event.objects.create(
            name="Acara milik saya",
            organizer=self.owner,
            category="Swap",
            desc="Deskripsi acara.",
            date="2026-11-10",
            time="10:00",
            location="Gedung Sate, Bandung",
        )
        self.form_data = {
            "name": "Workshop reparasi",
            "category": "Workshop",
            "desc": "Belajar memperbaiki pakaian.",
            "date": "2026-11-01",
            "time": "10:00",
            "location": "Gedung Sate, Bandung",
            "registration_fee": "0.00",
        }

    def test_guest_is_redirected_from_all_crud_routes(self):
        urls = [
            reverse("event:event_create"),
            reverse("event:event_edit", args=[self.event.pk]),
            reverse("event:event_delete", args=[self.event.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("user:login"), response.url)

    def test_authenticated_user_can_create_event_as_organizer(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("event:event_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')

        geocoding_response = Mock()
        geocoding_response.json.return_value = [{"lat": "-6.9025", "lon": "107.6188"}]
        with patch("event.forms.requests.get", return_value=geocoding_response):
            response = self.client.post(
                reverse("event:event_create"),
                self.form_data,
            )

        created_event = Event.objects.get(name=self.form_data["name"])
        self.assertRedirects(
            response,
            reverse("event:event_detail", args=[created_event.pk]),
        )
        self.assertEqual(created_event.organizer, self.owner)
        self.assertEqual(created_event.latitude, Decimal("-6.9025"))

    @patch("event.forms.requests.get")
    def test_owner_can_edit_event(self, get):
        geocoding_response = Mock()
        geocoding_response.json.return_value = [{"lat": "-6.9025", "lon": "107.6188"}]
        get.return_value = geocoding_response
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("event:event_edit", args=[self.event.pk]),
            {**self.form_data, "name": "Nama event diperbarui"},
        )

        self.assertRedirects(
            response,
            reverse("event:event_detail", args=[self.event.pk]),
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Nama event diperbarui")
        self.assertEqual(self.event.organizer, self.owner)

    def test_user_cannot_edit_or_delete_another_users_event(self):
        self.client.force_login(self.other_user)

        detail_response = self.client.get(
            reverse("event:event_detail", args=[self.event.pk])
        )
        edit_response = self.client.post(
            reverse("event:event_edit", args=[self.event.pk]),
            {**self.form_data, "name": "Perubahan tidak sah"},
        )
        delete_response = self.client.post(
            reverse("event:event_delete", args=[self.event.pk])
        )

        self.assertNotContains(detail_response, "Edit event")
        self.assertNotContains(detail_response, "Hapus event")
        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Acara milik saya")

    def test_owner_sees_event_management_controls(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("event:event_detail", args=[self.event.pk])
        )

        self.assertContains(response, "Edit event")
        self.assertContains(response, "Hapus event")

    def test_owner_delete_requires_post_and_removes_event(self):
        self.client.force_login(self.owner)
        delete_url = reverse("event:event_delete", args=[self.event.pk])

        confirmation = self.client.get(delete_url)
        self.assertEqual(confirmation.status_code, 200)
        self.assertContains(confirmation, 'method="post"')
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

        response = self.client.post(delete_url)

        self.assertRedirects(response, reverse("event:event_page"))
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())


class EventFormTests(TestCase):
    def setUp(self):
        cache.clear()
        self.form_data = {
            "name": "Workshop reparasi",
            "category": "Workshop",
            "desc": "Belajar memperbaiki pakaian.",
            "date": "2026-11-01",
            "time": "10:00",
            "location": "Gedung Sate, Bandung",
            "registration_fee": "0.00",
        }

    @patch("event.forms.requests.get")
    def test_location_is_geocoded_and_coordinates_are_saved_on_event(self, get):
        response = Mock()
        response.json.return_value = [{"lat": "-6.9025", "lon": "107.6188"}]
        get.return_value = response
        form = EventForm(data=self.form_data)

        self.assertTrue(form.is_valid(), form.errors)
        event = form.save(commit=False)

        self.assertEqual(event.latitude, Decimal("-6.9025"))
        self.assertEqual(event.longitude, Decimal("107.6188"))
        self.assertNotIn("organizer", form.fields)
        self.assertIn("cover_image", form.fields)
        self.assertIn("rules", form.fields)
        self.assertIn("registration_fee", form.fields)
        get.assert_called_once()

    @patch("event.forms.requests.get")
    def test_successful_location_lookup_is_cached(self, get):
        response = Mock()
        response.json.return_value = [{"lat": "-6.9025", "lon": "107.6188"}]
        get.return_value = response

        first_form = EventForm(data=self.form_data)
        second_form = EventForm(data=self.form_data)

        self.assertTrue(first_form.is_valid(), first_form.errors)
        self.assertTrue(second_form.is_valid(), second_form.errors)
        get.assert_called_once()

    @patch("event.forms.requests.get")
    def test_location_error_is_reported_when_geocoder_finds_no_results(self, get):
        response = Mock()
        response.json.return_value = []
        get.return_value = response
        form = EventForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("Lokasi tidak ditemukan", str(form.errors["location"]))

    @patch("event.forms.requests.get")
    def test_geocoding_is_skipped_when_other_form_fields_are_invalid(self, get):
        form = EventForm(data={**self.form_data, "name": ""})

        self.assertFalse(form.is_valid())
        get.assert_not_called()

    @patch("event.forms.requests.get", side_effect=requests.Timeout)
    def test_geocoding_service_errors_are_reported(self, get):
        form = EventForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("belum dapat diverifikasi", str(form.errors["location"]))
