from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="category",
            field=models.CharField(
                choices=[
                    ("Workshop", "Workshop"),
                    ("Thrift/Bazaar", "Thrift/Bazaar"),
                    ("Swap", "Swap"),
                ],
                default="Workshop",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="event",
            name="time",
            field=models.TimeField(max_length=20),
        ),
    ]
