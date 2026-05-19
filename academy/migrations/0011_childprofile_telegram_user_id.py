from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0010_testoption_identifier_testoption_is_hidden_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="childprofile",
            name="telegram_user_id",
            field=models.BigIntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
    ]
