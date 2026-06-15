from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0014_homeslide"),
    ]

    operations = [
        migrations.AddField(
            model_name="homeslide",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="home_slides/",
                verbose_name="Фоновое изображение",
            ),
        ),
    ]
