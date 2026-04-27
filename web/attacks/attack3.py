from typing import Tuple

from config import ATTACK3_INTERVAL, MQTT_STATE_TOPIC
from mqtt_service import publish_to_topic
from attacks.base import BaseAttack


class Attack3(BaseAttack):
    """Ataque 3: Spam de mensajes falsos al topic de estado."""

    def __init__(self):
        super().__init__('attack3', 'ATAQUE 3', ATTACK3_INTERVAL)

    def execute_attack(self) -> Tuple[bool, str, bool]:
        return publish_to_topic(MQTT_STATE_TOPIC, {'state': 'OFF'})
