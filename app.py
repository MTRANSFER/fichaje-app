from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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

@app.route("/fichar", methods=["GET", "POST"])
def fichar():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        vehiculo = request.form.get("vehiculo")  # Se usa .get() para evitar KeyError
        estado = request.form.get("estado")

        if not vehiculo or not estado:
            return "Error: Todos los campos son obligatorios", 400

        fecha_hora = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # UTC para evitar problemas de zona horaria

        conn = get_db_connection()
        conn.execute("INSERT INTO fichajes (conductor, vehiculo, estado, fecha_hora) VALUES (?, ?, ?, ?)",
                     (session["user"], vehiculo, estado, fecha_hora))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("fichar.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)





