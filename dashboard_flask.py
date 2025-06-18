from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Leemos el CSV
    df = pd.read_csv('webhook_dataset.csv')

    # Convertimos la columna timestamp a tipo datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

    # Preparamos los datos
    ids = df['id'].tolist()
    occupied = df['occupied'].astype(int).tolist()  # Convertir True/False a 1/0
    temperature = df['temperature_celsius'].tolist()
    humidity = df['humidity_percent'].tolist()
    battery = df['battery_voltage'].tolist()

    return render_template('dashboard.html',
                           ids=ids,
                           occupied=occupied,
                           temperature=temperature,
                           humidity=humidity,
                           battery=battery)

if __name__ == '__main__':
    app.run(debug=True, port=5001)


