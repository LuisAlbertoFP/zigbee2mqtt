import json
import threading
import time
from typing import Any

import paho.mqtt.client as mqtt

from config import (
    MQTT_AVAIL_TOPIC,
    MQTT_BUTTON_TOPIC,
    MQTT_HOST,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_SET_TOPIC,
    MQTT_STATE_TOPIC,
    MQTT_USERNAME,
    PUBLISH_TIMEOUT,
)
from state import get_runtime_copy, subscriber_lock, update_runtime
from utils import add_event, is_access_denied, pretty_payload


def mqtt_auth(client: mqtt.Client) -> None:
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)


def on_sub_connect(
    client: mqtt.Client,
    userdata: Any,
    flags: dict,
    reason_code: Any,
    properties: Any = None,
) -> None:
    ok = False
    try:
        ok = int(reason_code) == 0
    except Exception:
        ok = str(reason_code).lower() in ('success', '0')

    if ok:
        update_runtime(broker_online=True, last_error=None)
        add_event('ok', 'Broker MQTT conectado')
        client.subscribe(MQTT_STATE_TOPIC, qos=0)
        client.subscribe(MQTT_AVAIL_TOPIC, qos=0)
    else:
        msg = f'Conexión MQTT rechazada: {reason_code}'
        update_runtime(broker_online=False, last_error=msg)
        add_event('error', msg)


def on_sub_disconnect(
    client: mqtt.Client,
    userdata: Any,
    disconnect_flags: Any,
    reason_code: Any,
    properties: Any = None,
) -> None:
    update_runtime(broker_online=False)
    add_event('warn', 'Broker MQTT desconectado')


def on_sub_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    payload_raw = msg.payload.decode('utf-8', errors='replace')
    now = time.time()

    if msg.topic == MQTT_AVAIL_TOPIC:
        online = payload_raw.strip().lower() == 'online'
        update_runtime(device_online_hint=online, last_update_ts=now)
        add_event('info', f'Availability: {payload_raw}')
        return

    if msg.topic == MQTT_STATE_TOPIC:
        parsed: Any = payload_raw
        try:
            parsed = json.loads(payload_raw)
        except Exception:
            pass

        online_hint = True
        if isinstance(parsed, dict):
            availability = str(parsed.get('availability', '')).lower().strip()
            if availability == 'online':
                online_hint = True
            elif availability == 'offline':
                online_hint = False

        text = pretty_payload(parsed)
        update_runtime(
            last_state_payload=parsed,
            last_state_text=text,
            last_update_ts=now,
            device_online_hint=online_hint,
        )
        add_event('info', f'Estado recibido: {text}')


def subscriber_worker() -> None:
    while True:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f'web-ui-sub-{int(time.time() * 1000)}',
        )
        mqtt_auth(client)
        client.on_connect = on_sub_connect
        client.on_disconnect = on_sub_disconnect
        client.on_message = on_sub_message

        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever(retry_first_connection=True)
        except Exception as exc:
            msg = f'Suscriptor MQTT: {exc}'
            update_runtime(broker_online=False, last_error=msg)
            add_event('error', msg)
            time.sleep(3)


def ensure_subscriber_started() -> None:
    current = get_runtime_copy()
    if current['subscriber_started']:
        return

    with subscriber_lock:
        current = get_runtime_copy()
        if current['subscriber_started']:
            return

        thread = threading.Thread(target=subscriber_worker, daemon=True, name='mqtt-subscriber')
        thread.start()
        update_runtime(subscriber_started=True)
        add_event('info', 'Suscriptor MQTT iniciado')


def publish_to_topic(topic: str, payload: dict[str, Any]) -> tuple[bool, str, bool]:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f'web-ui-pub-{int(time.time() * 1000)}',
    )
    mqtt_auth(client)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception as exc:
        # Error de conexión TCP — el broker está caído
        error_msg = str(exc)
        update_runtime(last_error=error_msg, broker_online=False)
        add_event('error', f'No se pudo conectar al broker para publicar en {topic}: {error_msg}')
        return False, error_msg, is_access_denied(error_msg)

    try:
        client.loop_start()

        result = client.publish(topic, json.dumps(payload), qos=0, retain=False)
        result.wait_for_publish(timeout=PUBLISH_TIMEOUT)

        rc = result.rc
        client.loop_stop()
        client.disconnect()

        if rc == mqtt.MQTT_ERR_SUCCESS:
            update_runtime(last_error=None)
            add_event('ok', f'Publicado en {topic}: {payload}')
            return True, 'publicado', False

        error_msg = f'rc={rc}'
        update_runtime(last_error=error_msg)
        add_event('error', f'Error publicando en {topic}: {error_msg}')
        return False, error_msg, is_access_denied(error_msg)

    except Exception as exc:
        # Error de publicación — no implica que el broker esté caído
        error_msg = str(exc)
        update_runtime(last_error=error_msg)
        add_event('error', f'Excepción publicando en {topic}: {error_msg}')
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass
        return False, error_msg, is_access_denied(error_msg)


def publish_payload(payload: dict[str, Any]) -> tuple[bool, str, bool]:
    return publish_to_topic(MQTT_SET_TOPIC, payload)


def publish_button_single() -> tuple[bool, str, bool]:
    return publish_to_topic(MQTT_BUTTON_TOPIC, {'action': 'single'})
