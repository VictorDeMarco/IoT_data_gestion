import os
import pytz
import pandas as pd
from flask import Blueprint, session, redirect, flash, render_template, url_for, request
from auth_utils import login_requerido
from datetime import datetime
from werkzeug.utils import secure_filename

csv_bp = Blueprint('csv_bp', __name__)


CSV_DIR = os.path.join(os.path.dirname(__file__), 'csv')
zona = pytz.timezone('Europe/Madrid')
COLUMNAS_VALIDAS = [
    "timestamp",
    "occupied",
    "button_pressed",
    "tamper_detected",
    "battery_voltage",
    "temperature_celsius",
    "humidity_percent",
    "time_since_last_event_min",
    "event_count",
    "estado"
]
@csv_bp.route('/csv')
@login_requerido
def listar_csv():
    usuario_id = session.get('usuario_id')
    archivos = []

    # Archivo base compartido
    archivo_base = os.path.join(CSV_DIR, 'webhook_dataset.csv')
    if os.path.exists(archivo_base):
        archivos.append({
            'nombre': 'webhook_dataset.csv',
            'es_base': True,
            'tamano': round(os.path.getsize(archivo_base) / 1024, 2),
            'modificado': datetime.fromtimestamp(os.path.getmtime(archivo_base), tz=pytz.utc).astimezone(zona).strftime('%d/%m/%Y %H:%M')
        })
    # Archivos personales del usuario
    user_dir = os.path.join(CSV_DIR, f'user_{usuario_id}')
    if os.path.exists(user_dir):
        for nombre in os.listdir(user_dir):
            archivos.append({
                'nombre': nombre,
                'es_base': False,
                'tamano': round(os.path.getsize(user_dir) / 1024, 2),
                'modificado': datetime.fromtimestamp(os.path.getmtime(user_dir), tz=pytz.utc).astimezone(zona).strftime('%d/%m/%Y %H:%M')
            })

    return render_template('csv_list.html', archivos=archivos)

@csv_bp.route('/csv/<nombre>')
@login_requerido
def ver_csv(nombre):
    usuario_id = session.get('usuario_id')

    if nombre == 'webhook_dataset.csv':
        path_archivo = os.path.join(CSV_DIR, nombre)
    else:
        path_archivo = os.path.join(CSV_DIR, f'user_{usuario_id}', nombre)

    if not os.path.exists(path_archivo):
        return "Archivo no encontrado", 404

    df = pd.read_csv(path_archivo)
    columnas = df.columns.tolist()
    filas = df.values.tolist()

    return render_template('csv_view.html', nombre=nombre, columnas=columnas, filas=filas)

@csv_bp.route('/aplicar/<nombre>', methods=['POST'])
@login_requerido
def aplicar_csv(nombre):
    usuario_id = session.get('usuario_id')

    if nombre == 'webhook_dataset.csv':
        path_archivo = os.path.join(CSV_DIR, nombre)
    else:
        path_archivo = os.path.join(CSV_DIR, f'user_{usuario_id}', nombre)

    if os.path.exists(path_archivo):
        session['csv_aplicado'] = nombre
    else:
        flash('Archivo no encontrado.', 'error')
    return redirect(url_for('dashboard'))

@csv_bp.route('/eliminar/<nombre>', methods=['POST'])
@login_requerido
def eliminar_csv(nombre):
    usuario_id = session.get('usuario_id')

    if nombre == 'webhook_dataset.csv':
        path_archivo = os.path.join(CSV_DIR, nombre)
    else:
        path_archivo = os.path.join(CSV_DIR, f'user_{usuario_id}', nombre)
    if os.path.exists(path_archivo):
        os.remove(path_archivo)
    else:
        flash(f'Archivo "{nombre}" no encontrado.', 'error')
    return redirect(url_for('csv_bp.listar_csv'))



@csv_bp.route('/nuevo', methods=['GET'])
@login_requerido
def subir_csv_form():
    return render_template('csv_upload.html')

@csv_bp.route('/subir', methods=['POST'])
@login_requerido
def subir_csv():
    archivo = request.files.get('archivo_csv')

    if not archivo:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for('csv_bp.subir_csv_form'))

    if not archivo.filename.endswith('.csv'):
        flash("Solo se permiten archivos con extensión .csv.", "error")
        return redirect(url_for('csv_bp.subir_csv_form'))

    try:
        # Leer las columnas del archivo
        df = pd.read_csv(archivo)

        columnas_csv = df.columns.tolist()
        if columnas_csv != COLUMNAS_VALIDAS:
            flash("Formato del CSV incorrecto. Verifica el formato del archivo CSV base para ver cuál es el formato correcto.", "formato_error")
            return redirect(url_for('csv_bp.subir_csv_form'))

        # Volver a posicionar el archivo al principio para poder guardarlo
        archivo.stream.seek(0)

        nombre_seguro = secure_filename(archivo.filename)
        usuario_id = session.get('usuario_id')
        user_folder = os.path.join(CSV_DIR, f'user_{usuario_id}')
        os.makedirs(user_folder, exist_ok=True)
        destino = os.path.join(user_folder, nombre_seguro)
        archivo.save(destino)
        return redirect(url_for('csv_bp.listar_csv'))

    except Exception as e:
        flash(f"Error al procesar el archivo: {str(e)}", "error")
        return redirect(url_for('csv_bp.subir_csv_form'))
