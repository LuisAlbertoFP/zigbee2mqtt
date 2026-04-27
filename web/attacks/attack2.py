from typing import Tuple

from config import ATTACK2_INTERVAL, MQTT_SET_TOPIC
from mqtt_service import publish_to_topic
from attacks.base import BaseAttack


class Attack2(BaseAttack):
    """Ataque 2: Spam de comandos OFF al topic de control."""

    def __init__(self):
        super().__init__('attack2', 'ATAQUE 2', ATTACK2_INTERVAL)

    def execute_attack(self) -> Tuple[bool, str, bool]:
        return publish_to_topic(MQTT_SET_TOPIC, {'state': 'OFF'})
