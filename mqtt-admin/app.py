import os
import subprocess
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

#CONFIG_PATH = "/mosquitto/mosquitto.conf"
CONFIG_PATH = "/mosquitto/mosquitto-no-auth.conf"


# =========================
# UTILIDADES
# =========================

def read_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return f.read()
    except:
        return ""


def write_config(content):
    # backup
    if os.path.exists(CONFIG_PATH):
        os.rename(CONFIG_PATH, CONFIG_PATH + ".bak")

    with open(CONFIG_PATH, "w") as f:
        f.write(content)


def restart_mqtt():
    subprocess.run(["docker", "restart", "mqtt"])


def detect_status(config):
    if "allow_anonymous true" in config:
        return "INSEGURO"
    return "SEGURO"


# =========================
# LIMPIEZA DE CONFIG
# =========================

def clean_config_lines(lines):
    """
    Elimina:
    - listeners websocket (9001)
    - protocol websockets
    - duplicados
    """
    cleaned = []
    skip_ws_block = False

    for line in lines:
        stripped = line.strip()

        # eliminar bloque websocket completo
        if stripped.startswith("listener 9001"):
            skip_ws_block = True
            continue

        if skip_ws_block:
            if stripped.startswith("listener"):
                skip_ws_block = False
            else:
                continue

        # eliminar cualquier rastro de websocket
        if "protocol websockets" in stripped:
            continue

        cleaned.append(line)

    return cleaned


# =========================
# MODOS
# =========================

def set_secure():
    lines = read_config().splitlines()
    lines = clean_config_lines(lines)

    new_lines = []
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("allow_anonymous"):
            new_lines.append("allow_anonymous false  #SEGURIDAD ACTIVADA")
        else:
            new_lines.append(line)

    # asegurar que existe la línea si no estaba
    if not any("allow_anonymous" in l for l in new_lines):
        new_lines.append("allow_anonymous false")


    # añadir websocket limpio
    new_lines.append("")
    new_lines.append("listener 9001")
    new_lines.append("protocol websockets")
    new_lines.append("allow_anonymous false #SEGURIDAD ACTIVADA")
    write_config("\n".join(new_lines))
    restart_mqtt()


def set_insecure():
    lines = read_config().splitlines()
    lines = clean_config_lines(lines)

    new_lines = []
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("allow_anonymous"):
            new_lines.append("allow_anonymous true")
        else:
            new_lines.append(line)

    # asegurar que existe
    if not any("allow_anonymous" in l for l in new_lines):
        new_lines.append("allow_anonymous true")

    # añadir websocket limpio
    new_lines.append("")
    new_lines.append("listener 9001")
    new_lines.append("protocol websockets")
    new_lines.append("allow_anonymous true")

    write_config("\n".join(new_lines))
    restart_mqtt()


# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    config = read_config()
    status = detect_status(config)
    return render_template("index.html", config=config, status=status)


@app.route("/secure")
def secure():
    set_secure()
    return redirect("/")


@app.route("/insecure")
def insecure():
    set_insecure()
    return redirect("/")


@app.route("/save", methods=["POST"])
def save():
    config = request.form["config"]
    write_config(config)
    restart_mqtt()
    return redirect("/")


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)