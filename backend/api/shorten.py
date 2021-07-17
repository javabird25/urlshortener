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
        raise ShortenBadInputError(str(e)) from e

    short_url.save()


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
