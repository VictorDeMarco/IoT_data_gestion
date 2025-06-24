from flask import Blueprint, request, redirect, session, render_template, url_for
from user_model import Usuario, db
from auth_utils import login_requerido
user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/registro', methods=['GET', 'POST'])
@login_requerido
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']

        if Usuario.query.filter_by(nombre=nombre).first():
            return 'Usuario ya registrado'

        nuevo_usuario = Usuario(nombre=nombre)
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        return redirect(url_for('user_bp.login'))

    return render_template('register.html')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        usuario = Usuario.query.filter_by(nombre=nombre).first()

        if usuario and usuario.check_password(password):
            session['usuario_id'] = usuario.id
            return redirect(url_for('dashboard'))
        return 'Credenciales incorrectas'

    return render_template('login.html')

@user_bp.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('user_bp.login'))
