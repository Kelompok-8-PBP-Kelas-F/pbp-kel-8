from django.db import migrations


def create_schema(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        try:
            schema_editor.execute("CREATE SCHEMA IF NOT EXISTS tugas_kelompok;")
        except Exception:
            pass


def drop_schema(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("DROP SCHEMA IF EXISTS tugas_kelompok;")


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.RunPython(create_schema, drop_schema),
    ]
