from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import SensorCredential


@dataclass(frozen=True)
class SensorPrincipal:
    sensor_id: object
    is_authenticated: bool = True
    is_anonymous: bool = False


class SensorCredentialAuthentication(BaseAuthentication):
    """Authenticate `Authorization: Sensor <credential-uuid>.<secret>`."""

    keyword = b"sensor"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid sensor authorization header.")

        try:
            token_id, secret = parts[1].decode("ascii").split(".", 1)
            credential = SensorCredential.objects.select_related("sensor", "sensor__refrigerator").get(pk=token_id)
        except (UnicodeDecodeError, ValueError, DjangoValidationError, SensorCredential.DoesNotExist):
            raise AuthenticationFailed("Invalid sensor credential.") from None

        if not credential.is_valid or not credential.matches(secret):
            raise AuthenticationFailed("Invalid sensor credential.")

        SensorCredential.objects.filter(pk=credential.pk).update(last_used_at=timezone.now())
        return SensorPrincipal(sensor_id=credential.sensor_id), credential

    def authenticate_header(self, request):
        return "Sensor"
