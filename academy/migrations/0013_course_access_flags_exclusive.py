from django.db import migrations


def fix_exclusive_access_flags(apps, schema_editor):
    Course = apps.get_model("academy", "Course")
    Course.objects.filter(is_published=True, is_private=True).update(is_published=False)


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0012_psychologist_photo"),
    ]

    operations = [
        migrations.RunPython(fix_exclusive_access_flags, migrations.RunPython.noop),
    ]
