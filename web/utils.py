import json
import time
from typing import Any

from config import STATE_TTL_SECONDS
from state import add_event as _add_event


def now_ts() -> float:
    return time.time()


def add_event(level: str, message: str) -> None:
    _add_event(level, message, now_ts())


def pretty_payload(payload: Any) -> str:
    if payload is None:
        return 'Sin datos'
    if isinstance(payload, dict):
        if 'state' in payload:
            return f"state={payload['state']}"
        return json.dumps(payload, ensure_ascii=False)
    return str(payload)


def format_last_seen(ts: float | None) -> str:
    if not ts:
        return 'Nunca'
    delta = int(now_ts() - ts)
    if delta < 2:
        return 'Justo ahora'
    if delta < 60:
        return f'Hace {delta}s'
    minutes = delta // 60
    if minutes < 60:
        return f'Hace {minutes} min'
    hours = minutes // 60
    return f'Hace {hours} h'


def is_access_denied(error_msg: str) -> bool:
    msg = (error_msg or '').lower()
    return any(token in msg for token in [
        'not authorised',
        'not authorized',
        'auth',
        'refused',
        'rc=5',
    ])


def compute_device_status(data: dict[str, Any]) -> str:
    if not data['broker_online']:
        return 'offline'

    ts = data.get('last_update_ts')
    if not ts:
        return 'unknown'

    age = now_ts() - ts
    if age > STATE_TTL_SECONDS:
        return 'unknown'

    if data.get('device_online_hint') is False:
        return 'offline'

    return 'online'
