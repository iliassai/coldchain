from django.core.management.base import BaseCommand, CommandError

from monitoring.models import Sensor, SensorCredential


class Command(BaseCommand):
    help = "Rotate a sensor credential and print the new value once for device provisioning."

    def add_arguments(self, parser):
        parser.add_argument("sensor_id")

    def handle(self, *args, **options):
        try:
            sensor = Sensor.objects.select_related("refrigerator").get(pk=options["sensor_id"])
        except Sensor.DoesNotExist:
            raise CommandError("No sensor exists with that ID.") from None
        if not sensor.is_active or not sensor.refrigerator.is_active:
            raise CommandError("Cannot issue a credential for an inactive sensor or refrigerator.")

        _, token = SensorCredential.issue(sensor)
        self.stdout.write(token)
        self.stderr.write("Store this credential securely; it cannot be displayed again.")
