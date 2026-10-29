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
        self.assertContains(response, "dark:bg-[#151a15]")
        self.assertContains(response, "dark:brightness-75")
        self.assertContains(response, "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.assertContains(response, "https://tile.openstreetmap.de/{z}/{x}/{y}.png")
        self.assertContains(response, "Pasar Tukar Pakaian Bandung")
        self.assertContains(response, "Event mendatang &amp; rekomendasi")


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
