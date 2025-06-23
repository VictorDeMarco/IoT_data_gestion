from flask import Flask, render_template, request, session, redirect, url_for
from user_model import db
from user_routes import user_bp
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Cambia esto en producción


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL', 'sqlite:///default.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


app.register_blueprint(user_bp)


with app.app_context():
    db.create_all()

    # Crear usuario admin si no existe
    from user_model import Usuario
    if not Usuario.query.filter_by(email='admin@admin.com').first():
        admin = Usuario(nombre='admin', email='admin@admin.com')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

def login_requerido(f):
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('user_bp.login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
@login_requerido
def dashboard():
    df = pd.read_csv('src/python/csv/webhook_dataset.csv')
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
