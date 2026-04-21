#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <Wire.h>
#include <BH1750.h>
#include "DHT.h"

// --- KONFIGURASI ---
const char* ssid = "WIFI_NAME";
const char* password = "PASSWORD";
const char* serverName = "LOCAL_HOST"; 

#define DHTPIN D4
#define DHTTYPE DHT22
#define RELAY_PUMP D7
#define RELAY_LAMP D5
#define RELAY_FAN  D6

DHT dht(DHTPIN, DHTTYPE);
BH1750 lightMeter;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PUMP, OUTPUT);
  pinMode(RELAY_LAMP, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);

  // Awal MATI (Mode H)
  digitalWrite(RELAY_PUMP, LOW);
  digitalWrite(RELAY_LAMP, LOW);
  digitalWrite(RELAY_FAN, LOW);

  Wire.begin(D2, D1); 
  lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
  dht.begin();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Connected!");
}

void loop() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  float l = lightMeter.readLightLevel();
  int soilPercent = map(analogRead(A0), 1023, 200, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100);

  if (isnan(t) || isnan(h)) return;

  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    
    // Tunggu respon AI lebih lama (15 detik)
    http.setTimeout(15000); 
    
    if (http.begin(client, serverName)) {
      http.addHeader("Content-Type", "application/json");
      String json = "{\"suhu\":" + String(t) + ",\"hum\":" + String(h) + 
                    ",\"soil\":" + String(soilPercent) + ",\"lux\":" + String(l) + "}";

      int httpCode = http.POST(json);

      if (httpCode == HTTP_CODE_OK) {
        String payload = http.getString();
        Serial.println("Response: " + payload);

        // Eksekusi Relay (Cek string tanpa spasi)
        digitalWrite(RELAY_PUMP, (payload.indexOf("\"pump\":\"ON\"") != -1) ? HIGH : LOW);
        digitalWrite(RELAY_LAMP, (payload.indexOf("\"lamp\":\"ON\"") != -1) ? HIGH : LOW);
        digitalWrite(RELAY_FAN,  (payload.indexOf("\"fan\":\"ON\"")  != -1) ? HIGH : LOW);
      } else {
        Serial.printf("Error: %s\n", http.errorToString(httpCode).c_str());
      }
      http.end();
    }
  }
  // Ambil data tiap 10 detik agar tidak overload
  delay(10000); 
}