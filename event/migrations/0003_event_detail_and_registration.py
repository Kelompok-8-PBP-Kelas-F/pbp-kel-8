import decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0002_event_category"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="attendees",
            field=models.ManyToManyField(
                blank=True,
                related_name="attending_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="cover_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="events/covers/",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="end_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="max_attendees",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[MinValueValidator(1)],
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="preparation_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="event",
            name="registration_fee",
            field=models.DecimalField(
                decimal_places=2,
                default=decimal.Decimal("0.00"),
                max_digits=10,
                validators=[MinValueValidator(decimal.Decimal("0.00"))],
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="rules",
            field=models.TextField(blank=True),
        ),
    ]
