from unittest.mock import patch

from parameterized import parameterized
from rest_framework.test import APITestCase

from . import SHORTEN_ENDPOINT, EXAMPLE_DOT_COM, SLUG_EXAMPLE, \
    SOME_DIFFERENT_URL_DOT_COM, get_response_str
from .. import shorten
from ..models import ShortUrl
from ..shorten import NoFreeSlugsError


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

    def test_zero_length_slug(self):
        response = self.client.post(SHORTEN_ENDPOINT, {'slug': '', 'url': EXAMPLE_DOT_COM})

        self.assertEqual(400, response.status_code)


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


class SlugGeneratorAPIEndpointTestCase(APITestCase):
    def test_status_code_is_200(self):
        response = self.client.get('/api/slug/', {'length': 6})

        self.assertEqual(200, response.status_code)

    def test_generates_slugs_of_specified_length(self):
        response = self.client.get('/api/slug/', {'length': 6})

        self.assertEqual(6, len(response.content.decode()))

    @patch('api.shorten.generate_unique_slug')
    def test_no_free_slugs(self, slug_gen_mock):
        slug_gen_mock.side_effect = shorten.NoFreeSlugsError()

        response = self.client.get('/api/slug/', {'length': 6})

        self.assertEqual(409, response.status_code)

    def test_no_length_specified(self):
        response = self.client.get('/api/slug/')

        self.assertEqual(400, response.status_code)

    @parameterized.expand([
        ('negative length', -1),
        ('zero length', 0),
        ('not a number', 'what'),
        ('float', 6.9),
    ])
    def test_bad_length(self, description, length):
        response = self.client.get('/api/slug/', {'length': str(length)})

        self.assertEqual(400, response.status_code,
                         f'failed to return a 400 response for {description}')


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
