from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Asegúrate de cambiar esta clave por seguridad

# Configuración de zona horaria (ajustada para que coincida con tu hora local)
TZ = pytz.timezone('Europe/Madrid')

# Conexión a la base de datos
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Página de inicio / Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')

    return render_template('login.html')

# Panel de usuario (Admin ve todo, otros solo su información)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    if session['role'] == 'admin':
        fichajes = conn.execute('SELECT * FROM fichajes').fetchall()
    else:
        fichajes = conn.execute('SELECT * FROM fichajes WHERE conductor = ?', (session['username'],)).fetchall()

    conn.close()
    return render_template('dashboard.html', fichajes=fichajes, username=session['username'], role=session['role'])

# Registrar fichaje
@app.route('/fichar', methods=['POST'])
def fichar():
    if 'username' not in session:
        return redirect(url_for('login'))

    vehiculo = request.form.get('vehiculo', '').strip()
    estado = request.form.get('estado', 'Entrada')

    if not vehiculo:
        return "Error: Debes ingresar una matrícula válida", 400  # Evita el error BadRequestKeyError

    hora_actual = datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute('INSERT INTO fichajes (conductor, vehiculo, estado, hora) VALUES (?, ?, ?, ?)',
                 (session['username'], vehiculo, estado, hora_actual))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)






