import secrets
import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone


class Refrigerator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Sensor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refrigerator = models.ForeignKey(Refrigerator, on_delete=models.PROTECT, related_name="sensors")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("refrigerator__name", "name")
        constraints = [
            models.UniqueConstraint(fields=("refrigerator", "name"), name="unique_sensor_name_per_fridge"),
        ]

    def __str__(self):
        return f"{self.refrigerator}: {self.name}"


class SensorCredential(models.Model):
    """A revocable device credential. The raw secret is returned only by issue()."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sensor = models.ForeignKey(Sensor, on_delete=models.PROTECT, related_name="credentials")
    secret_hash = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, sensor):
        secret = secrets.token_urlsafe(32)
        with transaction.atomic():
            cls.objects.filter(sensor=sensor, revoked_at__isnull=True).update(revoked_at=timezone.now())
            credential = cls.objects.create(sensor=sensor, secret_hash=make_password(secret))
        return credential, f"{credential.pk}.{secret}"

    def matches(self, secret):
        return check_password(secret, self.secret_hash)

    @property
    def is_valid(self):
        return self.revoked_at is None and self.sensor.is_active and self.sensor.refrigerator.is_active

    def __str__(self):
        return f"Credential for {self.sensor}"


class ThresholdPolicy(models.Model):
    """An immutable-in-practice, effective-dated global or refrigerator policy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refrigerator = models.ForeignKey(
        Refrigerator,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="threshold_policies",
    )
    min_temperature = models.DecimalField(max_digits=6, decimal_places=2)
    max_temperature = models.DecimalField(max_digits=6, decimal_places=2)
    effective_from = models.DateTimeField(default=timezone.now)
    effective_to = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_threshold_policies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # A stable non-null scope key permits one open-ended policy per scope,
    # including the global scope, on both SQLite and PostgreSQL.
    scope_key = models.CharField(max_length=64, editable=False, db_index=True)

    class Meta:
        ordering = ("-effective_from",)
        constraints = [
            models.CheckConstraint(
                condition=Q(min_temperature__lt=F("max_temperature")),
                name="threshold_min_below_max",
            ),
            models.CheckConstraint(
                condition=Q(effective_to__isnull=True) | Q(effective_to__gt=F("effective_from")),
                name="threshold_period_positive",
            ),
            models.UniqueConstraint(
                fields=("scope_key",),
                condition=Q(effective_to__isnull=True),
                name="one_open_threshold_policy_per_scope",
            ),
        ]

    def clean(self):
        super().clean()
        self.scope_key = f"refrigerator:{self.refrigerator_id}" if self.refrigerator_id else "global"
        if self.min_temperature is not None and self.max_temperature is not None:
            if self.min_temperature >= self.max_temperature:
                raise ValidationError({"max_temperature": "Must be greater than min_temperature."})
        if self.effective_to and self.effective_from and self.effective_to <= self.effective_from:
            raise ValidationError({"effective_to": "Must be later than effective_from."})
        if not self.effective_from:
            return

        overlapping = ThresholdPolicy.objects.filter(
            scope_key=self.scope_key,
            effective_from__lt=self.effective_to,
        ) if self.effective_to else ThresholdPolicy.objects.filter(scope_key=self.scope_key)
        overlapping = overlapping.filter(Q(effective_to__isnull=True) | Q(effective_to__gt=self.effective_from))
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError("Threshold policy periods for the same scope cannot overlap.")

    def save(self, *args, **kwargs):
        self.scope_key = f"refrigerator:{self.refrigerator_id}" if self.refrigerator_id else "global"
        if self.pk:
            original = ThresholdPolicy.objects.filter(pk=self.pk).first()
            if original and any(
                getattr(original, field) != getattr(self, field)
                for field in ("refrigerator_id", "min_temperature", "max_temperature", "effective_from", "created_by_id")
            ):
                raise ValidationError("Threshold policy details are immutable; create a new effective-dated policy.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        scope = self.refrigerator or "Global"
        return f"{scope}: {self.min_temperature}–{self.max_temperature} °C"


class Measurement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sensor = models.ForeignKey(Sensor, on_delete=models.PROTECT, related_name="measurements")
    threshold_policy = models.ForeignKey(ThresholdPolicy, on_delete=models.PROTECT, related_name="measurements")
    external_id = models.CharField(max_length=128)
    temperature = models.DecimalField(max_digits=6, decimal_places=2)
    humidity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    measured_at = models.DateTimeField(default=timezone.now)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-measured_at", "-received_at")
        constraints = [
            models.UniqueConstraint(fields=("sensor", "external_id"), name="unique_measurement_external_id_per_sensor"),
            models.CheckConstraint(
                condition=Q(temperature__gte=-100) & Q(temperature__lte=100),
                name="measurement_temperature_reasonable",
            ),
            models.CheckConstraint(
                condition=Q(humidity__isnull=True) | (Q(humidity__gte=0) & Q(humidity__lte=100)),
                name="measurement_humidity_percentage",
            ),
        ]

    def __str__(self):
        return f"{self.sensor} {self.temperature} °C at {self.measured_at.isoformat()}"
