import os
import json
import time
from flask import Flask, render_template, redirect, url_for, flash
import paho.mqtt.client as mqtt

app = Flask(__name__)
app.secret_key = "demo-secret"

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_SET_TOPIC = os.getenv("MQTT_SET_TOPIC", "zigbee2mqtt/lab_ts0001_switch/set")
MQTT_STATE_TOPIC = os.getenv("MQTT_STATE_TOPIC", "zigbee2mqtt/lab_ts0001_switch")


def is_access_denied(error_msg: str) -> bool:
    """
    Detecta errores típicos de permisos MQTT
    """
    error_msg = error_msg.lower()
    return any(keyword in error_msg for keyword in [
        "not authorised",
        "not authorized",
        "auth",
        "refused",
        "rc=5"
    ])


def publish_payload(payload: dict) -> tuple[bool, str, bool]:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"web-ui-{int(time.time())}")

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()

        result = client.publish(MQTT_SET_TOPIC, json.dumps(payload), qos=0, retain=False)
        result.wait_for_publish()

        client.loop_stop()
        client.disconnect()

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return True, "publicado", False

        error_msg = f"rc={result.rc}"
        return False, error_msg, is_access_denied(error_msg)

    except Exception as e:
        error_msg = str(e)
        return False, error_msg, is_access_denied(error_msg)


@app.route("/")
def index():
    return render_template("index.html", set_topic=MQTT_SET_TOPIC, state_topic=MQTT_STATE_TOPIC)


def handle_result(action: str, ok: bool, msg: str, denied: bool):
    if denied:
        flash(f"{action}: ❌ ACCESO DENEGADO")
    else:
        flash(f"{action}: {'OK' if ok else 'ERROR'} - {msg}")


@app.post("/toggle")
def toggle():
    ok, msg, denied = publish_payload({"state": "TOGGLE"})
    handle_result("TOGGLE", ok, msg, denied)
    return redirect(url_for("index"))


@app.post("/on")
def turn_on():
    ok, msg, denied = publish_payload({"state": "ON"})
    handle_result("ON", ok, msg, denied)
    return redirect(url_for("index"))


@app.post("/off")
def turn_off():
    ok, msg, denied = publish_payload({"state": "OFF"})
    handle_result("OFF", ok, msg, denied)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)