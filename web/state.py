import threading
from collections import deque
from typing import Any

from config import MAX_EVENTS

state_lock = threading.Lock()
subscriber_lock = threading.Lock()
attack2_lock = threading.RLock()
attack3_lock = threading.RLock()

runtime_state: dict[str, Any] = {
    'broker_online': False,
    'device_online_hint': None,
    'last_state_payload': None,
    'last_state_text': 'Sin datos',
    'last_update_ts': None,
    'last_error': None,
    'subscriber_started': False,
    'events': deque(maxlen=MAX_EVENTS),
}

attack2_active = False
attack2_thread: threading.Thread | None = None

attack3_active = False
attack3_thread: threading.Thread | None = None


def add_event(level: str, message: str, timestamp: float) -> None:
    with state_lock:
        runtime_state['events'].appendleft({
            'ts': timestamp,
            'level': level,
            'message': message,
        })


def update_runtime(**kwargs: Any) -> None:
    with state_lock:
        runtime_state.update(kwargs)


def get_runtime_copy() -> dict[str, Any]:
    with state_lock:
        data = dict(runtime_state)
        data['events'] = list(runtime_state['events'])
        return data


def is_attack2_running() -> bool:
    with attack2_lock:
        return attack2_active


def set_attack2_running(value: bool) -> None:
    global attack2_active
    with attack2_lock:
        attack2_active = value


def get_attack2_thread() -> threading.Thread | None:
    with attack2_lock:
        return attack2_thread


def set_attack2_thread(thread: threading.Thread | None) -> None:
    global attack2_thread
    with attack2_lock:
        attack2_thread = thread
###################################


def is_attack3_running() -> bool:
    with attack3_lock:
        return attack3_active


def set_attack3_running(value: bool) -> None:
    global attack3_active
    with attack3_lock:
        attack3_active = value


def get_attack3_thread() -> threading.Thread | None:
    with attack3_lock:
        return attack3_thread


def set_attack3_thread(thread: threading.Thread | None) -> None:
    global attack3_thread
    with attack3_lock:
        attack3_thread = thread