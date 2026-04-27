from typing import Dict, Tuple

from attacks.base import BaseAttack
from attacks.attack2 import Attack2
from attacks.attack3 import Attack3
from attacks.attack4 import Attack4


class AttackManager:
    """Gestor centralizado de todos los ataques."""

    _instance = None
    _attacks: Dict[str, BaseAttack] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_attacks()
        return cls._instance

    def _initialize_attacks(self):
        """Inicializa todos los ataques disponibles."""
        self._attacks = {
            'attack2': Attack2(),
            'attack3': Attack3(),
            'attack4': Attack4(),
        }

    def register_attack(self, attack: BaseAttack):
        """Registra un nuevo ataque dinámicamente."""
        self._attacks[attack.attack_id] = attack

    def start_attack(self, attack_id: str) -> Tuple[bool, str]:
        """Inicia un ataque específico."""
        if attack_id not in self._attacks:
            return False, f'Ataque {attack_id} no encontrado'
        return self._attacks[attack_id].start()

    def stop_attack(self, attack_id: str) -> str:
        """Detiene un ataque específico."""
        if attack_id not in self._attacks:
            return f'Ataque {attack_id} no encontrado'
        return self._attacks[attack_id].stop()

    def get_attack_state(self, attack_id: str) -> bool:
        """Obtiene el estado de un ataque específico."""
        if attack_id not in self._attacks:
            return False
        return self._attacks[attack_id].is_running()

    def get_all_attack_states(self) -> Dict[str, bool]:
        """Obtiene el estado de todos los ataques."""
        return {
            attack_id: attack.is_running()
            for attack_id, attack in self._attacks.items()
        }

    def get_available_attacks(self) -> Dict[str, str]:
        """Obtiene la lista de ataques disponibles."""
        return {
            attack_id: attack.name
            for attack_id, attack in self._attacks.items()
        }


# Instancia global del gestor
attack_manager = AttackManager()

# Funciones de compatibilidad para el código existente
def start_attack2() -> tuple[bool, str]:
    return attack_manager.start_attack('attack2')

def stop_attack2() -> str:
    return attack_manager.stop_attack('attack2')

def start_attack3() -> tuple[bool, str]:
    return attack_manager.start_attack('attack3')

def stop_attack3() -> str:
    return attack_manager.stop_attack('attack3')
