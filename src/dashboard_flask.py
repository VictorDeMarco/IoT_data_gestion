from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Leemos el CSV
    df = pd.read_csv('webhook_dataset.csv')

    # Filtramos según el parámetro de URL
    modo = request.args.get('modo', 'real')  # valor por defecto: 'real'

    if modo == 'real':
        df = df[df['estado'] == 'real']
    elif modo == 'infectado':
        df = df[df['estado'] == 'infectado']


    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

    # Preparamos los datos
    ids = df['id'].tolist()
    occupied = df['occupied'].astype(int).tolist()
    temperature = df['temperature_celsius'].tolist()
    humidity = df['humidity_percent'].tolist()
    battery = df['battery_voltage'].tolist()

    return render_template('dashboard.html',
                           ids=ids,
                           occupied=occupied,
                           temperature=temperature,
                           humidity=humidity,
                           battery=battery,
                           modo=modo)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
