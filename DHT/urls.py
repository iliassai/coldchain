from django.urls import path
from monitoring.views import MeasurementIngestView

from . import api, views

urlpatterns = [
    path('test/', views.test),
    path("api/get", api.Dlist, name='json'),
    path("api/post", api.Dhtviews.as_view(), name='json'),
    path("api/v1/ingest/measurements/", MeasurementIngestView.as_view(), name="measurement-ingest"),
]
