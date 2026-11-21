#pragma once

// Copy this file to secrets.h and replace every placeholder.
// Do not commit secrets.h.
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Full one-time value printed by `python manage.py issue_sensor_credential ...`
// Format: <credential-uuid>.<secret>
const char* SENSOR_CREDENTIAL = "PASTE_SENSOR_CREDENTIAL_HERE";

// Local development only. Replace with your computer's LAN IP.
// This uses plain HTTP and must stay on a trusted private network.
const char* SERVER_URL = "http://192.168.1.50:8000/api/post";
