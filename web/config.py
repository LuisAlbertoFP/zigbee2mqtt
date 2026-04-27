import os

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'demo-secret-change-me')

MQTT_HOST = os.getenv('MQTT_HOST', 'mqtt')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')

MQTT_SET_TOPIC = os.getenv('MQTT_SET_TOPIC', 'zigbee2mqtt/lab_ts0001_switch/set')
MQTT_STATE_TOPIC = os.getenv('MQTT_STATE_TOPIC', 'zigbee2mqtt/lab_ts0001_switch')
MQTT_AVAIL_TOPIC = os.getenv('MQTT_AVAIL_TOPIC', 'zigbee2mqtt/lab_ts0001_switch/availability')
MQTT_BUTTON_TOPIC = os.getenv('MQTT_BUTTON_TOPIC', 'zigbee2mqtt/0x14b457fffe075dd4')

MQTT_SET_TEMP_TOPIC = os.getenv('MQTT_SET_TEMP_TOPIC', 'zigbee2mqtt/0x8c73dafffecf8009/set')
MQTT_TEMP_STATE_TOPIC = os.getenv('MQTT_TEMP_STATE_TOPIC', 'zigbee2mqtt/0x8c73dafffecf8009')



STATE_TTL_SECONDS = int(os.getenv('STATE_TTL_SECONDS', '30'))
MAX_EVENTS = int(os.getenv('MAX_EVENTS', '50'))
PUBLISH_TIMEOUT = float(os.getenv('MQTT_PUBLISH_TIMEOUT', '5'))
ATTACK2_INTERVAL = float(os.getenv('ATTACK2_INTERVAL', '0.1'))
ATTACK3_INTERVAL = float(os.getenv('ATTACK3_INTERVAL', '0.1'))
ATTACK4_INTERVAL = float(os.getenv('ATTACK4_INTERVAL', '0.5'))
ATTACK5_INTERVAL = float(os.getenv('ATTACK5_INTERVAL', '5')) #60
ATTACK5_THREADS  = int(os.getenv('ATTACK5_THREADS', '1000'))
