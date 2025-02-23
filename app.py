from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'tu_secreto'

# Conectar con la base de datos
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
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")

    return render_template('login.html')

# Ruta de logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Ruta del dashboard - Panel de fichajes
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Si el usuario es admin, ve todos los fichajes
    if session["role"] == "admin":
        cursor.execute("""
            SELECT fichajes.id, users.username, fichajes.vehicle, fichajes.status, fichajes.timestamp
            FROM fichajes 
            JOIN users ON fichajes.user_id = users.id
        """)
    else:
        cursor.execute("""
            SELECT fichajes.id, users.username, fichajes.vehicle, fichajes.status, fichajes.timestamp
            FROM fichajes 
            JOIN users ON fichajes.user_id = users.id 
            WHERE users.username = ?
        """, (session["username"],))

    fichajes = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", fichajes=fichajes, role=session["role"])

# Ruta para registrar fichajes
@app.route('/fichar', methods=['GET', 'POST'])
def fichar():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Lista de vehículos predefinidos
    vehicles = ["7411MRJ", "8327LGK"]

    if request.method == "POST":
        vehicle = request.form['vehicle']
        status = request.form['status']
        username = session['username']

        # Obtener la hora actual correctamente en la zona horaria local (sin aplicar más cambios)
        hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fichajes (user_id, vehicle, status, timestamp) 
            VALUES ((SELECT id FROM users WHERE username = ?), ?, ?, ?)
        """, (username, vehicle, status, hora_actual))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template("fichar.html", vehicles=vehicles)

# Exportar fichajes a Excel
@app.route('/export')
def export():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    if session["role"] == "admin":
        df = pd.read_sql_query("""
            SELECT fichajes.id, users.username, fichajes.vehicle, fichajes.status, fichajes.timestamp
            FROM fichajes 
            JOIN users ON fichajes.user_id = users.id
        """, conn)
    else:
        df = pd.read_sql_query("""
            SELECT fichajes.id, users.username, fichajes.vehicle, fichajes.status, fichajes.timestamp
            FROM fichajes 
            JOIN users ON fichajes.user_id = users.id 
            WHERE users.username = ?
        """, conn, params=(session["username"],))

    conn.close()

    file_path = "fichajes.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

# Iniciar el servidor
if __name__ == '__main__':
    app.run(debug=True)
