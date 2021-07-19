from rest_framework import serializers

from . import models


class ShortUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShortUrl
        fields = ['slug', 'url']
