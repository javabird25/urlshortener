import uuid
from unittest.mock import patch

from fakeredis import FakeRedis
from parameterized import parameterized
from rest_framework.test import APITestCase

from . import SHORTEN_ENDPOINT, EXAMPLE_DOT_COM, SLUG_EXAMPLE, \
    SOME_DIFFERENT_URL_DOT_COM, get_response_str, UUID_NULL, UUID_123
from .. import shorten
from ..models import ShortUrl
from ..serializers import ShortUrlSerializer
from ..shorten import NoFreeSlugsError


class ShorteningAPITestCaseBase(APITestCase):
    def make_custom_slug_request(self):
        return self.client.post(SHORTEN_ENDPOINT,
                                {'url': EXAMPLE_DOT_COM, 'slug': SLUG_EXAMPLE})


class ShorteningAPITestCase(ShorteningAPITestCaseBase):
    def make_two_requests(self):
        custom_slug_response = self.make_custom_slug_request()
        random_slug_response = self.client.post(SHORTEN_ENDPOINT,
                                                {'url': EXAMPLE_DOT_COM})
        return custom_slug_response, random_slug_response

    def test_saves_to_db(self):
        self.make_two_requests()
        self.assertEqual(2, len(ShortUrl.objects.filter(url=EXAMPLE_DOT_COM)))
        self.assertTrue(ShortUrl.objects.filter(slug=SLUG_EXAMPLE, url=EXAMPLE_DOT_COM))

    def test_empty_request_body(self):
        response = self.client.post(SHORTEN_ENDPOINT)
        self.assertEqual(400, response.status_code)

    def test_status_code_is_200(self):
        responses = self.make_two_requests()
        self.assertTrue(all([resp.status_code == 200 for resp in responses]))

    def test_content_type(self):
        responses = self.make_two_requests()
        self.assertTrue(all([resp.headers['Content-Type'] == 'text/plain; charset=utf-8'
                             for resp in responses]))

    def test_occupied_slug(self):
        self.make_custom_slug_request()
        response = self.make_custom_slug_request()

        self.assertEqual(409, response.status_code)
        self.assertEqual('This slug is already occupied.', response.content.decode())

    def test_zero_length_slug(self):
        response = self.client.post(SHORTEN_ENDPOINT, {'slug': '', 'url': EXAMPLE_DOT_COM})

        self.assertEqual(400, response.status_code)


class ShorteningAPIAuthorizationTestCase(ShorteningAPITestCaseBase):
    def test_records_user_id_in_db(self):
        self.make_custom_slug_request()

        url_model = ShortUrl.objects.all()[0]
        self.assertEqual(self.client.session['user_id'], str(url_model.user_id))

    def test_keeps_user_id_between_requests(self):
        self.make_custom_slug_request()
        id1 = self.client.session['user_id']
        self.make_custom_slug_request()
        id2 = self.client.session['user_id']

        self.assertEqual(id1, id2)


class CustomSlugShorteningAPITestCase(APITestCase):
    def test_response_contains_slug(self):
        response = self.client.post(SHORTEN_ENDPOINT,
                                    {'url': EXAMPLE_DOT_COM, 'slug': SLUG_EXAMPLE})
        self.assertEqual(SLUG_EXAMPLE, response.content.decode())


class RandomSlugShorteningAPITestCase(APITestCase):
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


class SlugGeneratorAPITestCase(APITestCase):
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


@patch('api.redis.redis', new_callable=FakeRedis)
class UnshorteningAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        ShortUrl(url=EXAMPLE_DOT_COM, slug=SLUG_EXAMPLE, user_id=UUID_NULL).save()

    def unshorten(self, params):
        return self.client.get('/api/unshorten/', params)

    def test_unshorten(self, _):
        actual_url = get_response_str(self.unshorten({'slug': SLUG_EXAMPLE}))

        self.assertEqual(EXAMPLE_DOT_COM, actual_url)

    def test_unshorten_unknown(self, _):
        response = self.unshorten({'slug': 'not_there'})

        self.assertEqual(404, response.status_code)

    def test_slug_not_specified(self, _):
        response = self.unshorten(None)

        self.assertEqual(400, response.status_code)


class UserURLListingAPITestCase(APITestCase):
    def test_no_user_id(self):
        response = self.client.get('/api/urls/')

        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())

    def test_gives_only_users_urls(self):
        expected_user_123s_urls = [
            ShortUrl(url=EXAMPLE_DOT_COM, slug='slug1', user_id=UUID_123),
            ShortUrl(url=SOME_DIFFERENT_URL_DOT_COM, slug='slug2', user_id=UUID_123),
        ]
        for url in expected_user_123s_urls:
            url.save()
        ShortUrl(url='http://thirdurl.com', slug='slug3', user_id=uuid.uuid4()).save()

        session = self.client.session
        session['user_id'] = str(UUID_123)
        session.save()
        response = self.client.get('/api/urls/')

        self.assertEqual(ShortUrlSerializer(expected_user_123s_urls, many=True).data,
                         response.json())
