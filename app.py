from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por seguridad

# Conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ruta de inicio de sesión
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")
    
    return render_template('login.html')

# Ruta del panel de control
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = get_db_connection()

    if username == "admin":
        fichajes = conn.execute('SELECT * FROM fichajes').fetchall()
    else:
        fichajes = conn.execute('SELECT * FROM fichajes WHERE username = ?', (username,)).fetchall()
    
    conn.close()
    return render_template('dashboard.html', username=username, fichajes=fichajes)

# Ruta para registrar fichajes
@app.route('/fichar', methods=['POST'])
def fichar():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    vehiculo = request.form.get('vehiculo', '').strip()  # Evita errores si el campo no se envía
    estado = request.form.get('estado', 'Entrada')

    if not vehiculo:  # Verifica que el vehículo no esté vacío
        return "Error: Debes ingresar una matrícula válida.", 400

    hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute('INSERT INTO fichajes (username, vehiculo, estado, hora) VALUES (?, ?, ?, ?)', 
                 (username, vehiculo, estado, hora_actual))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)







