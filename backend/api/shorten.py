from django.core.exceptions import ValidationError
from .models import ShortUrl
from string import ascii_letters, digits
import random

_SYMBOLS = ascii_letters + digits


def shorten(slug: str, url: str):
    if ShortUrl.objects.filter(slug=slug).exists():
        raise ShortenDuplicateError()

    short_url = ShortUrl(slug=slug, url=url)

    try:
        short_url.full_clean()
    except ValidationError as e:
        raise ShortenBadInputError() from e

    short_url.save()


def shorten_random(url: str, desired_slug_length: int) -> str:
    if desired_slug_length < 1:
        raise ShortenError(f'invalid {desired_slug_length=}')

    slug = _generate_slug(desired_slug_length)
    try:
        shorten(slug, url)
    except ShortenDuplicateError:
        # Random slug collision, try again
        return shorten_random(url, desired_slug_length)

    return slug


def _generate_slug(length: int) -> str:
    return ''.join(random.choices(_SYMBOLS, k=length))


def unshorten(slug: str) -> str:
    try:
        return ShortUrl.objects.get(slug=slug).url
    except ShortUrl.DoesNotExist as e:
        raise UnshortenError() from e


class ShortenError(Exception):
    pass


class ShortenDuplicateError(ShortenError):
    pass


class ShortenBadInputError(ShortenError):
    pass


class UnshortenError(Exception):
    pass