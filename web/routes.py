from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, url_for

from attacks import start_attack2, stop_attack2
from config import MQTT_AVAIL_TOPIC, MQTT_BUTTON_TOPIC, MQTT_SET_TOPIC, MQTT_STATE_TOPIC
from mqtt_service import ensure_subscriber_started, publish_button_single, publish_payload
from state import get_runtime_copy, is_attack2_running
from utils import compute_device_status, format_last_seen

bp = Blueprint('main', __name__)


@bp.before_app_request
def startup() -> None:
    ensure_subscriber_started()


@bp.route('/')
def index():
    data = get_runtime_copy()
    device_status = compute_device_status(data)

    return render_template(
        'index.html',
        app_name=current_app.config.get('APP_NAME', 'MQTT Control Pro // Hacker Dashboard'),
        set_topic=MQTT_SET_TOPIC,
        state_topic=MQTT_STATE_TOPIC,
        avail_topic=MQTT_AVAIL_TOPIC,
        button_topic=MQTT_BUTTON_TOPIC,
        broker_online=data['broker_online'],
        device_status=device_status,
        last_state=data['last_state_text'],
        last_error=data['last_error'],
        last_seen=format_last_seen(data['last_update_ts']),
        events=data['events'][:12],
        attack2_active=is_attack2_running(),
    )


@bp.get('/api/status')
def api_status():
    data = get_runtime_copy()
    device_status = compute_device_status(data)
    return jsonify(
        {
            'broker_online': data['broker_online'],
            'device_status': device_status,
            'last_state': data['last_state_text'],
            'last_error': data['last_error'],
            'last_seen': format_last_seen(data['last_update_ts']),
            'events': data['events'][:12],
            'set_topic': MQTT_SET_TOPIC,
            'state_topic': MQTT_STATE_TOPIC,
            'avail_topic': MQTT_AVAIL_TOPIC,
            'button_topic': MQTT_BUTTON_TOPIC,
            'attack2_active': is_attack2_running(),
        }
    )


def handle_result(action: str, ok: bool, msg: str, denied: bool) -> None:
    if denied:
        flash(f'{action}: 🔒 ACCESO DENEGADO', 'denied')
    else:
        flash(f"{action}: {'OK' if ok else 'ERROR'} - {msg}", 'ok' if ok else 'error')


@bp.post('/toggle')
def toggle():
    ok, msg, denied = publish_payload({'state': 'TOGGLE'})
    handle_result('TOGGLE', ok, msg, denied)
    return redirect(url_for('main.index'))


@bp.post('/on')
def turn_on():
    ok, msg, denied = publish_payload({'state': 'ON'})
    handle_result('ON', ok, msg, denied)
    return redirect(url_for('main.index'))


@bp.post('/off')
def turn_off():
    ok, msg, denied = publish_payload({'state': 'OFF'})
    handle_result('OFF', ok, msg, denied)
    return redirect(url_for('main.index'))


@bp.post('/button-single')
def button_single():
    ok, msg, denied = publish_button_single()
    handle_result('BOTÓN SINGLE', ok, msg, denied)
    return redirect(url_for('main.index'))


@bp.post('/attack2/start')
def attack2_start():
    started, msg = start_attack2()
    flash(msg, 'ok' if started else 'warn')
    return redirect(url_for('main.index'))


@bp.post('/attack2/stop')
def attack2_stop():
    flash(stop_attack2(), 'warn')
    return redirect(url_for('main.index'))


@bp.get('/health')
def health():
    data = get_runtime_copy()
    return {
        'ok': True,
        'broker_online': data['broker_online'],
        'device_status': compute_device_status(data),
        'last_state': data['last_state_text'],
        'last_error': data['last_error'],
        'attack2_active': is_attack2_running(),
    }
