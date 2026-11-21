from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from .models import Measurement, Sensor, ThresholdPolicy


class IdempotencyConflict(APIException):
    status_code = 409
    default_detail = "This external_id was already used with a different measurement."
    default_code = "idempotency_conflict"


class ThresholdNotConfigured(APIException):
    status_code = 409
    default_detail = "No temperature threshold is configured for this refrigerator."
    default_code = "threshold_not_configured"


def _effective_policy(sensor, measured_at):
    applicable = ThresholdPolicy.objects.filter(
        effective_from__lte=measured_at,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gt=measured_at))
    specific = applicable.filter(refrigerator_id=sensor.refrigerator_id).order_by("-effective_from")
    return specific.first() or applicable.filter(refrigerator__isnull=True).order_by("-effective_from").first()


def _same_request(measurement, temperature, humidity, measured_at):
    return (
        measurement.temperature == temperature
        and measurement.humidity == humidity
        and (measured_at is None or measurement.measured_at == measured_at)
    )


def record_measurement(*, sensor_id, external_id, temperature, humidity=None, measured_at=None):
    """Persist one measurement. Replays are returned, conflicting key reuse is rejected."""
    try:
        sensor = Sensor.objects.select_related("refrigerator").get(pk=sensor_id)
    except Sensor.DoesNotExist:
        raise ValidationError("Unknown sensor.") from None
    received_time = timezone.now()
    sample_time = measured_at or received_time
    skew = timedelta(seconds=getattr(settings, "SENSOR_MAX_FUTURE_SKEW_SECONDS", 300))
    if sample_time > received_time + skew:
        raise ValidationError({"measured_at": "Measurement timestamp is too far in the future."})

    if not sensor.is_active or not sensor.refrigerator.is_active:
        raise ValidationError("Sensor or refrigerator is inactive.")

    existing = Measurement.objects.filter(sensor=sensor, external_id=external_id).first()
    if existing:
        if not _same_request(existing, temperature, humidity, measured_at):
            raise IdempotencyConflict()
        return existing, False

    policy = _effective_policy(sensor, sample_time)
    if policy is None:
        raise ThresholdNotConfigured()

    try:
        with transaction.atomic():
            # The inner savepoint lets us recover from a concurrent duplicate key
            # without leaving the surrounding transaction marked as broken.
            with transaction.atomic():
                measurement = Measurement.objects.create(
                    sensor=sensor,
                    threshold_policy=policy,
                    external_id=external_id,
                    temperature=temperature,
                    humidity=humidity,
                    measured_at=sample_time,
                )
            Sensor.objects.filter(pk=sensor.pk).filter(
                Q(last_seen_at__isnull=True) | Q(last_seen_at__lt=received_time)
            ).update(last_seen_at=received_time)
    except IntegrityError:
        existing = Measurement.objects.filter(sensor=sensor, external_id=external_id).first()
        if existing and _same_request(existing, temperature, humidity, measured_at):
            return existing, False
        if existing:
            raise IdempotencyConflict() from None
        raise

    return measurement, True
