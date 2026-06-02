from django.db import migrations, models


def add_read_at_if_missing(apps, schema_editor):
    table_name = 'notifications_notification'
    conn = schema_editor.connection
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(%s)" % table_name)
        cols = [row[1] for row in cursor.fetchall()]
    except Exception:
        cols = []

    if 'read_at' not in cols:
        # Add column via SQL for SQLite (ALTER TABLE ADD COLUMN is supported)
        cursor.execute("ALTER TABLE %s ADD COLUMN read_at datetime NULL;" % table_name)


def noop_reverse(apps, schema_editor):
    # Removing columns in SQLite is non-trivial; keep reverse as no-op.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_read_at_if_missing, noop_reverse),
    ]
