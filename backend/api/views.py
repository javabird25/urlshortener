from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from rest_framework.decorators import api_view
from rest_framework.request import Request

from . import shorten


@api_view(['POST'])
def shorten_view(request: Request) -> HttpResponse:
    try:
        url = request.data['url']
    except KeyError:
        return HttpResponseBadRequest()
    try:
        slug = request.data.get('slug', shorten.generate_unique_slug(6))
    except shorten.NoFreeSlugsError:
        return HttpResponse('Random slug space is exhausted. Try shortening with a longer slug.',
                            status=409)
    try:
        shorten.shorten(slug, url)
    except shorten.ShortenDuplicateError:
        return HttpResponse('This slug is already occupied.', status=409)
    response = HttpResponse(slug)
    response['Content-Type'] = 'text/plain; charset=utf-8'
    return response


@api_view(['GET'])
def unshorten_view(request: Request) -> HttpResponse:
    try:
        url = shorten.unshorten(request.query_params['slug'])
    except shorten.UnshortenError:
        return HttpResponseNotFound()
    except KeyError:
        return HttpResponseBadRequest()
    return HttpResponse(url)
