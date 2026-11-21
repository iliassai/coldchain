from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Dht11
from .serializers import DHT11serialize
from monitoring.views import LegacyMeasurementIngestView


@api_view(['GET'])
def Dlist(request):
    all_data = Dht11.objects.all()
    data = DHT11serialize(all_data, many=True).data
    return Response({'data': data})

Dhtviews = LegacyMeasurementIngestView
