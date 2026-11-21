from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Measurement, Refrigerator, Sensor, SensorCredential, ThresholdPolicy


class MonitoringFactoryMixin:
    def make_sensor(self):
        fridge = Refrigerator.objects.create(name="Cold room")
        sensor = Sensor.objects.create(refrigerator=fridge, name="DHT11")
        policy = ThresholdPolicy(
            min_temperature=2,
            max_temperature=8,
            effective_from=timezone.now() - timedelta(days=1),
        )
        policy.save()
        return fridge, sensor, policy

    def authenticated_client(self, sensor):
        credential, raw_token = SensorCredential.issue(sensor)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Sensor {raw_token}")
        return client, credential


class ThresholdPolicyTests(MonitoringFactoryMixin, TestCase):
    def test_threshold_minimum_must_be_below_maximum(self):
        policy = ThresholdPolicy(min_temperature=8, max_temperature=8)

        with self.assertRaises(ValidationError):
            policy.save()

    def test_threshold_periods_for_same_scope_cannot_overlap(self):
        fridge = Refrigerator.objects.create(name="Room A")
        starts_at = timezone.now() - timedelta(days=2)
        first = ThresholdPolicy(
            refrigerator=fridge,
            min_temperature=2,
            max_temperature=8,
            effective_from=starts_at,
            effective_to=starts_at + timedelta(days=2),
        )
        first.save()
        overlapping = ThresholdPolicy(
            refrigerator=fridge,
            min_temperature=3,
            max_temperature=7,
            effective_from=starts_at + timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            overlapping.save()

    def test_threshold_policy_values_are_immutable_after_creation(self):
        policy = ThresholdPolicy(min_temperature=2, max_temperature=8)
        policy.save()
        policy.max_temperature = 9

        with self.assertRaises(ValidationError):
            policy.save()


class MeasurementIngestTests(MonitoringFactoryMixin, TestCase):
    def setUp(self):
        self.fridge, self.sensor, self.policy = self.make_sensor()
        self.client, self.credential = self.authenticated_client(self.sensor)
        self.url = "/api/v1/ingest/measurements/"
        self.payload = {
            "external_id": "sample-001",
            "temperature": "4.50",
            "humidity": "55.00",
            "measured_at": timezone.now().isoformat(),
        }

    def test_valid_reading_is_saved_with_sensor_and_effective_policy(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 201)
        measurement = Measurement.objects.get()
        self.assertEqual(measurement.sensor, self.sensor)
        self.assertEqual(measurement.threshold_policy, self.policy)
        self.assertEqual(measurement.temperature, 4.5)
        self.assertIsNotNone(measurement.received_at)
        self.sensor.refresh_from_db()
        self.assertLess(abs((self.sensor.last_seen_at - measurement.received_at).total_seconds()), 1)

    def test_delayed_measurement_updates_contact_time_not_sample_time(self):
        sample_time = timezone.now() - timedelta(hours=3)
        payload = {**self.payload, "measured_at": sample_time.isoformat()}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        measurement = Measurement.objects.get()
        self.sensor.refresh_from_db()
        self.assertEqual(measurement.measured_at, sample_time)
        self.assertGreater(self.sensor.last_seen_at, measurement.measured_at)

    def test_replay_is_idempotent_and_conflicting_reuse_is_rejected(self):
        first = self.client.post(self.url, self.payload, format="json")
        replay = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(Measurement.objects.count(), 1)

        conflict_payload = {**self.payload, "temperature": "5.00"}
        conflict = self.client.post(self.url, conflict_payload, format="json")
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(Measurement.objects.count(), 1)

    def test_missing_or_invalid_sensor_credential_is_rejected(self):
        anonymous_response = APIClient().post(self.url, self.payload, format="json")
        self.assertEqual(anonymous_response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION="Sensor not-a-valid-token")
        invalid_response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(invalid_response.status_code, 401)

    def test_revoked_credential_is_rejected(self):
        self.credential.revoked_at = timezone.now()
        self.credential.save(update_fields=("revoked_at",))

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 401)

    def test_issuing_new_credential_revokes_the_previous_one(self):
        _, new_token = SensorCredential.issue(self.sensor)

        old_token_response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(old_token_response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Sensor {new_token}")
        new_token_response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(new_token_response.status_code, 201)

    def test_malformed_uuid_credential_is_rejected_cleanly(self):
        self.client.credentials(HTTP_AUTHORIZATION="Sensor not-a-uuid.secret")

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 401)

    def test_future_timestamp_and_invalid_humidity_are_rejected(self):
        future_payload = {**self.payload, "measured_at": (timezone.now() + timedelta(hours=1)).isoformat()}
        future_response = self.client.post(self.url, future_payload, format="json")
        self.assertEqual(future_response.status_code, 400)

        humidity_payload = {**self.payload, "external_id": "sample-002", "humidity": "101"}
        humidity_response = self.client.post(self.url, humidity_payload, format="json")
        self.assertEqual(humidity_response.status_code, 400)

    def test_missing_effective_threshold_is_rejected(self):
        ThresholdPolicy.objects.all().delete()

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Measurement.objects.count(), 0)

    def test_legacy_route_uses_same_secure_idempotent_service(self):
        response = self.client.post(
            "/api/post",
            {"temp": "4.50", "hum": "55.00"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="legacy-001",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.data), {"id", "temp", "hum", "dt"})
        measurement = Measurement.objects.get()
        self.assertEqual(measurement.external_id, "legacy-001")
        self.assertEqual(measurement.sensor, self.sensor)

        replay = self.client.post(
            "/api/post",
            {"temp": "4.50", "hum": "55.00"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="legacy-001",
        )
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(Measurement.objects.count(), 1)

    def test_legacy_route_requires_idempotency_key(self):
        response = self.client.post("/api/post", {"temp": "4.50", "hum": "55.00"}, format="json")

        self.assertEqual(response.status_code, 400)

    def test_refrigerator_policy_overrides_global_policy(self):
        local_policy = ThresholdPolicy(
            refrigerator=self.fridge,
            min_temperature=1,
            max_temperature=5,
            effective_from=timezone.now() - timedelta(hours=1),
        )
        local_policy.save()
        payload = {**self.payload, "external_id": "sample-local"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Measurement.objects.get().threshold_policy, local_policy)
