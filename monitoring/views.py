from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import SensorCredentialAuthentication
from .permissions import IsSensorCredential
from .serializers import (
    LegacyMeasurementIngestSerializer,
    LegacyMeasurementResponseSerializer,
    MeasurementIngestSerializer,
    MeasurementSerializer,
)
from .services import record_measurement


class MeasurementIngestView(APIView):
    authentication_classes = (SensorCredentialAuthentication,)
    permission_classes = (IsSensorCredential,)

    def post(self, request):
        serializer = MeasurementIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        measurement, created = record_measurement(
            sensor_id=request.auth.sensor_id,
            external_id=data["external_id"],
            temperature=data["temperature"],
            humidity=data.get("humidity"),
            measured_at=data.get("measured_at"),
        )
        return Response(
            MeasurementSerializer(measurement).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class LegacyMeasurementIngestView(APIView):
    """Compatibility adapter for the old temp/hum payload at /api/post."""

    authentication_classes = (SensorCredentialAuthentication,)
    permission_classes = (IsSensorCredential,)

    def post(self, request):
        external_id = request.headers.get("Idempotency-Key", "").strip()
        if not external_id:
            raise ValidationError({"Idempotency-Key": "This header is required for safe retries."})
        if len(external_id) > 128:
            raise ValidationError({"Idempotency-Key": "Must be at most 128 characters."})

        serializer = LegacyMeasurementIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        measurement, created = record_measurement(
            sensor_id=request.auth.sensor_id,
            external_id=external_id,
            temperature=data["temp"],
            humidity=data.get("hum"),
        )
        return Response(
            LegacyMeasurementResponseSerializer(measurement).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
