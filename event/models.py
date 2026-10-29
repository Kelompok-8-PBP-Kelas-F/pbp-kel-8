import math
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Event(models.Model):
    CATEGORY_CHOICES = [
        ("Workshop", "Workshop"),
        ("Thrift/Bazaar", "Thrift/Bazaar"),
        ("Swap", "Swap"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    desc = models.TextField()
    date = models.DateField()
    time = models.TimeField(max_length=20)
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def distance_from_user(self, latitude=None, longitude=None):
        if (
            latitude is None
            or longitude is None
            or self.latitude is None
            or self.longitude is None
        ):
            return "—"

        latitude = float(latitude)
        longitude = float(longitude)
        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise ValueError("User coordinates must be valid latitude and longitude values.")

        user_latitude = math.radians(latitude)
        user_longitude = math.radians(longitude)
        event_latitude = math.radians(float(self.latitude))
        event_longitude = math.radians(float(self.longitude))
        latitude_delta = event_latitude - user_latitude
        longitude_delta = event_longitude - user_longitude

        haversine = (
            math.sin(latitude_delta / 2) ** 2
            + math.cos(user_latitude)
            * math.cos(event_latitude)
            * math.sin(longitude_delta / 2) ** 2
        )
        distance = 6371 * 2 * math.asin(math.sqrt(min(1, haversine)))
        return f"{distance:.1f} km"

    def __str__(self):
        return self.name