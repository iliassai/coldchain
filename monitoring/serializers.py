from rest_framework import serializers


class MeasurementIngestSerializer(serializers.Serializer):
    external_id = serializers.CharField(max_length=128, trim_whitespace=True)
    temperature = serializers.DecimalField(max_digits=6, decimal_places=2)
    humidity = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    measured_at = serializers.DateTimeField(required=False)

    def validate_external_id(self, value):
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_temperature(self, value):
        if value < -100 or value > 100:
            raise serializers.ValidationError("Temperature must be between -100 and 100 °C.")
        return value

    def validate_humidity(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Humidity must be between 0 and 100 percent.")
        return value


class LegacyMeasurementIngestSerializer(serializers.Serializer):
    temp = serializers.DecimalField(max_digits=6, decimal_places=2)
    hum = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)

    def validate_temp(self, value):
        if value < -100 or value > 100:
            raise serializers.ValidationError("Temperature must be between -100 and 100 °C.")
        return value

    def validate_hum(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Humidity must be between 0 and 100 percent.")
        return value


class MeasurementSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    sensor = serializers.UUIDField(source="sensor_id", read_only=True)
    threshold_policy = serializers.UUIDField(source="threshold_policy_id", read_only=True)
    external_id = serializers.CharField(read_only=True)
    temperature = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    humidity = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True, read_only=True)
    measured_at = serializers.DateTimeField(read_only=True)
    received_at = serializers.DateTimeField(read_only=True)


class LegacyMeasurementResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    temp = serializers.DecimalField(source="temperature", max_digits=6, decimal_places=2, read_only=True)
    hum = serializers.DecimalField(source="humidity", max_digits=5, decimal_places=2, allow_null=True, read_only=True)
    dt = serializers.DateTimeField(source="measured_at", read_only=True)
