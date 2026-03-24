import json
import os
import time
from flask import Flask, render_template, redirect, url_for
import paho.mqtt.client as mqtt

app = Flask(__name__)

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_SET_TOPIC = os.getenv("MQTT_SET_TOPIC", "zigbee2mqtt/lab_ts0001_switch/set")
MQTT_STATE_TOPIC = os.getenv("MQTT_STATE_TOPIC", "zigbee2mqtt/lab_ts0001_switch")

def publish_payload(payload: dict) -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"web-ui-{int(time.time())}")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    result = client.publish(MQTT_SET_TOPIC, json.dumps(payload), qos=0, retain=False)
    result.wait_for_publish()
    client.loop_stop()
    client.disconnect()

@app.route("/")
def index():
    return render_template(
        "index.html",
        set_topic=MQTT_SET_TOPIC,
        state_topic=MQTT_STATE_TOPIC
    )

@app.post("/toggle")
def toggle():
    publish_payload({"state": "TOGGLE"})
    return redirect(url_for("index"))

@app.post("/on")
def turn_on():
    publish_payload({"state": "ON"})
    return redirect(url_for("index"))

@app.post("/off")
def turn_off():
    publish_payload({"state": "OFF"})
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)