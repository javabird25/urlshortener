from django.db import models


class ShortUrl(models.Model):
    slug = models.SlugField(verbose_name='slug (shortened URL without http://domain/ part)',
                            primary_key=True)
    url = models.URLField('shortened URL')
    user_id = models.UUIDField('ephemeral user ID')
