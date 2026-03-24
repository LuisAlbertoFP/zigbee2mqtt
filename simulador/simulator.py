import json
import os
import time
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_SET_TOPIC = os.getenv("MQTT_SET_TOPIC", "zigbee2mqtt/lab_ts0001_switch/set")
MQTT_STATE_TOPIC = os.getenv("MQTT_STATE_TOPIC", "zigbee2mqtt/lab_ts0001_switch")
IEEE_ADDRESS = os.getenv("IEEE_ADDRESS", "0x0000000000000000")
MODEL = os.getenv("MODEL", "TS0001_switch_module")
FRIENDLY_NAME = os.getenv("FRIENDLY_NAME", "lab_ts0001_switch")

state = "OFF"

def publish_state(client):
    payload = {
        "friendly_name": FRIENDLY_NAME,
        "ieee_address": IEEE_ADDRESS,
        "model": MODEL,
        "state": state,
        "linkquality": 92
    }
    client.publish(MQTT_STATE_TOPIC, json.dumps(payload), qos=0, retain=True)
    print(f"[SIMULADOR] Estado publicado: {payload}")

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[SIMULADOR] Conectado al broker rc={rc}")
    print(f"[SIMULADOR] Dispositivo simulado: {MODEL}")
    print(f"[SIMULADOR] IEEE: {IEEE_ADDRESS}")
    client.subscribe(MQTT_SET_TOPIC)
    print(f"[SIMULADOR] Escuchando: {MQTT_SET_TOPIC}")
    publish_state(client)

def on_message(client, userdata, msg):
    global state

    raw = msg.payload.decode(errors="ignore").strip()
    print(f"[SIMULADOR] Mensaje recibido en {msg.topic}: {raw}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("[SIMULADOR] Payload no JSON, ignorado")
        return

    new_state = str(data.get("state", "")).upper()

    if new_state == "ON":
        state = "ON"
    elif new_state == "OFF":
        state = "OFF"
    elif new_state == "TOGGLE":
        state = "OFF" if state == "ON" else "ON"
    else:
        print("[SIMULADOR] Comando no reconocido")
        return

    print(f"[SIMULADOR] >>> ACCIÓN SIMULADA: switch {state}")
    publish_state(client)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"zigbee-sim-{int(time.time())}")
client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"[SIMULADOR] Error: {e}. Reintentando en 2 segundos...")
        time.sleep(2)