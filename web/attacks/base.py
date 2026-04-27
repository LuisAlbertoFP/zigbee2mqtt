import threading
import time
from abc import ABC, abstractmethod
from typing import Tuple

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
