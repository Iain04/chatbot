# Generated by Django 4.2.4 on 2023-08-18 09:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Message',
        ),
    ]
