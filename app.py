from flask import Flask, request, render_template, redirect, url_for, flash, session
import pymysql
import os
import json
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import re
import traceback
load_dotenv()

app = Flask(__name__)

# Configuración de la base de datos
# Accede a las variables del .env
app.config['MYSQL_HOST'] = os.getenv("DB_HOST")
app.config['MYSQL_USER'] = os.getenv("DB_USER")  # Reemplaza con tu nombre de usuario de MySQL
app.config['MYSQL_PASSWORD'] = os.getenv("DB_PASS") # Reemplaza con tu contraseña de MySQL
app.config['MYSQL_DB'] = os.getenv("DB_NAME")  # Reemplaza con el nombre de tu base de datos
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  # Clave secreta para sesiones

# Conexión con MySQL usando PyMySQL
def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor  # Para obtener resultados como diccionarios
    )

class_times = {
    '0': '07:00 - 08:00',
    '1': '08:00 - 09:00',
    '2': '09:00 - 10:00',
    '3': '10:00 - 11:00',
    '4': '11:00 - 12:00',
    '5': '12:00 - 13:00',
    '6': '13:00 - 14:00',
    '7': '14:00 - 15:00',
    '8': '15:00 - 16:00',
    '9': '16:00 - 17:00',
    '10': '17:00 - 18:00',
    '11': '18:00 - 19:00',
    '12': '19:00 - 20:00',
    '13': '20:00 - 21:00',
    '14': '21:00 - 22:00'
}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form['usuario']
        password = request.form['contrasena']

        # Conectar a la base de datos
        connection = get_db_connection()
        cur = connection.cursor()

        # Consulta para encontrar el usuario por nombre de usuario
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        user = cur.fetchone()

        if user and check_password_hash(user['contrasena'], password):
            # Usuario autenticado, crear sesión
            # Guardar todos los campos del usuario en la sesión automáticamente
            for key, value in user.items():
                session[key] = value
           
            flash('Login exitoso!', 'success')
            return redirect(url_for('dashboard'))  # Redirigir al dashboard o página principal
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')

        cur.close()
        connection.close()

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    dias, hora ,clase,aimharder_user,aimharder_pass = None,None,None, None, None  # Inicializar estas variables fuera del bloque if
    
    if request.method == "POST":
        selected_id = request.form.get("time_slot")
        selected_time = class_times.get(selected_id)
        selected_days = request.form.getlist('week_days')
        clase = request.form.get('clase')
        aimharder_user = request.form.get('aimharder_user')
        aimharder_pass = request.form.get('aimharder_pass')

        if selected_time:
            update_target_file(selected_time, selected_days, clase,aimharder_user,aimharder_pass)
            flash(f"Horario de {clase} actualizado a: {selected_time} los días {', '.join(selected_days)}", 'success')
            return redirect(url_for('dashboard'))  
    
    #hora, dias = getData()
    user_data = get_user_data_from_mysql()
    #print("hora: " , hora, "   === dias: ",dias)
    return render_template("index.html", class_times=class_times, dias=user_data['dias'], hora=user_data['hora'], clase=user_data['clase'],aimharder_pass=user_data['aimharder_pass'],aimharder_user=user_data['aimharder_user'])   

def get_user_data_from_mysql():
    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("SELECT * FROM configs WHERE id = %s", (session['id'],))
    user_data = cur.fetchone()
    if user_data:
        cur.close()
        connection.close()
        return user_data
    else:
        cur.close()
        connection.close()
        return None

def update_target_file(selected_time, selected_days, clase,aimharder_user,aimharder_pass):
    #print("selected_time: ", selected_time)
    path = "aimharderVPS.py"
    try:
        """  with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        # Reemplaza la línea que define 'desired_class_time'
        code = re.sub(
            r"(desired_class_time\s*=\s*)['\"].*?['\"]",
            rf"\1'{selected_time}'",
            code
        )

        # Actualiza los días
        days_str = "[" + ", ".join([f"'{day}'" for day in selected_days]) + "]"
        code = re.sub(
            r"(selected_days\s*=\s*)\[.*?\]",
            rf"\1{days_str}",
            code
        )
        # Reemplaza la línea que define 'clase'
        code = re.sub(
            r"(clase_deseada\s*=\s*)['\"].*?['\"]",
            rf"\1'{clase}'",
            code
        )


        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        """
        # Conectar a la base de datos
        connection = get_db_connection()
        cur = connection.cursor()
        # Verificar si existe
        # Usamos UPSERT: si el ID ya existe, se actualizan los campos; si no, se inserta
        cur.execute(
            """
            INSERT INTO configs (id, clase, dias, hora, aimharder_user, aimharder_pass) 
            VALUES (%s, %s,%s,%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                clase = VALUES(clase),
                dias = VALUES(dias),
                hora = VALUES(hora),
                aimharder_user = VALUES(aimharder_user),
                aimharder_pass = VALUES(aimharder_pass)
            """,
            (session["id"], str(clase),json.dumps(selected_days), str(selected_time),aimharder_user,aimharder_pass)
        )
        connection.commit()  # Confirmar la transacción
        cur.close()
        connection.close()

        return f"Reserva automática actualizada a: {selected_time} los días {', '.join(selected_days)}"
    except Exception as e:
        print("Error:", str(e))
        traceback.print_exc()
        return f"Error: {str(e)}"

@app.route("/logout")
def logout():
    session.clear()  # Limpiar la sesión
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        usuario = request.form['usuario']
        password = request.form['contrasena']
        email = request.form['email']
        full_name = request.form['full_name']

        # Hashear la contraseña antes de guardarla
        hashed_password = generate_password_hash(password)

        # Conectar a la base de datos
        connection = get_db_connection()
        cur = connection.cursor()

        # Verificar si el usuario ya existe
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        existing_user = cur.fetchone()
        if existing_user:
            flash('El nombre de usuario ya existe. Elige otro.', 'danger')
            cur.close()
            connection.close()
            return redirect(url_for('register'))

        # Insertar el nuevo usuario en la base de datos
        cur.execute(
            "INSERT INTO usuarios (usuario, contrasena, email, full_name) VALUES (%s, %s, %s, %s)",
            (usuario, hashed_password, email, full_name)
        )
        print("ID: ", cur.lastrowid)
        cur.execute(
            "INSERT INTO configs (id, clase, hora, dias,aimharder_user,aimharder_pass) VALUES (%s,%s,%s, %s, %s, %s)",
            (cur.lastrowid, "HYROX-endurance", "[lunes,Miercoles,Viernes]", "08:00-09:00","dfgh@fg.com", "dfh@345")
        )
        connection.commit()  # Confirmar la transacción
        cur.close()
        connection.close()

        flash('¡Usuario registrado exitosamente! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template("register.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
