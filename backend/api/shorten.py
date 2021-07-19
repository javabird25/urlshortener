import random
import uuid
from string import ascii_letters, digits

from django.core.exceptions import ValidationError

from .models import ShortUrl
from . import redis

_SYMBOLS = ascii_letters + digits


def shorten(slug: str, url: str, user_id: uuid.UUID) -> None:
    if ShortUrl.objects.filter(slug=slug).exists():
        raise ShortenDuplicateError()

    short_url = ShortUrl(slug=slug, url=url, user_id=user_id)

    try:
        short_url.full_clean()
    except ValidationError as e:
        raise ShortenBadInputError(str(e)) from e

    short_url.save()


def unshorten(slug: str) -> str:
    cached_url = redis.redis.get(slug)
    if cached_url:
        return cached_url.decode()
    return _unshorten_uncached(slug)


def _unshorten_uncached(slug: str) -> str:
    try:
        url = ShortUrl.objects.get(slug=slug).url
        redis.redis.set(slug, url)
        return url
    except ShortUrl.DoesNotExist as e:
        raise UnshortenError() from e


def generate_unique_slug(length: int) -> str:
    if length < 1:
        raise ValueError(f'invalid {length=}')
    slug = ''.join(random.choices(_SYMBOLS, k=length))
    if ShortUrl.objects.filter(slug=slug).exists():
        # Just generated an occupied slug, try again
        try:
            return generate_unique_slug(length)
        except RecursionError:
            # Slug space of this length is (almost) exhausted
            raise NoFreeSlugsError()
    return slug


class NoFreeSlugsError(Exception):
    pass


class ShortenError(Exception):
    pass


class ShortenDuplicateError(ShortenError):
    pass


class ShortenBadInputError(ShortenError):
    pass


class UnshortenError(Exception):
    pass
