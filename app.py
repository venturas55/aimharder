from flask import Flask, request, render_template, redirect, url_for, flash, session
import pymysql
import os
import json
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
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

def get_current_clases_from():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT class_name FROM current_classes WHERE usuario = %s", (session['usuario'],))
        result = cur.fetchall()
    conn.close()
    return set(r['class_name'] for r in result)

def get_horarios():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM bookings WHERE user_id = %s", (session['id'],))
        result = cur.fetchall()
    conn.close()
    return result          

def get_config():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM configs WHERE id = %s", (session['id'],))
        result = cur.fetchone()
    conn.close()
    return result          

def get_current_hours_from():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT hora FROM current_hours WHERE usuario = %s", (session['usuario'],))
        result = cur.fetchall()
    conn.close()
    
    # Ordenar horarios por hora de inicio
    def sort_key(hora_str):
        # Extrae la hora de inicio como número, ej: '08:00 - 09:00' -> 800
        start = hora_str.split('-')[0].strip()
        h, m = map(int, start.split(':'))
        return h * 60 + m

    sorted_hours = sorted([r['hora'] for r in result], key=sort_key)
    
    # Crear diccionario con índice como string
    return {str(i): sorted_hours[i] for i in range(len(sorted_hours))}

""" class_times = {
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
} """

#current_clases=set()
#current_clases.add("Cross MD")
#current_clases.add("HYROX-Endurance")
#current_clases.add("Grappling")
#current_clases.add("B. Jiu-jitsu Principiante")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form['usuario']
        password = request.form['contrasena']

        # Conectar a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

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
        conn.close()

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'id' not in session:
        return redirect(url_for('login'))
    
    dias, hora ,clase,aimharder_user,aimharder_pass = None,None,None, None, None  # Inicializar estas variables fuera del bloque if
    
    class_times = get_current_hours_from()
    current_clases= get_current_clases_from()
    horario_lista= get_horarios()
    config= get_config()
    horario = { h['dia']: {'hora': h['hora'], 'clase': h['clase'],'activo':h['activo']} for h in horario_lista }
    print("horario:",horario)

    #hora, dias = getData()
    user_data = get_user_data_from_mysql()
    #print("hora: " , hora, "   === dias: ",dias)
    return render_template("index.html", config=config,horario=horario,class_times=class_times, dias=user_data['dias'], hora=user_data['hora'], clase=user_data['clase'],aimharder_pass=user_data['aimharder_pass'],aimharder_user=user_data['aimharder_user'],gym=user_data['gym'],current_clases=current_clases)   

@app.route("/guardar_basico", methods=["POST"])
def guardar_basico():
        conn = get_db_connection()
        cursor = conn.cursor()
        if request.method == "POST":
            dias = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']
            horario = {}
            for d in dias:
                hora = request.form.get(f"{d}_hora") or ""
                clase = request.form.get(f"{d}_clase") or ""
                activo = 1 if request.form.get(f"{d}_activo") else 0
                print(activo)
                
                horario[d] = {
                    "hora": hora,
                    "clase": clase,
                    "activo": activo
                }
                cursor.execute("""
                    INSERT INTO bookings (user_id, dia, hora, clase, activo)
                    VALUES (%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        hora = VALUES(hora),
                        clase = VALUES(clase),
                        activo = VALUES(activo)
                """, (session['id'], d, hora, clase,activo))

            conn.commit()
            conn.close()

            print(horario)
               
            #update_target_file(selected_time, selected_days, clase,aimharder_user,aimharder_pass,gym,session['id'])
            flash(f"Horarios actualizados", 'success')
            return redirect(url_for('dashboard'))  
       
@app.route("/guardar_avanzado", methods=["POST"])
def guardar_avanzado():
        if request.method == "POST":
            print(request.form)
            aimharder_user = request.form.get('aimharder_user')
            aimharder_pass = request.form.get('aimharder_pass')
            gym = request.form.get('gym')
            periodicidad = request.form.get('periodicidad')
            update_config(aimharder_user,aimharder_pass,gym,periodicidad)
            return redirect(url_for('dashboard'))  

def get_user_data_from_mysql():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM configs WHERE id = %s", (session['id'],))
    user_data = cur.fetchone()
    if user_data:
        cur.close()
        conn.close()
        return user_data
    else:
        cur.close()
        conn.close()
        return None

def update_target_file(selected_time, selected_days, clase,aimharder_user,aimharder_pass,gym,id):
    #print("selected_time: ", selected_time)
    path = os.path.join("scripts", f"aimharderVPS{id}.py")  # ejemplo guardando en carpeta 'scripts'
    print(path)
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
       
        return f"Reserva automática actualizada a: {selected_time} los días {', '.join(selected_days)}"
    except Exception as e:
        print("Error:", str(e))
        traceback.print_exc()
        return f"Error: {str(e)}"


def update_config(aimharder_user,aimharder_pass,gym,periodicidad):
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()
        # Verificar si existe
        # Usamos UPSERT: si el ID ya existe, se actualizan los campos; si no, se inserta
        cur.execute(
            """
            INSERT INTO configs (id, aimharder_user, aimharder_pass,gym,periodicidad) 
            VALUES (%s, %s,%s,%s,%s )
            ON DUPLICATE KEY UPDATE 
                aimharder_user = VALUES(aimharder_user),
                aimharder_pass = VALUES(aimharder_pass),
                gym = VALUES(gym),
                periodicidad = VALUES(periodicidad)
            """,
            (session["id"], aimharder_user,aimharder_pass,gym,periodicidad)
        )
        conn.commit()  # Confirmar la transacción
        cur.close()
        conn.close()
        return "Reconfiguracion actualizada"
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
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar si el usuario ya existe
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        existing_user = cur.fetchone()
        if existing_user:
            flash('El nombre de usuario ya existe. Elige otro.', 'danger')
            cur.close()
            conn.close()
            return redirect(url_for('register'))

        # Insertar el nuevo usuario en la base de datos
        cur.execute(
            "INSERT INTO usuarios (usuario, contrasena, email, full_name) VALUES (%s, %s, %s, %s)",
            (usuario, hashed_password, email, full_name)
        )
        print("ID: ", cur.lastrowid)
        cur.execute(
            "INSERT INTO configs (id, clase, hora, dias,aimharder_user,aimharder_pass) VALUES (%s,%s,%s, %s, %s, %s)",
            (cur.lastrowid, "HYROX-Endurance", "[lunes,Miercoles,Viernes]", "08:00-09:00","dfgh@fg.com", "dfh@345")
        )
        conn.commit()  # Confirmar la transacción
        cur.close()
        conn.close()

        flash('¡Usuario registrado exitosamente! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template("register.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
