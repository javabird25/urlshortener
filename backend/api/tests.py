from unittest.case import skip
from unittest.mock import patch

from django.http.response import HttpResponse
from django.test.testcases import TestCase
from django.core.exceptions import ValidationError
from django.urls.conf import path
from rest_framework.test import APITestCase
from parameterized import parameterized

from .shorten import ShortenBadInputError, shorten, shorten_random, unshorten, ShortenError, ShortenDuplicateError, UnshortenError
from .models import ShortUrl

EXAMPLE_DOT_COM = 'http://example.com'
SLUG_EXAMPLE = 'my_slug'


def get_response_str(response: HttpResponse):
    return response.content.decode()


class ShorteningAPIEndpointTestCase(APITestCase):
    ...


class RandomShorteningAPIEndpointTestCase(APITestCase):
    def setUp(self):
        self.response = self.shorten_random(EXAMPLE_DOT_COM)

    def shorten_random(self, url):
        return self.client.post('/api/shorten/', {'url': url})

    def get_received_slug(self):
        return get_response_str(self.response)

    def test_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        self.assertEqual(self.response.headers['Content-Type'],
                         'text/plain; charset=utf-8')

    def test_response_content(self):
        self.assertEqual(len(self.get_received_slug()), 6,
                         msg=f'unexpected request length. Request content repr: {self.get_received_slug()!r}')

    def test_saves_to_db(self):
        slug = self.get_received_slug()
        url_model = ShortUrl.objects.get(slug=slug, url=EXAMPLE_DOT_COM)
        self.assertTrue(url_model)

    def test_empty_request_body(self):
        response = self.client.post('/api/shorten/')
        self.assertEqual(response.status_code, 400)


class UnshorteningAPIEndpointTestCase(APITestCase):
    def setUp(self):
        ShortUrl(url=EXAMPLE_DOT_COM, slug=SLUG_EXAMPLE).save()
        self.response = self.unshorten({'slug': SLUG_EXAMPLE})

    def unshorten(self, params):
        return self.client.get('/api/unshorten/', params)

    def test_unshorten(self):
        actual_url = get_response_str(self.response)

        self.assertEqual(actual_url, EXAMPLE_DOT_COM)

    def test_unshorten_unknown(self):
        response = self.unshorten({'slug': 'not_there'})

        self.assertEqual(response.status_code, 404)

    def test_slug_not_specified(self):
        response = self.unshorten(None)

        self.assertEqual(response.status_code, 400)


class ShortenUnshortenTestCase(TestCase):
    def test_shorten_saves_to_db(self):
        shorten(SLUG_EXAMPLE, EXAMPLE_DOT_COM)

        short_url_model = ShortUrl.objects.get(slug=SLUG_EXAMPLE)
        self.assertEqual(short_url_model.url, EXAMPLE_DOT_COM)

    def test_shorten_duplicate_slug(self):
        shorten(SLUG_EXAMPLE, EXAMPLE_DOT_COM)
        with self.assertRaises(ShortenDuplicateError):
            shorten(SLUG_EXAMPLE, 'http://somedifferenturl.com')

    def test_shorten_bad_slug(self):
        with self.assertRaises(ShortenBadInputError):
            shorten(', !"', EXAMPLE_DOT_COM)

    def test_shorten_bad_url(self):
        with self.assertRaises(ShortenBadInputError):
            shorten(SLUG_EXAMPLE, 'not an URL')

    def test_unshorten_loads_from_db(self):
        ShortUrl(slug=SLUG_EXAMPLE, url=EXAMPLE_DOT_COM).save()

        long_url = unshorten(SLUG_EXAMPLE)

        self.assertEqual(long_url, EXAMPLE_DOT_COM)

    def test_unshorten_unknown_url(self):
        with self.assertRaises(UnshortenError):
            unshorten(SLUG_EXAMPLE)

    def test_shorten_unshorten(self):
        expected_long_url = EXAMPLE_DOT_COM

        shorten(SLUG_EXAMPLE, expected_long_url)
        actual_long_url = unshorten(SLUG_EXAMPLE)

        self.assertEqual(actual_long_url, expected_long_url)


class ShortenRandomTestCase(TestCase):
    @patch('api.shorten.shorten')
    def test_delegates_to_shorten(self, shorten_mock):
        slug = shorten_random(EXAMPLE_DOT_COM, 6)

        shorten_mock.assert_called_with(slug, EXAMPLE_DOT_COM)

    def test_short_link_length(self):
        links = [shorten_random(EXAMPLE_DOT_COM, 5),
                 shorten_random(EXAMPLE_DOT_COM, 6)]

        self.assertEqual([len(l) for l in links], [5, 6])

    @parameterized.expand([(0,), (-1,), (51,)])
    def test_bad_length(self, length):
        with self.assertRaises(ShortenError, msg=f'failed to disallow length {length}'):
            shorten_random(EXAMPLE_DOT_COM, length)

    @patch('random.choices')
    def test_random_slug_collision(self, choices):
        colliding_slug = '123456'
        different_slug = '654321'
        ShortUrl(slug=colliding_slug, url=EXAMPLE_DOT_COM).save()
        choices.side_effect = [colliding_slug, different_slug]

        slug = shorten_random('http://differenturl.com', 6)

        self.assertEqual(slug, different_slug)


class ShortUrlModelTestCase(TestCase):
    def test_create(self):
        slug = '123456'

        model = ShortUrl(slug=slug, url=EXAMPLE_DOT_COM)

        self.assertEqual(model.slug, '123456')
        self.assertEqual(model.url, EXAMPLE_DOT_COM)

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
