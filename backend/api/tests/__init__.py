from django.http import HttpResponse

SHORTEN_ENDPOINT = '/api/shorten/'
EXAMPLE_DOT_COM = 'http://example.com'
SOME_DIFFERENT_URL_DOT_COM = 'http://somedifferenturl.com'
SLUG_EXAMPLE = 'my_slug'


def get_response_str(response: HttpResponse):
    return response.content.decode()
