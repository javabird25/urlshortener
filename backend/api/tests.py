from unittest.mock import patch

from django.http.response import HttpResponse
from django.test.testcases import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from parameterized import parameterized

from . import shorten
from .models import ShortUrl
from .shorten import NoFreeSlugsError

SHORTEN_ENDPOINT = '/api/shorten/'
EXAMPLE_DOT_COM = 'http://example.com'
SOME_DIFFERENT_URL_DOT_COM = 'http://somedifferenturl.com'
SLUG_EXAMPLE = 'my_slug'


def get_response_str(response: HttpResponse):
    return response.content.decode()


class ShorteningAPIEndpointTestCase(APITestCase):
    def setUp(self):
        self.custom_slug_response = self.client.post(SHORTEN_ENDPOINT,
                                                     {'url': EXAMPLE_DOT_COM, 'slug': SLUG_EXAMPLE})
        self.random_slug_response = self.client.post(SHORTEN_ENDPOINT,
                                                     {'url': EXAMPLE_DOT_COM})
        self.responses = [self.custom_slug_response, self.random_slug_response]

    def test_saves_to_db(self):
        self.assertEqual(2, len(ShortUrl.objects.filter(url=EXAMPLE_DOT_COM)))
        self.assertTrue(ShortUrl.objects.filter(slug=SLUG_EXAMPLE, url=EXAMPLE_DOT_COM))

    def test_empty_request_body(self):
        response = self.client.post(SHORTEN_ENDPOINT)
        self.assertEqual(400, response.status_code)

    def test_status_code_is_200(self):
        self.assertTrue(all([resp.status_code == 200 for resp in self.responses]))

    def test_content_type(self):
        self.assertTrue(all([resp.headers['Content-Type'] == 'text/plain; charset=utf-8'
                             for resp in self.responses]))

    def test_occupied_slug(self):
        response = self.client.post(SHORTEN_ENDPOINT,
                                    {'url': SOME_DIFFERENT_URL_DOT_COM, 'slug': SLUG_EXAMPLE})
        self.assertEqual(409, response.status_code)
        self.assertEqual('This slug is already occupied.', response.content.decode())


class CustomSlugShorteningAPIEndpointTestCase(APITestCase):
    def test_response_contains_slug(self):
        response = self.client.post(SHORTEN_ENDPOINT,
                                    {'url': EXAMPLE_DOT_COM, 'slug': SLUG_EXAMPLE})
        self.assertEqual(SLUG_EXAMPLE, response.content.decode())


class RandomSlugShorteningAPIEndpointTestCase(APITestCase):
    def test_response_content(self):
        slug = self.client.post(SHORTEN_ENDPOINT, {'url': EXAMPLE_DOT_COM}).content.decode()
        self.assertEqual(6, len(slug), f'unexpected request length. Request content repr: {slug!r}')

    @patch('api.shorten.generate_unique_slug')
    def test_exhausted_random_slug_space(self, generate_unique_slug):
        generate_unique_slug.side_effect = NoFreeSlugsError()

        response = self.client.post(SHORTEN_ENDPOINT, {'url': EXAMPLE_DOT_COM})

        self.assertEqual(409, response.status_code)
        self.assertEqual('Random slug space is exhausted. Try shortening with a longer slug.',
                         response.content.decode())


class GenerateUniqueSlugTestCase(TestCase):
    def test_generate(self):
        slug = shorten.generate_unique_slug(6)

        self.assertEqual(6, len(slug))

    @patch('random.choices')
    def test_random_slug_collision(self, choices):
        colliding_slug = '123456'
        different_slug = '654321'
        ShortUrl(slug=colliding_slug, url=EXAMPLE_DOT_COM).save()
        choices.side_effect = [colliding_slug, different_slug]

        slug = shorten.generate_unique_slug(6)

        self.assertEqual(different_slug, slug)

    @patch('random.choices')
    def test_all_slugs_occupied(self, choices):
        slug = '1'
        ShortUrl(slug=slug, url=EXAMPLE_DOT_COM).save()
        choices.return_value = slug

        with self.assertRaises(NoFreeSlugsError):
            shorten.generate_unique_slug(1)

    @parameterized.expand([(0,), (-1,)])
    def test_bad_length(self, length):
        with self.assertRaises(ValueError, msg=f'failed to disallow length {length}'):
            shorten.generate_unique_slug(length)


