#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// Sử dụng Public Broker  (HiveMQ)
const char* MQTT_SERVER = "broker.hivemq.com"; 
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "sensors/esp32_01/telemetry";

#define DHT_PIN    4
#define TRIG_PIN   5
#define ECHO_PIN   18
#define LED_PIN    2

DHT dht(DHT_PIN, DHT22);
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastSendTime = 0;
unsigned long sequenceNo = 0;

void connectWiFi() {
  Serial.print("Connecting WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting MQTT...");
    String clientId = "ESP32_Thao_" + String((uint32_t)ESP.getEfuseMac(), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println(" Connected!");
    } else {
      Serial.print(" Failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Retry in 2s...");
      delay(2000);
    }
  }
}

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1.0;
  return duration * 0.0343f / 2.0f;
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  dht.begin();
  
  connectWiFi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastSendTime >= 5000) { // Gửi mỗi 5 giây
    lastSendTime = now;

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    float distance = readDistanceCm();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Error: DHT read failed!");
      return;
    }

    sequenceNo++;

    char payload[512];
    snprintf(payload, sizeof(payload),
      "{\"device_id\":\"esp32_01\","
      "\"temperature\":%.2f,"
      "\"humidity\":%.2f,"
      "\"distance_cm\":%.2f,"
      "\"rssi\":%d,"
      "\"sequence\":%lu,"
      "\"timestamp\":%lu}",
      temperature, humidity, distance, WiFi.RSSI(), sequenceNo, millis() / 1000
    );

    if (mqttClient.publish(MQTT_TOPIC, payload)) {
      Serial.println("Published: " + String(payload));
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
    }
  }
}