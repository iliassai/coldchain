#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>

#include "secrets.h"

#define DHTPIN D2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

// Production sampling interval from the project requirements.
// For short bench tests, temporarily change this to 10000UL.
// const unsigned long SAMPLE_INTERVAL_MS = 10000UL;
const unsigned long SAMPLE_INTERVAL_MS = 20UL * 60UL * 1000UL;
const unsigned long RETRY_INTERVAL_MS = 15UL * 1000UL;
const float TEMP_TEST_OFFSET = 10.0;
const bool ENABLE_TEMP_TEST_OFFSETS = false;

uint32_t bootNonce = 0;
uint32_t postCount = 0;

bool hasPendingReading = false;
String pendingJson;
String pendingSampleId;

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("\nConnecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected");
  Serial.print("ESP8266 IP: ");
  Serial.println(WiFi.localIP());

  // ESP.random() is used after Wi-Fi is active to create a per-boot ID.
  bootNonce = ESP.random();
}

void createPendingReading() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT11 read failed");
    return;
  }

  postCount++;
  float postedTemperature = temperature;

  // Test-only values to exercise temperatures outside the configured range.
  if (ENABLE_TEMP_TEST_OFFSETS) {
    if (postCount % 5 == 0) {
      postedTemperature += TEMP_TEST_OFFSET;
      Serial.println("Test offset applied (+)");
    } else if (postCount % 3 == 0) {
      postedTemperature -= TEMP_TEST_OFFSET * 2;
      Serial.println("Test offset applied (-)");
    }
  }

  // Keep the counter increasing; resetting it could reuse an id in this boot.
  pendingSampleId = String(bootNonce, HEX) + "-" + String(postCount);
  pendingJson = "{\"temp\":" + String(postedTemperature, 1) +
                ",\"hum\":" + String(humidity, 1) + "}";
  hasPendingReading = true;

  Serial.println("JSON queued: " + pendingJson);
  Serial.println("Sample ID: " + pendingSampleId);
}

bool postPendingReading() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi disconnected; reconnecting");
    WiFi.reconnect();
    return false;
  }

  for (uint8_t attempt = 1; attempt <= 3; attempt++) {
    WiFiClient client;
    HTTPClient http;
    http.setTimeout(10000);

    if (!http.begin(client, SERVER_URL)) {
      Serial.println("Could not start HTTP connection");
      delay(1000 * attempt);
      continue;
    }

    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Sensor ") + SENSOR_CREDENTIAL);
    http.addHeader("Idempotency-Key", pendingSampleId);

    int httpCode = http.POST(pendingJson);
    Serial.print("HTTP status: ");
    Serial.println(httpCode);

    if (httpCode > 0) {
      Serial.println("Response: " + http.getString());
    } else {
      Serial.print("Connection error: ");
      Serial.println(http.errorToString(httpCode));
    }

    http.end();

    if (httpCode >= 200 && httpCode < 300) {
      return true;  // 201 means created; 200 means idempotent replay.
    }

    // A 4xx response needs a configuration/request fix. Keep the sample
    // pending and retry it later with the same ID.
    if (httpCode >= 400 && httpCode < 500) {
      return false;
    }

    delay(1000 * attempt);
  }

  return false;
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  connectToWiFi();
}

void loop() {
  if (!hasPendingReading) {
    createPendingReading();
    if (!hasPendingReading) {
      delay(5000);
      return;
    }
  }

  if (postPendingReading()) {
    hasPendingReading = false;
    Serial.println("Reading accepted");
    delay(SAMPLE_INTERVAL_MS);
  } else {
    Serial.println("Reading pending; retrying with the same sample ID");
    delay(RETRY_INTERVAL_MS);
  }
}
