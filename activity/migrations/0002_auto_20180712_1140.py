# Generated by Django 2.0.6 on 2018-07-12 03:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='action',
            field=models.CharField(max_length=25),
        ),
    ]