class UnshorteningAPIEndpointTestCase(APITestCase):
    def setUp(self):
        ShortUrl(url=EXAMPLE_DOT_COM, slug=SLUG_EXAMPLE).save()
        self.response = self.unshorten({'slug': SLUG_EXAMPLE})

    def unshorten(self, params):
        return self.client.get('/api/unshorten/', params)

    def test_unshorten(self):
        actual_url = get_response_str(self.response)

        self.assertEqual(EXAMPLE_DOT_COM, actual_url)

    def test_unshorten_unknown(self):
        response = self.unshorten({'slug': 'not_there'})

        self.assertEqual(404, response.status_code)

    def test_slug_not_specified(self):
        response = self.unshorten(None)

        self.assertEqual(400, response.status_code)


class ShortenUnshortenTestCase(TestCase):
    def test_shorten_saves_to_db(self):
        shorten.shorten(SLUG_EXAMPLE, EXAMPLE_DOT_COM)

        short_url_model = ShortUrl.objects.get(slug=SLUG_EXAMPLE)
        self.assertEqual(EXAMPLE_DOT_COM, short_url_model.url)

    def test_shorten_duplicate_slug(self):
        shorten.shorten(SLUG_EXAMPLE, EXAMPLE_DOT_COM)
        with self.assertRaises(shorten.ShortenDuplicateError):
            shorten.shorten(SLUG_EXAMPLE, SOME_DIFFERENT_URL_DOT_COM)

    def test_shorten_bad_slug(self):
        with self.assertRaises(shorten.ShortenBadInputError):
            shorten.shorten(', !"', EXAMPLE_DOT_COM)

    def test_shorten_bad_url(self):
        with self.assertRaises(shorten.ShortenBadInputError):
            shorten.shorten(SLUG_EXAMPLE, 'not an URL')

    def test_unshorten_loads_from_db(self):
        ShortUrl(slug=SLUG_EXAMPLE, url=EXAMPLE_DOT_COM).save()

        long_url = shorten.unshorten(SLUG_EXAMPLE)

        self.assertEqual(EXAMPLE_DOT_COM, long_url)

    def test_unshorten_unknown_url(self):
        with self.assertRaises(shorten.UnshortenError):
            shorten.unshorten(SLUG_EXAMPLE)

    def test_shorten_unshorten(self):
        expected_long_url = EXAMPLE_DOT_COM

        shorten.shorten(SLUG_EXAMPLE, expected_long_url)
        actual_long_url = shorten.unshorten(SLUG_EXAMPLE)

        self.assertEqual(expected_long_url, actual_long_url)


class ShortUrlModelTestCase(TestCase):
    def test_create(self):
        slug = '123456'

        model = ShortUrl(slug=slug, url=EXAMPLE_DOT_COM)

        self.assertEqual('123456', model.slug)
        self.assertEqual(EXAMPLE_DOT_COM, model.url)

    def test_create_bad_url(self):
        with self.assertRaises(ValidationError):
            ShortUrl(slug='123', url='not an URL').full_clean()

    @parameterized.expand([(' ',), (',',), ("'!",)])
    def test_bad_slug_characters(self, string):
        with self.assertRaises(ValidationError, msg=f'Failed to disallow {string!r}'):
            ShortUrl(slug=string, url=EXAMPLE_DOT_COM).full_clean()

    def test_slug_too_long(self):
        with self.assertRaises(ValidationError):
            ShortUrl(slug='1' * 100, url=EXAMPLE_DOT_COM).full_clean()

    def test_url_too_long(self):
        with self.assertRaises(ValidationError):
            ShortUrl(slug='1', url='http://' + 'a' * 200 + '.com').full_clean()


class RedirectionTestCase(TestCase):
    @parameterized.expand([
        ('with trailing backslash', f'/{SLUG_EXAMPLE}/'),
        ('without trailing backslash', f'/{SLUG_EXAMPLE}'),
    ])
    def test_redirect(self, description, url):
        ShortUrl(slug=SLUG_EXAMPLE, url=EXAMPLE_DOT_COM).save()

        response = self.client.get(url)

        message = f'failed to redirect {description}'
        self.assertIn(response.status_code, {301, 302}, message)
        self.assertEqual(EXAMPLE_DOT_COM, response.headers['Location'], message)

    @parameterized.expand([
        ('with trailing backslash', f'/unknown/'),
        ('without trailing backslash', f'/unknown'),
    ])
    def test_unknown_slug(self, description, url):
        response = self.client.get(url)

        self.assertEqual(404, response.status_code, f'failed to give a 404 response {description}')
