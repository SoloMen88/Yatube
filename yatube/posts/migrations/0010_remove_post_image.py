# Generated by Django 2.2.16 on 2022-04-05 18:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_post_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
    ]