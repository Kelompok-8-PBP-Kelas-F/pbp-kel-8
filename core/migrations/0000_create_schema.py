from django.db import migrations


def create_schema(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        try:
            with schema_editor.connection.cursor() as cursor:
                cursor.execute("SAVEPOINT create_schema_sp;")
                cursor.execute("CREATE SCHEMA IF NOT EXISTS tugas_kelompok;")
        except Exception:
            with schema_editor.connection.cursor() as cursor:
                cursor.execute("ROLLBACK TO SAVEPOINT create_schema_sp;")


def drop_schema(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("DROP SCHEMA IF EXISTS tugas_kelompok;")


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.RunPython(create_schema, drop_schema),
    ]
