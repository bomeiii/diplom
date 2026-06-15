from django.db import migrations, models


def create_default_slides(apps, schema_editor):
    HomeSlide = apps.get_model("academy", "HomeSlide")
    if HomeSlide.objects.exists():
        return
    HomeSlide.objects.bulk_create(
        [
            HomeSlide(
                title="Пространство для роста и поддержки",
                text="Психологические курсы и материалы для детей и подростков — в спокойном и понятном формате.",
                order=1,
                is_active=True,
            ),
            HomeSlide(
                title="Учимся понимать себя",
                text="Статьи, тесты и интерактивные задания от профессиональных психологов.",
                order=2,
                is_active=True,
            ),
        ]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0013_course_access_flags_exclusive"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomeSlide",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Заголовок")),
                ("text", models.TextField(blank=True, verbose_name="Текст на слайде")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Показывать")),
            ],
            options={
                "verbose_name": "Слайд главной страницы",
                "verbose_name_plural": "Слайды главной страницы",
                "ordering": ["order", "id"],
            },
        ),
        migrations.RunPython(create_default_slides, migrations.RunPython.noop),
    ]
