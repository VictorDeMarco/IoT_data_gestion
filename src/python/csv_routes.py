import os
import pandas as pd
from flask import Blueprint, session, redirect, flash, render_template, url_for
from auth_utils import login_requerido
from datetime import datetime
csv_bp = Blueprint('csv_bp', __name__)


CSV_DIR = os.path.join(os.path.dirname(__file__), 'csv')

@csv_bp.route('/csv')
@login_requerido
def listar_csv():
    archivos = []
    for f in os.listdir(CSV_DIR):
        if f.endswith('.csv'):
            path = os.path.join(CSV_DIR, f)
            archivos.append({
                'nombre': f,
                'tamano': round(os.path.getsize(path) / 1024, 2),
                'modificado': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%d/%m/%Y %H:%M')
            })
    return render_template('csv_list.html', archivos=archivos)

@csv_bp.route('/csv/<nombre>')
@login_requerido
def ver_csv(nombre):
    path_archivo = os.path.join(CSV_DIR, nombre)
    if not os.path.exists(path_archivo):
        return "Archivo no encontrado", 404

    df = pd.read_csv(path_archivo)
    columnas = df.columns.tolist()
    filas = df.values.tolist()

    return render_template('csv_view.html', nombre=nombre, columnas=columnas, filas=filas)

@csv_bp.route('/aplicar/<nombre>', methods=['POST'])
@login_requerido
def aplicar_csv(nombre):
    path_archivo = os.path.join(CSV_DIR, nombre)
    if os.path.exists(path_archivo):
        session['csv_aplicado'] = nombre
        flash(f'Se ha aplicado el archivo "{nombre}" al dashboard.', 'success')
    else:
        flash('Archivo no encontrado.', 'error')
    return redirect(url_for('csv_bp.listar_csv'))
@csv_bp.route('/eliminar/<nombre>', methods=['POST'])
@login_requerido
def eliminar_csv(nombre):
    path_archivo = os.path.join(CSV_DIR, nombre)
    if os.path.exists(path_archivo):
        os.remove(path_archivo)
        flash(f'Archivo "{nombre}" eliminado exitosamente.', 'success')
    else:
        flash(f'Archivo "{nombre}" no encontrado.', 'error')
    return redirect(url_for('csv_bp.listar_csv'))