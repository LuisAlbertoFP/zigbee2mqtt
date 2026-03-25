import json
import os
import threading
import time
from collections import deque
from typing import Any

import paho.mqtt.client as mqtt
from flask import Flask, flash, jsonify, redirect, render_template, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo-secret-change-me")

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

MQTT_SET_TOPIC = os.getenv("MQTT_SET_TOPIC", "zigbee2mqtt/lab_ts0001_switch/set")
MQTT_STATE_TOPIC = os.getenv("MQTT_STATE_TOPIC", "zigbee2mqtt/lab_ts0001_switch")
MQTT_AVAIL_TOPIC = os.getenv("MQTT_AVAIL_TOPIC", "zigbee2mqtt/lab_ts0001_switch/availability")

STATE_TTL_SECONDS = int(os.getenv("STATE_TTL_SECONDS", "30"))
MAX_EVENTS = int(os.getenv("MAX_EVENTS", "50"))
PUBLISH_TIMEOUT = float(os.getenv("MQTT_PUBLISH_TIMEOUT", "5"))

MQTT_BUTTON_TOPIC = os.getenv("MQTT_BUTTON_TOPIC", "zigbee2mqtt/0x14b457fffe075dd4")


state_lock = threading.Lock()
runtime_state: dict[str, Any] = {
    "broker_online": False,
    "device_online_hint": None,
    "last_state_payload": None,
    "last_state_text": "Sin datos",
    "last_update_ts": None,
    "last_error": None,
    "subscriber_started": False,
    "events": deque(maxlen=MAX_EVENTS),
}


def mqtt_auth(client: mqtt.Client) -> None:
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)


def now_ts() -> float:
    return time.time()


def add_event(level: str, message: str) -> None:
    with state_lock:
        runtime_state["events"].appendleft(
            {
                "ts": now_ts(),
                "level": level,
                "message": message,
            }
        )


def update_runtime(**kwargs: Any) -> None:
    with state_lock:
        runtime_state.update(kwargs)


def get_runtime_copy() -> dict[str, Any]:
    with state_lock:
        data = dict(runtime_state)
        data["events"] = list(runtime_state["events"])
        return data


def pretty_payload(payload: Any) -> str:
    if payload is None:
        return "Sin datos"
    if isinstance(payload, dict):
        if "state" in payload:
            return f"state={payload['state']}"
        return json.dumps(payload, ensure_ascii=False)
    return str(payload)


def format_last_seen(ts: float | None) -> str:
    if not ts:
        return "Nunca"
    delta = int(now_ts() - ts)
    if delta < 2:
        return "Justo ahora"
    if delta < 60:
        return f"Hace {delta}s"
    minutes = delta // 60
    if minutes < 60:
        return f"Hace {minutes} min"
    hours = minutes // 60
    return f"Hace {hours} h"


def is_access_denied(error_msg: str) -> bool:
    msg = (error_msg or "").lower()
    return any(token in msg for token in [
        "not authorised",
        "not authorized",
        "auth",
        "refused",
        "rc=5",
    ])


def compute_device_status(data: dict[str, Any]) -> str:
    if not data["broker_online"]:
        return "offline"

    ts = data.get("last_update_ts")
    if not ts:
        return "unknown"

    age = now_ts() - ts
    if age > STATE_TTL_SECONDS:
        return "unknown"

    if data.get("device_online_hint") is False:
        return "offline"

    return "online"


def on_sub_connect(client: mqtt.Client, userdata: Any, flags: dict, reason_code: Any, properties: Any = None) -> None:
    ok = False
    try:
        ok = int(reason_code) == 0
    except Exception:
        ok = str(reason_code).lower() in ("success", "0")

    if ok:
        update_runtime(broker_online=True, last_error=None)
        add_event("ok", "Broker MQTT conectado")
        client.subscribe(MQTT_STATE_TOPIC, qos=0)
        client.subscribe(MQTT_AVAIL_TOPIC, qos=0)
    else:
        msg = f"Conexión MQTT rechazada: {reason_code}"
        update_runtime(broker_online=False, last_error=msg)
        add_event("error", msg)


def on_sub_disconnect(client: mqtt.Client, userdata: Any, disconnect_flags: Any, reason_code: Any, properties: Any = None) -> None:
    update_runtime(broker_online=False)
    add_event("warn", "Broker MQTT desconectado")


def on_sub_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    payload_raw = msg.payload.decode("utf-8", errors="replace")
    now = now_ts()

    if msg.topic == MQTT_AVAIL_TOPIC:
        online = payload_raw.strip().lower() == "online"
        update_runtime(
            device_online_hint=online,
            last_update_ts=now,
        )
        add_event("info", f"Availability: {payload_raw}")
        return

    if msg.topic == MQTT_STATE_TOPIC:
        parsed: Any = payload_raw
        try:
            parsed = json.loads(payload_raw)
        except Exception:
            pass

        online_hint = True
        if isinstance(parsed, dict):
            availability = str(parsed.get("availability", "")).lower().strip()
            if availability == "online":
                online_hint = True
            elif availability == "offline":
                online_hint = False

        text = pretty_payload(parsed)
        update_runtime(
            last_state_payload=parsed,
            last_state_text=text,
            last_update_ts=now,
            device_online_hint=online_hint,
        )
        add_event("info", f"Estado recibido: {text}")


