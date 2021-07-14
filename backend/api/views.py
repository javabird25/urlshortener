from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from rest_framework.request import Request
from rest_framework.decorators import api_view

from .shorten import UnshortenError, shorten_random, unshorten


@api_view(['POST'])
def shorten_view(request: Request) -> HttpResponse:
    try:
        url = request.data['url']
    except KeyError:
        return HttpResponseBadRequest()
    slug = shorten_random(url, 6)
    response = HttpResponse(slug)
    response['Content-Type'] = 'text/plain; charset=utf-8'
    return response


@api_view(['GET'])
def unshorten_view(request: Request) -> HttpResponse:
    try:
        url = unshorten(request.query_params['slug'])
    except UnshortenError:
        return HttpResponseNotFound()
    except KeyError:
        return HttpResponseBadRequest()
    return HttpResponse(url)