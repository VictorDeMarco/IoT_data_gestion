"""
Webhook

Descripción: Esta es la parte principal de una página web encargada de recibir los archivos que envían los dispositivos IoT
a través de la web TTN, una vez recibidos determina si ese paquete según sus criterios es real o infectado y luego lo almacena.
Autor: Víctor De Marco Velasco
Fecha: 2025-05-19
Versión: 1.0
"""

from flask import Flask, request
import csv
import os
import traceback
app = Flask(__name__)
CSV_FILE = 'src/csv/webhook_dataset.csv'

# Crear el archivo CSV con cabecera si no existe
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'occupied', 'button_pressed', 'tamper_detected',
                         'battery_voltage', 'temperature_celsius', 'humidity_percent',
                         'time_since_last_event_min', 'event_count', 'estado'])

def evaluar_paquete(paquete_actual, paquete_anterior):
    """
    Aplica reglas heurísticas para detectar si un paquete de datos es sospechoso o no.
     Devuelve True si es infectado y una lista de razones por lo que el cree que esta infectado.
    """
    if paquete_anterior is None:
        return False, ["No hay paquete anterior para comparar"]

    sospechoso = False
    sospechas = 0
    razones = []

    # Heurística 1: si el sensor marca 'ocupado', se considera sospechoso automáticamente
    if paquete_actual['occupied'] == "True":
        sospechoso = True

    # Heurística 2: event_count debe aumentar
    if paquete_actual['event_count'] < paquete_anterior['event_count']:
        sospechoso = True
        razones.append("event_count no ha aumentado")

    # Heurística 3: temperatura fuera de rango normal
    temp = paquete_actual['temperature_celsius']
    if not (0 <= temp <= 45):
        razones.append("temperatura fuera del rango normal (0-45)")
        sospechas += 1
        if not (-10 <= temp <= 60):
            sospechoso = True
            razones.append("temperatura fuera del rango físico (-10 a 60)")

    # Heurística 4: humedad fuera de rango normal
    hum = paquete_actual['humidity_percent']
    if not (30 <= hum <= 75):
        razones.append("humedad fuera del rango normal (30-75)")
        sospechas += 1
        if not (0 <= hum <= 100):
            sospechoso = True
            razones.append("humedad fuera del rango físico (0-100)")

    # Heurística 5: caída de batería sospechosa
    delta_battery = abs(paquete_actual['battery_voltage'] - paquete_anterior['battery_voltage'])
    if delta_battery > 0.11:
        sospechas += 1
        razones.append("diferencia de batería sospechosa (>0.11V)")

    # Heurística 6: presencia detectada sin eventos recientes
    tiempo = paquete_actual['time_since_last_event_min']
    tamper = paquete_actual['tamper_detected']
    if tamper == "True" and tiempo >= 2:
        sospechoso = True
        razones.append("presencia sin evento reciente (≥2 min)")

    # Heurística final: múltiples sospechas acumuladas
    if sospechas >= 2:
        sospechoso = True
        razones.append("acumulación de sospechas")

    return sospechoso, razones

@app.route('/ttn', methods=['POST'])
def ttn_webhook():
    """
    Endpoint que recibe paquetes POST tipo LoRaWAN desde TTN o simuladores.
    Aplica heurísticas y guarda el resultado en el CSV.
    """
    data = request.json
    print("🛰️ Paquete recibido:", data)

    try:
        uplink = data['uplink_message']
        decoded = uplink['decoded_payload']
        timestamp = data.get('received_at', '').split('.')[0] + 'Z'  # Se recorta a segundos

        # Construcción del paquete actual
        nuevo = {
            'occupied': str(decoded.get('occupied', 'False')),
            'button_pressed': str(decoded.get('button_pressed', 'False')),
            'tamper_detected': str(decoded.get('tamper_detected', 'False')),
            'battery_voltage': float(decoded.get('battery_voltage', 0.0)),
            'temperature_celsius': int(decoded.get('temperature_celsius', 0)),
            'humidity_percent': int(decoded.get('humidity_percent', 0)),
            'time_since_last_event_min': int(decoded.get('time_since_last_event_min', 0)),
            'event_count': int(decoded.get('event_count', 0))
        }

        # Buscar el último paquete real para comparar
        paquete_anterior = None
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r') as f:
                rows = list(csv.DictReader(f))
                for row in reversed(rows):
                    if row.get('estado', '').lower() == 'real':
                        paquete_anterior = {
                            'occupied': str(row['occupied']),
                            'button_pressed': str(row['button_pressed']),
                            'tamper_detected': str(row['tamper_detected']),
                            'battery_voltage': float(row['battery_voltage']),
                            'temperature_celsius': float(row['temperature_celsius']),
                            'humidity_percent': float(row['humidity_percent']),
                            'time_since_last_event_min': float(row['time_since_last_event_min']),
                            'event_count': int(row['event_count'])
                        }
                        break

        # Evaluar el paquete y determinar si es sospechoso
        sospechoso, razones = evaluar_paquete(nuevo, paquete_anterior)
        estado = "infectado" if sospechoso else "real"

        # Guardar el paquete al archivo CSV
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                nuevo['occupied'],
                nuevo['button_pressed'],
                nuevo['tamper_detected'],
                nuevo['battery_voltage'],
                nuevo['temperature_celsius'],
                nuevo['humidity_percent'],
                nuevo['time_since_last_event_min'],
                nuevo['event_count'],
                estado
            ])

        print(f"✅ Paquete almacenado como: {estado}")
        if razones:
            print(" Motivos:", "; ".join(razones))

        return "OK", 200

    except Exception as e:
        traceback.print_exc()
        print("❌ Error:", e)
        return "Error", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
