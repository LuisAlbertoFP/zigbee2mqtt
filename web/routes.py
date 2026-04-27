from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
import importlib
import inspect

from config import MQTT_AVAIL_TOPIC, MQTT_BUTTON_TOPIC, MQTT_SET_TOPIC, MQTT_STATE_TOPIC, MQTT_SET_TEMP_TOPIC
from mqtt_service import ensure_subscriber_started, publish_button_single, publish_payload, publish_to_topic
from state import get_runtime_copy
from utils import compute_device_status, format_last_seen

bp = Blueprint('main', __name__)


@bp.before_app_request
def startup() -> None:
    ensure_subscriber_started()


def _is_ajax_request():
    """Detecta si la petición es AJAX."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _get_attack_manager():
    """Obtiene la instancia del gestor de ataques dinámicamente."""
    try:
        attacks_module = importlib.import_module('attacks')
        # Prefer the module-level singleton instance over the class itself
        instance = getattr(attacks_module, 'attack_manager', None)
        if instance is not None:
            return instance
        # Fallback: instantiate the class if only the class is available
        cls = getattr(attacks_module, 'AttackManager', None)
        return cls() if cls is not None else None
    except ImportError:
        return None


def _get_status_data():
    """Obtiene y procesa los datos de estado comunes para múltiples endpoints."""
    data = get_runtime_copy()
    attack_manager = _get_attack_manager()
    
    # Obtener estados de todos los ataques dinámicamente
    attack_states = {}
    if attack_manager:
        attack_states = attack_manager.get_all_attack_states()
    
    return {
        'data': data,
        'device_status': compute_device_status(data),
        'last_seen': format_last_seen(data['last_update_ts']),
        'events': data['events'][:12],
        'attack_states': attack_states,
    }


@bp.route('/')
def index():
    status = _get_status_data()
    data = status['data']
    
    return render_template(
        'index.html',
        app_name=current_app.config.get('APP_NAME', 'MQTT Control Pro // Hacker Dashboard'),
        set_topic=MQTT_SET_TOPIC,
        state_topic=MQTT_STATE_TOPIC,
        avail_topic=MQTT_AVAIL_TOPIC,
        button_topic=MQTT_BUTTON_TOPIC,
        broker_online=data['broker_online'],
        device_status=status['device_status'],
        last_state=data['last_state_text'],
        last_error=data['last_error'],
        last_seen=status['last_seen'],
        events=status['events'],
        attack_states=status['attack_states'],
    )


@bp.get('/api/status')
def api_status():
    status = _get_status_data()
    data = status['data']
    
    return jsonify({
        'broker_online': data['broker_online'],
        'device_status': status['device_status'],
        'last_state': data['last_state_text'],
        'last_error': data['last_error'],
        'last_seen': status['last_seen'],
        'events': status['events'],
        'set_topic': MQTT_SET_TOPIC,
        'state_topic': MQTT_STATE_TOPIC,
        'avail_topic': MQTT_AVAIL_TOPIC,
        'button_topic': MQTT_BUTTON_TOPIC,
        'attack_states': status['attack_states'],
    })


def _handle_result(action: str, ok: bool, msg: str, denied: bool) -> dict:
    """Maneja el resultado de una operación MQTT."""
    if denied:
        message = f'{action}: 🔒 ACCESO DENEGADO'
        category = 'denied'
    else:
        message = f"{action}: {'OK' if ok else 'ERROR'} - {msg}"
        category = 'ok' if ok else 'error'
    
    if not _is_ajax_request():
        flash(message, category)
    
    return {
        'success': ok and not denied,
        'message': message,
        'category': category,
        'denied': denied
    }


def _device_action(action: str, state: str):
    """Ejecuta una acción del dispositivo."""
    ok, msg, denied = publish_payload({'state': state})
    result = _handle_result(action, ok, msg, denied)
    
    if _is_ajax_request():
        return jsonify(result)
    else:
        return redirect(url_for('main.index'))


@bp.post('/toggle')
def toggle():
    return _device_action('TOGGLE', 'TOGGLE')


@bp.post('/on')
def turn_on():
    return _device_action('ON', 'ON')


@bp.post('/off')
def turn_off():
    return _device_action('OFF', 'OFF')


@bp.post('/button-single')
def button_single():
    ok, msg, denied = publish_button_single()
    result = _handle_result('BOTÓN SINGLE', ok, msg, denied)
    
    if _is_ajax_request():
        return jsonify(result)
    else:
        return redirect(url_for('main.index'))


# Rutas dinámicas para ataques
@bp.route('/attack/<attack_id>/<action>', methods=['POST'])
def attack_handler(attack_id: str, action: str):
    """Maneja todas las acciones de ataques de forma dinámica."""
    attack_manager = _get_attack_manager()
    
    if not attack_manager:
        result = {
            'success': False,
            'message': 'Sistema de ataques no disponible',
            'category': 'error'
        }
        
        if _is_ajax_request():
            return jsonify(result)
        else:
            flash(result['message'], result['category'])
            return redirect(url_for('main.index'))
    
    if action == 'start':
        started, msg = attack_manager.start_attack(attack_id)
        result = {
            'success': started,
            'message': msg,
            'category': 'ok' if started else 'warn'
        }
    elif action == 'stop':
        msg = attack_manager.stop_attack(attack_id)
        result = {
            'success': True,
            'message': msg,
            'category': 'warn'
        }
    else:
        result = {
            'success': False,
            'message': f'Acción no válida: {action}',
            'category': 'error'
        }
    
    if _is_ajax_request():
        return jsonify(result)
    else:
        flash(result['message'], result['category'])
        return redirect(url_for('main.index'))


@bp.post('/temp-calibration/set')
def temp_calibration_set():
    """Establece temperature_calibration a -30 en el sensor."""
    from attacks.attack4 import set_calibration
    set_calibration(-30)
    ok, msg, denied = publish_to_topic(MQTT_SET_TEMP_TOPIC, {'temperature_calibration': -30})
    result = _handle_result('CALIBRACIÓN TEMP -30', ok, msg, denied)
    if _is_ajax_request():
        return jsonify(result)
    return redirect(url_for('main.index'))


@bp.post('/temp-calibration/reset')
def temp_calibration_reset():
    """Resetea temperature_calibration a 0 en el sensor."""
    from attacks.attack4 import set_calibration
    set_calibration(0)
    ok, msg, denied = publish_to_topic(MQTT_SET_TEMP_TOPIC, {'temperature_calibration': 0})
    result = _handle_result('CALIBRACIÓN TEMP RESET', ok, msg, denied)
    if _is_ajax_request():
        return jsonify(result)
    return redirect(url_for('main.index'))


@bp.get('/health')
def health():
    status = _get_status_data()
    data = status['data']
    
    return {
        'ok': True,
        'broker_online': data['broker_online'],
        'device_status': status['device_status'],
        'last_state': data['last_state_text'],
        'last_error': data['last_error'],
        'attack_states': status['attack_states'],
    }
