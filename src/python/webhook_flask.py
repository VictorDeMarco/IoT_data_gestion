
from flask import Flask, request
import csv
import os

app = Flask(__name__)
CSV_FILE = 'src/python/csv/webhook_dataset.csv'

# Crear fichero CSV si no existe
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'occupied', 'button_pressed', 'tamper_detected',
                         'battery_voltage', 'temperature_celsius', 'humidity_percent',
                         'time_since_last_event_min', 'event_count'])

@app.route('/ttn', methods=['POST'])
def ttn_webhook():
    data = request.json
    try:
        uplink = data['uplink_message']
        decoded = uplink['decoded_payload']
        timestamp = uplink['received_at']
        timestamp = timestamp.split('.')[0] + 'Z'

        # Append directo al CSV (sin recargar todo el dataset)
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                decoded.get('occupied', ''),
                decoded.get('button_pressed', ''),
                decoded.get('tamper_detected', ''),
                decoded.get('battery_voltage', ''),
                decoded.get('temperature_celsius', ''),
                decoded.get('humidity_percent', ''),
                decoded.get('time_since_last_event_min', ''),
                decoded.get('event_count', ''),
                'real'
            ])

        print("✅ Paquete recibido y almacenado")
        return "OK", 200
    except Exception as e:
        print("Error:", e)
        return "Error", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
