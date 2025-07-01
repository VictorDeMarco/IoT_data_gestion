import os
import pytz
import pandas as pd
from flask import Blueprint, session, redirect, flash, render_template, url_for, request, send_from_directory
from datetime import datetime
from werkzeug.utils import secure_filename
from src.dashboard_visualizer.utils.auth_utils import login_requerido
from src.webhook_receptor.webhook_flask import evaluar_paquete
from src.dashboard_visualizer.utils.paths import CSV_FILE_BASE, CSV_DIR

csv_bp = Blueprint('csv_bp', __name__)

zona = pytz.timezone('Europe/Madrid')

COLUMNAS_VALIDAS = [
    "timestamp", "occupied", "button_pressed", "tamper_detected",
    "battery_voltage", "temperature_celsius", "humidity_percent",
    "time_since_last_event_min", "event_count", "estado"
]
nombre_dataset = 'webhook_dataset.csv'

# Ruta para listar todos los archivos CSV disponibles para el usuario
@csv_bp.route('/csv')
@login_requerido
def listar_csv():
    nombre_usuario = session.get('nombre_usuario')
    if not nombre_usuario:
        return "Nombre de usuario no encontrado en sesión", 403

    archivos = []

    # Añadir el archivo base a la lista
    if os.path.exists(CSV_FILE_BASE):
        archivos.append({
            'nombre': nombre_dataset,
            'es_base': True,
            'tamano': round(os.path.getsize(CSV_FILE_BASE) / 1024, 2),
            'modificado': datetime.fromtimestamp(os.path.getmtime(CSV_FILE_BASE), tz=pytz.utc).astimezone(zona).strftime('%d/%m/%Y %H:%M')
        })

    # Añadir los archivos personales de cada usuario a la lista
    user_dir = os.path.join(CSV_DIR, nombre_usuario)
    if os.path.exists(user_dir):
        for nombre in os.listdir(user_dir):
            archivos.append({
                'nombre': nombre,
                'es_base': False,
                'tamano': round(os.path.getsize(user_dir) / 1024, 2),
                'modificado': datetime.fromtimestamp(os.path.getmtime(user_dir), tz=pytz.utc).astimezone(zona).strftime('%d/%m/%Y %H:%M')
            })

    return render_template('csv_templates/csv_list.html', archivos=archivos)

# Ruta para ver el contenido de un CSV específico
@csv_bp.route('/csv/<nombre>')
@login_requerido
def ver_csv(nombre):
    nombre_usuario = session.get('nombre_usuario')

    # Determinar si es el archivo base o del usuario
    if nombre == nombre_dataset:
        path_archivo = os.path.join(CSV_DIR, nombre)
    else:
        path_archivo = os.path.join(CSV_DIR, nombre_usuario, nombre)

    if not os.path.exists(path_archivo):
        return "Archivo no encontrado", 404

    # Leer y mostrar contenido
    df = pd.read_csv(path_archivo)
    columnas = df.columns.tolist()
    filas = df.values.tolist()

    return render_template('csv_templates/csv_view.html', nombre=nombre, columnas=columnas, filas=filas)

# Ruta para aplicar un CSV como fuente de datos activa para el dashboard
@csv_bp.route('/aplicar/<nombre>', methods=['POST'])
@login_requerido
def aplicar_csv(nombre):
    nombre_usuario = session.get('nombre_usuario')

    if nombre == nombre_dataset:
        path_archivo = os.path.join(CSV_DIR, nombre)
    else:
        path_archivo = os.path.join(CSV_DIR, nombre_usuario, nombre)

    if os.path.exists(path_archivo):
        session['csv_aplicado'] = nombre  # Guardar el nombre del CSV activo
    else:
        flash('Archivo no encontrado.', 'error')

    return redirect(url_for('dashboard'))

# Ruta para eliminar un archivo CSV del sistema
@csv_bp.route('/eliminar/<nombre>', methods=['POST'])
@login_requerido
def eliminar_csv(nombre):
    nombre_usuario = session.get('nombre_usuario')

    if nombre == nombre_dataset:
        flash(f'"{nombre}" Es el archivo base y no puede ser eliminado.', 'error')
        return redirect(url_for('csv_bp.listar_csv'))
    else:
        path_archivo = os.path.join(CSV_DIR,nombre_usuario, nombre)

    if os.path.exists(path_archivo):
        os.remove(path_archivo)
    else:
        flash(f'Archivo "{nombre}" no encontrado.', 'error')

    return redirect(url_for('csv_bp.listar_csv'))

# Vista para mostrar el formulario de subida de archivos
@csv_bp.route('/nuevo', methods=['GET'])
@login_requerido
def subir_csv_form():
    return render_template('csv_templates/csv_upload.html')

