# Generated by Django 2.0.6 on 2018-07-02 06:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_profile_is_confirmed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='is_confirmed',
        ),
    ]
