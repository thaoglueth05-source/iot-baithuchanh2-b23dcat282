import json
import time
from paho.mqtt import client as mqtt_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/esp32_01/telemetry"

INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "dxrrru-xQrAhwpzRntGDQ4MwUF087rVWkYV5JSKRTGmjdt1grLPcju3tNx7m5Iw-ea8ZpTg1W9i2DF2D6S2wxg=="
INFLUX_ORG = "thaoglueth05@gmail.com"
INFLUX_BUCKET = "iot_raw"

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"Received payload: {payload}")

        if "temperature" not in payload or "humidity" not in payload:
            print("Warning: Missing required sensor fields!")
            return

        point = Point("sensor_telemetry") \
            .tag("device_id", payload.get("device_id", "esp32_01")) \
            .tag("location", "lab_room_1") \
            .field("temperature", float(payload["temperature"])) \
            .field("humidity", float(payload["humidity"])) \
            .field("distance_cm", float(payload["distance_cm"])) \
            .field("rssi", int(payload["rssi"])) \
            .field("sequence", int(payload["sequence"])) \
            .time(int(time.time()), WritePrecision.S)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print("Successfully written to InfluxDB!\n")

    except Exception as e:
        print(f"Error processing message: {e}")

def run():
    client = mqtt_client.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to topic {MQTT_TOPIC}. Listening for data...")
    client.loop_forever()

if __name__ == "__main__":
    run()