import os

from flask import Blueprint, request, redirect, session, render_template, url_for, flash

from src.dashboard_visualizer.utils.paths import CSV_DIR
from src.dashboard_visualizer.utils.user_model import Usuario, db

user_bp = Blueprint('user_bp', __name__)

# Ruta para el registro de nuevos usuarios
@user_bp.route('/registro', methods=['GET'])
def mostrar_formulario_registro():
    return render_template('user_templates/register.html')

@user_bp.route('/registro', methods=['POST'])
def procesar_registro():
    nombre = request.form['nombre']
    password = request.form['password']

    if Usuario.query.filter_by(nombre=nombre).first():
        flash('El nombre de usuario ya está registrado.', 'registro_error')
        return redirect(url_for('user_bp.mostrar_formulario_registro'))

    nuevo_usuario = Usuario(nombre=nombre)
    nuevo_usuario.set_password(password)
    db.session.add(nuevo_usuario)
    db.session.commit()
    return redirect(url_for('user_bp.mostrar_formulario_login'))

# Ruta de inicio de sesión
@user_bp.route('/login', methods=['GET'])
def mostrar_formulario_login():
    return render_template('user_templates/login.html')

@user_bp.route('/login', methods=['POST'])
def procesar_login():
    nombre = request.form['nombre']
    password = request.form['password']
    usuario = Usuario.query.filter_by(nombre=nombre).first()

    if usuario and usuario.check_password(password):
        session['usuario_id'] = usuario.id
        session['nombre_usuario'] = usuario.nombre
        return redirect(url_for('dashboard'))

    flash('Usuario o contraseña incorrectos.', 'login_error')
    return redirect(url_for('user_bp.mostrar_formulario_login'))

# Ruta de recuperación de contraseña
@user_bp.route('/recuperar', methods=['GET'])
def mostrar_formulario_recuperar():
    return render_template('user_templates/recover.html')

@user_bp.route('/recuperar', methods=['POST'])
def procesar_recuperar():
    nombre = request.form['nombre']
    archivo_csv = request.form['archivo_csv']
    nueva_pass = request.form.get('nueva_pass')
    confirmar_pass = request.form.get('confirmar_pass')
    url = 'user_bp.mostrar_formulario_recuperar'
    usuario = Usuario.query.filter_by(nombre=nombre).first()
    if not usuario:
        flash("Usuario no encontrado.", "recuperar_error")
        return redirect(url_for(url))

    user_dir = os.path.join(CSV_DIR, nombre)
    archivo_path = os.path.join(user_dir, archivo_csv)

    if not os.path.isfile(archivo_path):
        flash("Archivo CSV incorrecto.", "recuperar_error")
        return redirect(url_for(url))

    if not nueva_pass or nueva_pass != confirmar_pass:
        flash("Las contraseñas no coinciden.", "recuperar_error")
        return redirect(url_for(url))

    # Cambiar contraseña
    usuario.set_password(nueva_pass)
    db.session.commit()
    flash("Contraseña actualizada correctamente.", "recuperar_ok")
    return redirect(url_for(url))

# Ruta para cerrar sesión
@user_bp.route('/logout')
def logout():
    session.clear()  # Limpiar toda la sesión
    session['csv_aplicado'] = 'webhook_dataset.csv'  # Establecer dataset por defecto tras logout
    return redirect(url_for('user_bp.procesar_login'))