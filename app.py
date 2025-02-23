from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"

# Función para conectar con la base de datos
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Página de inicio de sesión
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            error = "Usuario o contraseña incorrectos"
    
    return render_template("login.html", error=error)

# Página principal (dashboard)
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if session["role"] == "admin":
        fichajes = conn.execute("SELECT * FROM fichajes").fetchall()
    else:
        fichajes = conn.execute("SELECT * FROM fichajes WHERE conductor = ?", (session["user"],)).fetchall()
    
    conn.close()
    
    return render_template("dashboard.html", fichajes=fichajes, user=session["user"], role=session["role"])

# Página de fichaje
@app.route("/fichar", methods=["GET", "POST"])
def fichar():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "vehiculo" not in request.form:
            return "Error: No se recibió el campo 'vehiculo'", 400

        vehiculo = request.form["vehiculo"]
        estado = request.form["estado"]
        fecha_hora = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # UTC para evitar problemas de zona horaria

        conn = get_db_connection()
        conn.execute("INSERT INTO fichajes (conductor, vehiculo, estado, fecha_hora) VALUES (?, ?, ?, ?)",
                     (session["user"], vehiculo, estado, fecha_hora))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("fichar.html")

# Cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Exportar fichajes a Excel
@app.route("/export")
def export():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    fichajes = conn.execute("SELECT * FROM fichajes").fetchall()
    conn.close()

    # Crear CSV en respuesta
    output = "ID,Conductor,Vehículo,Estado,Hora\n"
    for fichaje in fichajes:
        output += f"{fichaje['id']},{fichaje['conductor']},{fichaje['vehiculo']},{fichaje['estado']},{fichaje['fecha_hora']}\n"

    return output, 200, {"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=fichajes.csv"}

if __name__ == "__main__":
    app.run(debug=True)

