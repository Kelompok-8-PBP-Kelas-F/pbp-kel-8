import hashlib
from decimal import Decimal, InvalidOperation

import requests
from django import forms
from django.core.cache import cache

from .models import Event


def _geocode_location(location):
    normalized_location = " ".join(location.split())
    cache_key = "event-geocode:" + hashlib.sha256(
        normalized_location.casefold().encode("utf-8")
    ).hexdigest()
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cache_key, cached_result

    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": normalized_location,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "id",
        },
        headers={"User-Agent": "Thrift.io/1.0 (event location geocoding)"},
        timeout=(3.05, 10),
    )
    response.raise_for_status()
    results = response.json()
    if not isinstance(results, list):
        raise ValueError("Location service returned an invalid response.")
    if not results:
        cache.set(cache_key, {}, timeout=600)
        return cache_key, {}
    if not isinstance(results[0], dict):
        raise ValueError("Location service returned invalid coordinates.")

    return cache_key, results[0]


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ("name", "category", "desc", "date", "time", "location")
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full border-2 border-line bg-surface p-2.5 text-foreground",
                "placeholder": "Nama event",
            }),
            "category": forms.Select(attrs={
                "class": "w-full border-2 border-line bg-surface p-2.5 text-foreground",
            }),
            "desc": forms.Textarea(attrs={
                "class": "w-full border-2 border-line bg-surface p-2.5 text-foreground",
                "rows": 4,
                "placeholder": "Deskripsi event",
            }),
            "date": forms.DateInput(attrs={
                "class": "w-full border-2 border-line bg-surface p-2.5 text-foreground",
                "type": "date",
            }),
            "time": forms.TimeInput(attrs={
                "class": "w-full border-2 border-line bg-surface p-2.5 text-foreground",
                "type": "time",
            }),
            "location": forms.TextInput(attrs={
                "class": "w-full border-2 border-line bg-surface p-2.5 text-foreground",
                "placeholder": "Contoh: Gedung Sate, Bandung",
                "autocomplete": "street-address",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location"].help_text = (
            "Latitude dan longitude akan dicari otomatis dari OpenStreetMap."
        )

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        location = cleaned_data.get("location")
        if not location:
            return cleaned_data

        try:
            cache_key, result = _geocode_location(location)
        except requests.RequestException:
            self.add_error(
                "location",
                "Lokasi belum dapat diverifikasi. Periksa koneksi internet lalu coba lagi.",
            )
            return cleaned_data
        except ValueError:
            self.add_error(
                "location",
                "Layanan pencarian lokasi memberikan respons yang tidak valid. Coba lagi nanti.",
            )
            return cleaned_data

        if not result:
            self.add_error(
                "location",
                "Lokasi tidak ditemukan. Masukkan nama tempat beserta kota atau alamat yang lebih lengkap.",
            )
            return cleaned_data

        try:
            latitude = Decimal(result["lat"])
            longitude = Decimal(result["lon"])
        except (KeyError, InvalidOperation, TypeError):
            self.add_error(
                "location",
                "Koordinat lokasi tidak valid. Coba masukkan alamat yang lebih spesifik.",
            )
            return cleaned_data

        if (
            not latitude.is_finite()
            or not longitude.is_finite()
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            self.add_error(
                "location",
                "Koordinat lokasi berada di luar rentang yang valid. Coba masukkan alamat lain.",
            )
            return cleaned_data

        cache.set(
            cache_key,
            {"lat": str(latitude), "lon": str(longitude)},
            timeout=30 * 24 * 60 * 60,
        )
        self.instance.latitude = latitude
        self.instance.longitude = longitude
        return cleaned_data
