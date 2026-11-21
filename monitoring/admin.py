from django.contrib import admin

from .models import Measurement, Refrigerator, Sensor, ThresholdPolicy


@admin.register(Refrigerator)
class RefrigeratorAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "location")


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ("name", "refrigerator", "is_active", "last_seen_at")
    list_filter = ("is_active", "refrigerator")
    search_fields = ("name", "refrigerator__name")


@admin.register(ThresholdPolicy)
class ThresholdPolicyAdmin(admin.ModelAdmin):
    list_display = ("refrigerator", "min_temperature", "max_temperature", "effective_from", "effective_to", "created_by")
    list_filter = ("refrigerator",)
    readonly_fields = ("scope_key", "created_at")

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return self.readonly_fields
        return tuple(field.name for field in obj._meta.fields if field.name != "effective_to")


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ("sensor", "temperature", "humidity", "measured_at", "received_at")
    list_filter = ("sensor__refrigerator",)
    search_fields = ("external_id", "sensor__name", "sensor__refrigerator__name")
    readonly_fields = tuple(field.name for field in Measurement._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
