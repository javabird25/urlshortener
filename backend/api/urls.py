from django.urls import path

from . import views

urlpatterns = [
    path('shorten/', views.shorten_view),
    path('unshorten/', views.unshorten_view),
]
