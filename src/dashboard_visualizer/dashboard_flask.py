"""
Dashboard

Descripción: Esta es la parte principal del código encargado de mantener una página web en flask en la que poder visualizar, almacenar e infectar ficheros csv que contengan datos relacionados con dispositivos IoT
Autor: Víctor De Marco Velasco
Fecha: 2025-05-19
Versión: 1.0
"""

import pandas as pd
import os
from flask import Flask, render_template, request, session, flash
from src.dashboard_visualizer.utils.paths import CSV_FILE_BASE, CSV_DIR
from src.dashboard_visualizer.utils.user_model import db, Usuario
from src.dashboard_visualizer.routes.user_routes import user_bp
from src.dashboard_visualizer.routes.csv_routes import csv_bp
from src.dashboard_visualizer.routes.infect_routes import infect_bp
from src.dashboard_visualizer.utils.auth_utils import login_requerido


app = Flask(__name__)

# Clave secreta para gestionar sesiones de Flask
app.secret_key = 'f9a8c3086470aa19e0dddfc2c7f3e5b17c0a4d7cf6c0cb38f3a58791f0e77fc9'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL', 'sqlite:///default.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos con la app
db.init_app(app)

app.register_blueprint(user_bp)
app.register_blueprint(csv_bp)
app.register_blueprint(infect_bp)

# Crear todas las tablas y el usuario admin si no existe aún
with app.app_context():
    db.create_all()

    if not Usuario.query.filter_by(nombre='admin').first():
        admin = Usuario(nombre='admin')
        admin.set_password('admin')  # Establece la contraseña cifrada
        db.session.add(admin)
        db.session.commit()

# Inyectar el usuario actual a todas las plantillas automáticamente
@app.context_processor
def inject_user():
    usuario = None
    if 'usuario_id' in session:
        # Recuperar objeto Usuario desde la sesión
        usuario = db.session.get(Usuario, session['usuario_id'])

        # Guardar nombre de usuario en sesión si no está
        if usuario and 'nombre_usuario' not in session:
            session['nombre_usuario'] = usuario.nombre

    return dict(usuario_actual=usuario)

# Ruta principal del dashboard
@app.route('/')
@login_requerido
def dashboard():
    # Obtener el CSV activo, o por defecto el base
    nombre_csv = session.get('csv_aplicado', 'webhook_dataset.csv')

    # Determinar la ruta del archivo (global o del usuario)
    if nombre_csv == 'webhook_dataset.csv':
        csv_path = CSV_FILE_BASE
    else:
        nombre_usuario = session.get('nombre_usuario')
        csv_path = os.path.join(CSV_DIR, nombre_usuario, nombre_csv)

    # Validar si el archivo existe
    if not os.path.exists(csv_path):
        flash(f'Archivo "{nombre_csv}" no encontrado, usando uno por defecto.', 'error_dash')
        csv_path = CSV_FILE_BASE

    # Leer el CSV con pandas
    df = pd.read_csv(csv_path)

    # Modo de filtrado (real, infectado, o todos)
    modo = request.args.get('modo', 'real')
    if modo == 'real':
        df = df[df['estado'] == 'real']
    elif modo == 'infectado':
        df = df[df['estado'] == 'infectado']
    # En el caso de todos no es necesario filtrar

    # Conversión de timestamps y preparación del DataFrame
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

    # Renderizar dashboard con datos procesados para las gráficas
    return render_template('dashboard_templates/dashboard.html',
                           ids=df['id'].tolist(),
                           occupied=df['occupied'].astype(int).tolist(),
                           temperature=df['temperature_celsius'].tolist(),
                           humidity=df['humidity_percent'].tolist(),
                           battery=df['battery_voltage'].tolist(),
                           modo=modo)

@app.errorhandler(404)
@login_requerido
def page_not_found(e):
    return render_template('common_templates/error.html', error_message="Página no encontrada (404)"), 404

@app.errorhandler(500)
@login_requerido
def internal_error(e):
    return render_template('common_templates/error.html', error_message="Error interno del servidor (500)"), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