# Ruta POST para subir un nuevo archivo CSV al sistema
@csv_bp.route('/subir', methods=['POST'])
@login_requerido
def subir_csv():
    archivo = request.files.get('archivo_csv')
    url = 'csv_bp.subir_csv_form'
    if not archivo:
        flash("No se seleccionó ningún archivo.", "formato_error")
        return redirect(url_for(url))

    if not archivo.filename.endswith('.csv'):
        flash("Solo se permiten archivos con extensión .csv.", "formato_error")
        return redirect(url_for(url))



    if archivo.filename == 'webhook_dataset.csv':
        flash("El archivo csv a subir no debe llamarse igual que el archivo base ", "formato_error")
        return redirect(url_for(url))

    try:
        df = pd.read_csv(archivo)

        # Validación exacta de columnas
        columnas_csv = df.columns.tolist()
        if columnas_csv != COLUMNAS_VALIDAS:
            flash("Formato del CSV incorrecto. Verifica el formato del archivo CSV base para ver cuál es el formato correcto.", "formato_error")
            return redirect(url_for(url))

        # Reiniciar el puntero del archivo para volver a guardarlo
        archivo.stream.seek(0)

        # Guardar archivo en carpeta del usuario
        nombre_seguro = secure_filename(archivo.filename)
        nombre_usuario = session.get('nombre_usuario')
        user_folder = os.path.join(CSV_DIR,nombre_usuario)
        os.makedirs(user_folder, exist_ok=True)
        destino = os.path.join(user_folder, nombre_seguro)
        archivo.save(destino)

        return redirect(url_for('csv_bp.listar_csv'))

    except Exception as e:
        flash(f"Error al procesar el archivo: {str(e)}", "formato_error")
        return redirect(url_for(url))

# Vista para analizar un CSV y determinar si sus datos son reales o infectados
@csv_bp.route('/analizar', methods=['GET'])
@login_requerido
def analizar_csv_form():
    return render_template('csv_templates/csv_analyze.html')
@csv_bp.route('/analizar', methods=['POST'])
@login_requerido
def analizar_csv():
    archivo = request.files.get('archivo_csv')
    url = 'csv_bp.analizar_csv'
    if not archivo:
        flash("No se seleccionó ningún archivo.", "analizarf")
        return redirect(url_for(url))

    try:
        df = pd.read_csv(archivo)

        # Validar que al menos contenga las columnas necesarias (en este caso no necesita la columna estado ya que es la que se va a añadir)
        columnas_esperadas = COLUMNAS_VALIDAS[:-1]
        if not all(col in df.columns for col in columnas_esperadas):
            flash("Formato incorrecto. Verifica las columnas del CSV de ejemplo. En este caso el archivo puede no contener la columna de estado", "analizarf")
            return redirect(url_for(url))

        # Ordenar cronológicamente
        df = df.sort_values(by='timestamp')

        estados = []
        paquete_anterior = None

        for _, fila in df.iterrows():
            paquete_actual = {
                'timestamp': fila['timestamp'],
                'occupied': str(fila['occupied']),
                'button_pressed': str(fila['button_pressed']),
                'tamper_detected': str(fila['tamper_detected']),
                'battery_voltage': float(fila['battery_voltage']),
                'temperature_celsius': float(fila['temperature_celsius']),
                'humidity_percent': float(fila['humidity_percent']),
                'time_since_last_event_min': float(fila['time_since_last_event_min']),
                'event_count': int(fila['event_count'])
            }
            # Evaluar cada fila del CSV usando reglas heurísticas
            sospechoso, _ = evaluar_paquete(paquete_actual, paquete_anterior)
            estados.append("infectado" if sospechoso else "real")
            paquete_anterior = paquete_actual

        df['estado'] = estados

        # Guardar el archivo analizado con sufijo "_analizado"
        nombre_seguro = secure_filename(archivo.filename)
        nombre_base = os.path.splitext(nombre_seguro)[0]
        nombre_usuario = session.get('nombre_usuario')
        user_dir = os.path.join(CSV_DIR, nombre_usuario)
        os.makedirs(user_dir, exist_ok=True)

        nombre_salida = f"{nombre_base}_analizado.csv"
        path_guardado = os.path.join(user_dir, nombre_salida)
        df.to_csv(path_guardado, index=False)

        flash("Archivo analizado correctamente", "analizart")
        return redirect(url_for(url))

    except Exception as e:
        flash(f"Error durante el análisis: {str(e)}", "analizarf")
        return redirect(url_for(url))

# Ruta para descargar un archivo CSV desde el servidor
@csv_bp.route('/descargar/<nombre>')
@login_requerido
def descargar_csv(nombre):
    nombre_usuario = session.get('nombre_usuario')

    if nombre == nombre_dataset:
        path_dir = CSV_DIR
    else:
        path_dir = os.path.join(CSV_DIR, nombre_usuario)

    return send_from_directory(path_dir, nombre, as_attachment=True)