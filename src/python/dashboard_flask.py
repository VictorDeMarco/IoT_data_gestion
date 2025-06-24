from flask import Flask, render_template, request, session, redirect, url_for, flash
from user_model import db
from user_routes import user_bp
from csv_routes import csv_bp
import pandas as pd
import os
from auth_utils import login_requerido
app = Flask(__name__)
app.secret_key = 'super-secret-key'


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL', 'sqlite:///default.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


app.register_blueprint(user_bp)
app.register_blueprint(csv_bp)

from user_model import Usuario

with app.app_context():
    db.create_all()

    if not Usuario.query.filter_by(nombre='admin').first():
        admin = Usuario(nombre='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

@app.route('/')
@login_requerido
def dashboard():
    nombre_csv = session.get('csv_aplicado', 'webhook_dataset.csv')
    csv_path = os.path.join(os.path.dirname(__file__), 'csv', nombre_csv)

    if not os.path.exists(csv_path):
        flash(f'Archivo "{nombre_csv}" no encontrado, usando uno por defecto.', 'error')
        csv_path = os.path.join(os.path.dirname(__file__), 'csv', 'webhook_dataset.csv')

    df = pd.read_csv(csv_path)
    modo = request.args.get('modo', 'real')

    if modo == 'real':
        df = df[df['estado'] == 'real']
    elif modo == 'infectado':
        df = df[df['estado'] == 'infectado']

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

    return render_template('dashboard.html',
                           ids=df['id'].tolist(),
                           occupied=df['occupied'].astype(int).tolist(),
                           temperature=df['temperature_celsius'].tolist(),
                           humidity=df['humidity_percent'].tolist(),
                           battery=df['battery_voltage'].tolist(),
                           modo=modo)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
