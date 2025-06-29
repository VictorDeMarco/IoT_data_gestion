from flask import session, redirect, url_for
from functools import wraps
from src.dashboard_visualizer.utils.user_model import Usuario


def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        usuario_id = session.get('usuario_id')
        if not usuario_id or not Usuario.query.get(usuario_id):
            session.pop('usuario_id', None)
            return redirect(url_for('user_bp.procesar_login'))
        return f(*args, **kwargs)
    return wrapper