def subscriber_worker() -> None:
    while True:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"web-ui-sub-{int(time.time())}")
        mqtt_auth(client)
        client.on_connect = on_sub_connect
        client.on_disconnect = on_sub_disconnect
        client.on_message = on_sub_message

        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever(retry_first_connection=True)
        except Exception as exc:
            msg = f"Suscriptor MQTT: {exc}"
            update_runtime(broker_online=False, last_error=msg)
            add_event("error", msg)
            time.sleep(3)


def ensure_subscriber_started() -> None:
    current = get_runtime_copy()
    if current["subscriber_started"]:
        return

    thread = threading.Thread(target=subscriber_worker, daemon=True)
    thread.start()
    update_runtime(subscriber_started=True)
    add_event("info", "Suscriptor MQTT iniciado")


def publish_payload(payload: dict[str, Any]) -> tuple[bool, str, bool]:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"web-ui-pub-{int(time.time())}")
    mqtt_auth(client)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()

        result = client.publish(MQTT_SET_TOPIC, json.dumps(payload), qos=0, retain=False)
        result.wait_for_publish(timeout=PUBLISH_TIMEOUT)

        rc = result.rc
        client.loop_stop()
        client.disconnect()

        if rc == mqtt.MQTT_ERR_SUCCESS:
            update_runtime(last_error=None)
            add_event("ok", f"Comando enviado: {payload}")
            return True, "publicado", False

        error_msg = f"rc={rc}"
        update_runtime(last_error=error_msg)
        add_event("error", f"Error publicando: {error_msg}")
        return False, error_msg, is_access_denied(error_msg)

    except Exception as exc:
        error_msg = str(exc)
        update_runtime(last_error=error_msg, broker_online=False)
        add_event("error", f"Excepción publicando: {error_msg}")
        return False, error_msg, is_access_denied(error_msg)


def handle_result(action: str, ok: bool, msg: str, denied: bool) -> None:
    if denied:
        flash(f"{action}: 🔒 ACCESO DENEGADO")
    else:
        flash(f"{action}: {'OK' if ok else 'ERROR'} - {msg}")


@app.before_request
def startup() -> None:
    ensure_subscriber_started()


@app.route("/")
def index():
    data = get_runtime_copy()
    device_status = compute_device_status(data)

    return render_template(
        "index.html",
        set_topic=MQTT_SET_TOPIC,
        state_topic=MQTT_STATE_TOPIC,
        avail_topic=MQTT_AVAIL_TOPIC,
        broker_online=data["broker_online"],
        device_status=device_status,
        last_state=data["last_state_text"],
        last_error=data["last_error"],
        last_seen=format_last_seen(data["last_update_ts"]),
        events=data["events"][:12],
    )


@app.get("/api/status")
def api_status():
    data = get_runtime_copy()
    device_status = compute_device_status(data)
    return jsonify(
        {
            "broker_online": data["broker_online"],
            "device_status": device_status,
            "last_state": data["last_state_text"],
            "last_error": data["last_error"],
            "last_seen": format_last_seen(data["last_update_ts"]),
            "events": data["events"][:12],
            "set_topic": MQTT_SET_TOPIC,
            "state_topic": MQTT_STATE_TOPIC,
            "avail_topic": MQTT_AVAIL_TOPIC,
        }
    )


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


@app.get("/health")
def health():
    data = get_runtime_copy()
    return {
        "ok": True,
        "broker_online": data["broker_online"],
        "device_status": compute_device_status(data),
        "last_state": data["last_state_text"],
        "last_error": data["last_error"],
    }



def publish_to_topic(topic: str, payload: dict[str, Any]) -> tuple[bool, str, bool]:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"web-ui-pub-{int(time.time())}")
    mqtt_auth(client)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()

        result = client.publish(topic, json.dumps(payload), qos=0, retain=False)
        result.wait_for_publish(timeout=PUBLISH_TIMEOUT)

        rc = result.rc
        client.loop_stop()
        client.disconnect()

        if rc == mqtt.MQTT_ERR_SUCCESS:
            update_runtime(last_error=None)
            add_event("ok", f"Publicado en {topic}: {payload}")
            return True, "publicado", False

        error_msg = f"rc={rc}"
        update_runtime(last_error=error_msg)
        add_event("error", f"Error publicando en {topic}: {error_msg}")
        return False, error_msg, is_access_denied(error_msg)

    except Exception as exc:
        error_msg = str(exc)
        update_runtime(last_error=error_msg, broker_online=False)
        add_event("error", f"Excepción publicando en {topic}: {error_msg}")
        return False, error_msg, is_access_denied(error_msg)

def publish_payload(payload: dict[str, Any]) -> tuple[bool, str, bool]:
    return publish_to_topic(MQTT_SET_TOPIC, payload)

@app.post("/button-single")
def button_single():
    ok, msg, denied = publish_to_topic(MQTT_BUTTON_TOPIC, {"action": "single"})
    handle_result("BOTÓN SINGLE", ok, msg, denied)
    return redirect(url_for("index"))

if __name__ == "__main__":
    ensure_subscriber_started()
    app.run(host="0.0.0.0", port=8080)