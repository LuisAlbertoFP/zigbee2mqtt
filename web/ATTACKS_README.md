# Sistema de Ataques Automático

## Descripción

El sistema de ataques ha sido completamente refactorizado para ser **automático y extensible**. Ahora puedes agregar nuevos ataques sin modificar el archivo `routes.py`.

## Cómo Funciona

### 1. Arquitectura

- **BaseAttack**: Clase abstracta que define la estructura común de todos los ataques
- **AttackManager**: Gestor centralizado que maneja todos los ataques
- **Rutas Dinámicas**: Una sola ruta `/attack/<attack_id>/<action>` maneja todos los ataques

### 2. Rutas Automáticas

Todos los ataques usan el mismo patrón de URL:
```
POST /attack/<attack_id>/start  - Inicia el ataque
POST /attack/<attack_id>/stop   - Detiene el ataque
```

Ejemplos:
- `POST /attack/attack2/start`
- `POST /attack/attack3/stop`
- `POST /attack/attack4/start` (nuevo ataque)

## Cómo Agregar Nuevos Ataques

### Paso 1: Crear la Clase del Ataque

```python
from attacks import BaseAttack
from mqtt_service import publish_to_topic
from config import MQTT_SET_TOPIC

class AttackX(BaseAttack):
    def __init__(self):
        super().__init__(
            attack_id='attackX',      # ID único del ataque
            name='ATAQUE X - NOMBRE', # Nombre descriptivo
            interval=0.1              # Intervalo en segundos
        )
    
    def execute_attack(self):
        # Tu lógica de ataque aquí
        return publish_to_topic(MQTT_SET_TOPIC, {'state': 'OFF'})
```

### Paso 2: Registrar el Ataque

```python
from attacks import AttackManager

def register_my_attacks():
    manager = AttackManager()
    manager.register_attack(AttackX())

# Llamar en app.py o en un módulo de inicialización
register_my_attacks()
```

### Paso 3: ¡Listo!

El ataque estará disponible automáticamente en:
- `POST /attack/attackX/start`
- `POST /attack/attackX/stop`
- Estado visible en `/api/status`

## Ejemplos de Ataques

Ver `new_attacks_example.py` para ejemplos completos:

- **Attack4**: Spam de TOGGLE cada 0.5s
- **Attack5**: Spam de botones cada 0.2s  
- **Attack6**: Flood de datos falsos cada 0.05s

## Ventajas del Nuevo Sistema

✅ **Sin modificar routes.py**: Agregar ataques no requiere tocar el código de rutas
✅ **Automático**: Los ataques se registran y están disponibles inmediatamente
✅ **Consistente**: Todos los ataques siguen el mismo patrón
✅ **Extensible**: Fácil agregar nuevas funcionalidades
✅ **Mantenible**: Código más limpio y organizado
✅ **Thread-safe**: Manejo seguro de hilos para cada ataque

## API de Estado

El endpoint `/api/status` ahora incluye `attack_states` con el estado de todos los ataques:

```json
{
  "attack_states": {
    "attack2": true,
    "attack3": false,
    "attack4": true
  }
}
```

## Compatibilidad

Las funciones originales (`start_attack2`, `stop_attack2`, etc.) siguen funcionando para mantener compatibilidad con código existente.