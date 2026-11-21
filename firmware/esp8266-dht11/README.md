# ESP8266 DHT11 firmware

This sketch posts the existing `temp`/`hum` payload to Django's compatibility endpoint, `/api/post`. It adds the sensor credential and an idempotency key required by the backend.

## Configure

1. Copy `secrets.example.h` to `secrets.h` in this folder.
2. Set the Wi-Fi name/password, the full sensor credential, and the Django computer's LAN IP in `secrets.h`.
3. Keep `secrets.h` local; it is ignored by Git.
4. Run Django on the LAN with `python manage.py runserver 0.0.0.0:8000` and allow the ESP8266's host address in `DJANGO_ALLOWED_HOSTS`.
5. Install/select the ESP8266 Arduino core and the `DHT sensor library`, then open `esp8266-dht11.ino` in Arduino IDE.

The sample interval is 20 minutes. For short bench tests, temporarily set `SAMPLE_INTERVAL_MS` to `10000UL`. Temperature offsets are disabled by default; set `ENABLE_TEMP_TEST_OFFSETS` to `true` only while testing, then turn it off before collecting real readings.

The local example URL uses plain HTTP, so use it only on a trusted private network and do not expose the development server to the internet. The sketch retries the same pending reading and ID in RAM; a board reboot loses a pending reading that has not reached the server. HTTPS certificate validation and persistent offline buffering belong in a later deployment-hardening step.
