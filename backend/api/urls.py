from django.urls import path

from . import views

urlpatterns = [
    path('api/shorten/', views.shorten_view),
    path('api/unshorten/', views.unshorten_view),
    path('api/slug/', views.slug_view),
    path('<slug:slug>/', views.redirect_view),
    path('<slug:slug>', views.redirect_view),
]
