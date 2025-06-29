from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, Blueprint, session
import random
from src.dashboard_visualizer.utils.auth_utils import login_requerido
import requests


infect_bp = Blueprint('infect_bp', __name__)

# Dirección del webhook (el receptor simulado del backend)
TTN_ENDPOINT = "http://172.18.0.3:5000/ttn"

# Ruta principal para manejar envío de paquetes simulados
@infect_bp.route('/infectar', methods=['GET'])
@login_requerido
def mostrar_formulario_infeccion():
    paquete = session.get('paquete_preparado')
    return render_template('infect_templates/infect.html', paquete_preparado=paquete)
@infect_bp.route('/infectar', methods=['POST'])
@login_requerido
def procesar_infeccion():
    url = 'infect_bp.mostrar_formulario_infeccion'
    if 'confirmar_paquete' in request.form:
        paquete = session.pop('paquete_preparado', None)
        if paquete:
            requests.post(TTN_ENDPOINT, json=paquete)
            flash("✅ Paquete enviado correctamente", "infectt")
        return redirect(url_for(url))

    if 'cancelar_paquete' in request.form:
        session.pop('paquete_preparado', None)
        flash("❌ Paquete cancelado", "infectf")
        return redirect(url_for(url))

    if 'enviar_aleatorio' in request.form:
        paquete = generar_paquete_aleatorio()
        session['paquete_preparado'] = paquete
        return redirect(url_for(url))

    if 'previsualizar_manual' in request.form:
        paquete = construir_paquete_desde_formulario(request.form)
        session['paquete_preparado'] = paquete
        return redirect(url_for(url))

    # Si no coincide ningún botón, redirige sin cambios
    return redirect(url_for(url))


# Construye un paquete JSON con la estructura TTN desde el formulario manual
def construir_paquete_desde_formulario(form):
    return {
        "end_device_ids": {
            "device_id": "manual-device",
            "application_ids": {"application_id": "manual-app"},
        },
        "received_at": datetime.utcnow().isoformat() + "Z",
        "uplink_message": {
            "decoded_payload": {
                "occupied": form.get('occupied') == 'on',
                "button_pressed": form.get('button_pressed') == 'on',
                "tamper_detected": form.get('tamper_detected') == 'on',
                "battery_voltage": float(form['battery_voltage']),
                "temperature_celsius": float(form['temperature_celsius']),
                "humidity_percent": float(form['humidity_percent']),
                "time_since_last_event_min": int(form['time_since_last_event_min']),
                "event_count": int(form['event_count']),
            }
        }
    }

# Genera un paquete JSON aleatorio con estructura válida para TTN
def generar_paquete_aleatorio():
    return {
        "end_device_ids": {
            "device_id": "simulated-device",
            "application_ids": {"application_id": "simulated-app"},
        },
        "received_at": datetime.utcnow().isoformat() + "Z",
        "uplink_message": {
            "decoded_payload": {
                "occupied": random.choice([True, False]),
                "button_pressed": random.choice([True, False]),
                "tamper_detected": random.choice([True, False]),
                "battery_voltage": round(random.uniform(2.0, 3.3), 2),
                "temperature_celsius": round(random.uniform(5, 45), 1),
                "humidity_percent": random.randint(10, 85),
                "time_since_last_event_min": random.randint(0, 60),
                "event_count": random.randint(1000, 20000),
            }
        }
    }
