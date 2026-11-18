from django.urls import path
from . import api, views

urlpatterns = [
    path('test/', views.test),
    path("api/get", api.Dlist, name='json'),
    path("api/post", api.Dhtviews.as_view(), name='json'),
]
