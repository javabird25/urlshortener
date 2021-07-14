from django.db import models


class ShortUrl(models.Model):
    slug = models.SlugField(verbose_name='Slug (shortened URL without http://domain/ part)', primary_key=True)
    url = models.URLField(verbose_name='Shortened URL')
