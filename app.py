from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Clave para la sesión

# Conectar con la base de datos
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Página de inicio (Login)
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")

# Panel de usuario
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

    return render_template("dashboard.html", user=session["user"], role=session["role"], fichajes=fichajes)

# Fichaje
@app.route("/fichar", methods=["POST"])
def fichar():
    if "user" not in session:
        return redirect(url_for("login"))

    vehiculo = request.form["vehiculo"]
    estado = request.form["estado"]
    fecha_hora = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # UTC para evitar problemas de zona horaria

    conn = get_db_connection()
    conn.execute("INSERT INTO fichajes (conductor, vehiculo, estado, fecha_hora) VALUES (?, ?, ?, ?)",
                 (session["user"], vehiculo, estado, fecha_hora))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

# Exportar datos
@app.route("/export")
def export():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    fichajes = conn.execute("SELECT * FROM fichajes").fetchall()
    conn.close()

    output = "ID,Conductor,Vehículo,Estado,Fecha\n"
    for ficha in fichajes:
        output += f"{ficha['id']},{ficha['conductor']},{ficha['vehiculo']},{ficha['estado']},{ficha['fecha_hora']}\n"

    return output, 200, {"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=fichajes.csv"}

# Cerrar sesión
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Render asignará el puerto
    app.run(host="0.0.0.0", port=port, debug=True)

