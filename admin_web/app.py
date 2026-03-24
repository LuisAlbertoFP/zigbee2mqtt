import os
import subprocess
from flask import Flask, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "admin-secret"

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = os.getenv("MQTT_PORT", "1883")

MQTT_ADMIN_USER = os.getenv("MQTT_ADMIN_USER", "admin")
MQTT_ADMIN_PASS = os.getenv("MQTT_ADMIN_PASS", "")

MQTT_WEB_USER = os.getenv("MQTT_WEB_USER", "webui")
MQTT_WEB_PASS = os.getenv("MQTT_WEB_PASS", "webpass")
MQTT_WEB_ROLE = os.getenv("MQTT_WEB_ROLE", "webui_role")

MQTT_TOPIC_SET = os.getenv("MQTT_TOPIC_SET", "zigbee2mqtt/lab_ts0001_switch/set")
MQTT_TOPIC_STATE = os.getenv("MQTT_TOPIC_STATE", "zigbee2mqtt/lab_ts0001_switch")


def run_ctrl(args):
    cmd = [
        "mosquitto_ctrl",
        "-h", MQTT_HOST,
        "-p", MQTT_PORT,
        "-u", MQTT_ADMIN_USER,
        "-P", MQTT_ADMIN_PASS,
        "dynsec",
        *args,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            input="",  # evita bloqueos por stdin
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip(), cmd
    except FileNotFoundError as e:
        return 127, "", f"mosquitto_ctrl no encontrado: {e}", cmd


def run_checked(args, ignore_already_exists=False, ignore_not_found=False):
    rc, out, err, cmd = run_ctrl(args)

    print("\nCMD:", " ".join(cmd))
    print("RC :", rc)
    print("OUT:", out)
    print("ERR:", err)

    text = f"{out}\n{err}".lower()

    if rc == 0:
        return True, out or err or "OK"

    if ignore_already_exists and "already exists" in text:
        return True, out or err or "Ya existía"

    if ignore_not_found and ("not found" in text or "does not exist" in text):
        return True, out or err or "No existía"

    return False, out or err or f"Error rc={rc}"


def ensure_base():
    messages = []

    steps = [
        # Crear cliente SIN interacción: pasar password con -p
        (["createClient", MQTT_WEB_USER, "-p", MQTT_WEB_PASS], True, False, "Crear cliente"),
        # Reforzar/actualizar password sin interacción
        (["setClientPassword", MQTT_WEB_USER, MQTT_WEB_PASS], False, False, "Asignar contraseña"),
        (["createRole", MQTT_WEB_ROLE], True, False, "Crear rol"),
        (
            ["addRoleACL", MQTT_WEB_ROLE, "subscribeLiteral", MQTT_TOPIC_STATE, "allow", "10"],
            True,
            False,
            "Permitir subscribe al topic de estado",
        ),
        (
            ["addRoleACL", MQTT_WEB_ROLE, "publishClientReceive", MQTT_TOPIC_STATE, "allow", "10"],
            True,
            False,
            "Permitir recepción del estado",
        ),
        (
            ["addClientRole", MQTT_WEB_USER, MQTT_WEB_ROLE, "10"],
            True,
            False,
            "Asignar rol al cliente",
        ),
    ]

    for args, ignore_exists, ignore_not_found, label in steps:
        ok, msg = run_checked(
            args,
            ignore_already_exists=ignore_exists,
            ignore_not_found=ignore_not_found,
        )
        messages.append(f"{label}: {msg}")
        if not ok:
            return False, messages

    return True, messages


@app.route("/")
def index():
    return render_template(
        "index.html",
        topic_set=MQTT_TOPIC_SET,
        topic_state=MQTT_TOPIC_STATE,
        web_user=MQTT_WEB_USER,
    )


@app.post("/init")
def init():
    ok, messages = ensure_base()
    for m in messages:
        flash(m)

    flash("Inicialización completada." if ok else "Error durante la inicialización.")
    return redirect(url_for("index"))


@app.post("/secure")
def secure():
    ok, messages = ensure_base()
    for m in messages:
        flash(m)

    if not ok:
        flash("No se pudo preparar la base.")
        return redirect(url_for("index"))

    run_checked(
        ["removeRoleACL", MQTT_WEB_ROLE, "publishClientSend", MQTT_TOPIC_SET],
        ignore_not_found=True,
    )

    ok2, msg2 = run_checked(
        ["addRoleACL", MQTT_WEB_ROLE, "publishClientSend", MQTT_TOPIC_SET, "deny", "100"],
        ignore_already_exists=True,
    )
    flash(f"Modo seguro: {msg2 if ok2 else 'Error: ' + msg2}")
    return redirect(url_for("index"))


@app.post("/insecure")
def insecure():
    ok, messages = ensure_base()
    for m in messages:
        flash(m)

    if not ok:
        flash("No se pudo preparar la base.")
        return redirect(url_for("index"))

    run_checked(
        ["removeRoleACL", MQTT_WEB_ROLE, "publishClientSend", MQTT_TOPIC_SET],
        ignore_not_found=True,
    )

    ok2, msg2 = run_checked(
        ["addRoleACL", MQTT_WEB_ROLE, "publishClientSend", MQTT_TOPIC_SET, "allow", "100"],
        ignore_already_exists=True,
    )
    flash(f"Modo inseguro: {msg2 if ok2 else 'Error: ' + msg2}")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)