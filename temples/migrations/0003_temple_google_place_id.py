# Generated by Django 5.2 on 2025-04-05 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0002_temple_name_temple_raw_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="temple",
            name="google_place_id",
            field=models.CharField(default='', max_length=512),
        ),
    ]
