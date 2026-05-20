from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0011_childprofile_telegram_user_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="psychologist",
            name="photo_url",
        ),
        migrations.AddField(
            model_name="psychologist",
            name="photo",
            field=models.ImageField(blank=True, upload_to="psychologists/"),
        ),
    ]
