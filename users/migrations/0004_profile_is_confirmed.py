# Generated by Django 2.0.6 on 2018-07-01 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_profile_full_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
