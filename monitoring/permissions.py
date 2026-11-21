from rest_framework.permissions import BasePermission

from .authentication import SensorPrincipal
from .models import SensorCredential


class IsSensorCredential(BasePermission):
    """Allow only requests authenticated with a sensor-specific credential."""

    def has_permission(self, request, view):
        return isinstance(request.user, SensorPrincipal) and isinstance(request.auth, SensorCredential)
