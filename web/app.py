from flask import Flask

from config import FLASK_SECRET_KEY
from routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY
    app.config['APP_NAME'] = 'MQTT Control Pro Hacker Dashboard'
    app.register_blueprint(bp)
    
    # Registrar nuevos ataques automáticamente
    try:
        from new_attacks_example import register_new_attacks
        register_new_attacks()
    except ImportError:
        pass  # Los nuevos ataques son opcionales
    
    return app


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
