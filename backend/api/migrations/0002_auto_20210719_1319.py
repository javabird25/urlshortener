# Generated by Django 3.2.5 on 2021-07-19 08:19

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shorturl',
            name='user_id',
            field=models.UUIDField(default=uuid.UUID(int=0), verbose_name='ephemeral user ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shorturl',
            name='slug',
            field=models.SlugField(primary_key=True, serialize=False, verbose_name='slug (shortened URL without http://domain/ part)'),
        ),
        migrations.AlterField(
            model_name='shorturl',
            name='url',
            field=models.URLField(verbose_name='shortened URL'),
        ),
    ]