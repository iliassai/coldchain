from django.conf import settings
from django.core.mail import send_mail
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from projet.settings import MIN_TEMP

from .models import Dht11
from .serializers import DHT11serialize

import telebot


@api_view(['GET'])
def Dlist(request):
    all_data = Dht11.objects.all()
    data = DHT11serialize(all_data, many=True).data
    return Response({'data': data})

class Dhtviews(generics.CreateAPIView):

    queryset = Dht11.objects.all()
    serializer_class = DHT11serialize

    def perform_create(self, serializer):
        data = serializer.save()
        temperature = data.temp

        if temperature is not None and (
            temperature > settings.MAX_TEMP or temperature < settings.MIN_TEMP
        ):
            message = f"Alerte ! Temperature = {temperature} °C"

            if settings.EMAIL_HOST_USER:
                send_mail(
                    subject="Alerte température",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER],
                )

            if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)
                bot.send_message(settings.TELEGRAM_CHAT_ID, message)
