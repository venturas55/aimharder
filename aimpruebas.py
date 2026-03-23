from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from datetime import date,datetime, timedelta
import os
import subprocess
import sys
import pymysql
import json
import smtplib
import tempfile
import shutil, glob
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")  # Reemplaza con tu nombre de usuario de MySQL
DB_PASS = os.getenv("DB_PASS") # Reemplaza con tu contraseña de MySQL
DB_NAME = os.getenv("DB_NAME")  # Reemplaza con el nombre de tu base de datos


for old_profile in glob.glob("/tmp/aimharder-profile-*"):
    try:
        shutil.rmtree(old_profile)
    except Exception:
        pass

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor
)

# Accede a las variables
email_account = os.getenv("EMAIL_ACCOUNT")
email_password = os.getenv("EMAIL_PASSWORD")
#email_to = os.getenv("EMAIL_TO")
email_to_dev = os.getenv("EMAIL_TO_DEV")
email_smtp_server = os.getenv("EMAIL_SMTP_SERVER")
email_smtp_port = os.getenv("EMAIL_SMTP_PORT")
#user_name = os.getenv("AIMHARDER_USERNAME")
#passw = os.getenv("AIMHARDER_PASSWORD")


ahora = datetime.now()
today = date.today()
fechalog= str(today) + " " + ahora.strftime("%H:%M")

# Mapea weekday() a nombres
tomorrow_week_map = {
    6: 'Lunes',
    0: 'Martes',
    1: 'Miercoles',
    2: 'Jueves',
    3: 'Viernes',
    4: 'Sabado',
    5: 'Domingo'
}

# Mapea dia a clase 
dias = {
    'Lunes':1,
    'Martes':2,
    'Miercoles':3,
    'Jueves':4,
    'Viernes':5,
    'Sabado':6,
    'Domingo':7
}



def get_text_or_empty(parent, by, value):
    elements = parent.find_elements(by, value)
    return elements[0].text.strip() if elements else ""

def book_class(driver, reserva_deseada, nextClase):
    wait = WebDriverWait(driver, 15)

    if today.weekday() == 6:
        try:
            driver.find_element(By.ID, "nextWeek").click()
        except NoSuchElementException:
            print(f"{fechalog} - No se encontró botón nextWeek")

    anchor = driver.find_element(By.CSS_SELECTOR, f"div#weekDays a.{nextClase}")
    anchor.click()

    wait.until(EC.staleness_of(anchor))

    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bloqueClase")))
    except TimeoutException:
        return {"status": "error", "msg": "No cargaron las clases"}

    time.sleep(3)

    class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")

    for block in class_blocks:
        class_name = get_text_or_empty(block, By.CLASS_NAME, "rvNombreCl")
        class_horario = get_text_or_empty(block, By.CLASS_NAME, "rvHora")

        if reserva_deseada['clase'] in class_name and class_horario == reserva_deseada['hora']:

            instructor_name = get_text_or_empty(block, By.CLASS_NAME, "rvCoach")
            box_name = get_text_or_empty(block, By.CLASS_NAME, "rvBox")

            # Ocultar cookies
            try:
                driver.execute_script("document.getElementById('eucookielaw').style.display = 'none';")
            except Exception:
                pass

            try:
                reserve_link = block.find_element(By.XPATH, ".//a[contains(@onclick, 'bookClass')]")
                # reserve_link.click()
            except NoSuchElementException:
                return {"status": "error", "msg": "No se encontró botón reservar"}

            # CLASE LLENA
            try:
                wait.until(EC.presence_of_element_located((By.ID, 'infoDialogBox')))
                info_dialog = driver.find_element(By.ID, 'infoDialogBox')

                if "La clase está llena" in info_dialog.text:
                    return {
                        "status": "llena",
                        "clase": reserva_deseada['clase'],
                        "hora": reserva_deseada['hora'],
                        "box": box_name,
                        "coach": instructor_name
                    }

            except TimeoutException:
                pass

            # LISTA DE ESPERA
            try:
                WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((
                        By.XPATH,
                        "//span[contains(@class, 'rvLista') and contains(text(), 'En lista de espera')]"
                    ))
                )

                return {
                    "status": "espera",
                    "clase": reserva_deseada['clase'],
                    "hora": reserva_deseada['hora'],
                    "box": box_name,
                    "coach": instructor_name
                }

            except TimeoutException:
                return {
                    "status": "reservada",
                    "clase": reserva_deseada['clase'],
                    "hora": reserva_deseada['hora'],
                    "box": box_name,
                    "coach": instructor_name
                }

    return {
        "status": "no_encontrada",
        "clase": reserva_deseada['clase'],
        "hora": reserva_deseada['hora']
    }


def gestionar_resultado_email(res, email_to, email_to_dev):
    status = res["status"]

    if status == "reservada":
        send_email(
            subject="Reserva confirmada ✅",
            body=f"Reserva realizada para {res['clase']} ({res['hora']}) en {res['box']} con {res['coach']}",
            to_email=email_to
        )

    elif status == "espera":
        send_email(
            subject="En lista de espera 🟡",
            body=f"Lista de espera para {res['clase']} ({res['hora']})",
            to_email=email_to
        )

    elif status == "llena":
        send_email(
            subject="Clase llena ❌",
            body=f"La clase {res['clase']} ({res['hora']}) está llena",
            to_email=email_to
        )

    elif status == "no_encontrada":
        send_email(
            subject="Clase no encontrada ❌",
            body=f"No se encontró {res['clase']} a las {res['hora']}",
            to_email=email_to_dev
        )

    elif status == "error":
        send_email(
            subject="Error en reserva ❌",
            body=res["msg"],
            to_email=email_to_dev
        )

#funcion que se ejecutará un domingo
def book_week(driver,reservas_deseadas):
    nextWeek = driver.find_element(By.ID, "nextWeek")
    nextWeek.click()
    for i in range(1,8):
        tomorrow = today + timedelta(days=i)
        nextClase = "wds"+tomorrow.strftime("%Y%m%d")
        print(nextClase," - ",reservas_deseadas[i-1])
        #book_class(driver,reservas_deseadas[i-1],nextClase)

def login_to_aimharder(username, password):

    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")  # New headless mode for Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--verbose")  # Chrome imprimirá muchos logs
    
    # For VPS environment
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--remote-debugging-address=0.0.0.0")
    
    # Set environment variables for VPS
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOCAL'] = '1'


    # Crear directorio temporal único
    tmpdir = tempfile.mkdtemp(prefix="aimharder-profile-")
    print("User data dir que vamos a usar:", tmpdir)
    # Usar el directorio temporal para el perfil
    chrome_options.add_argument(f"--user-data-dir={tmpdir}")

    chrome_log_path = "/tmp/chrome_debug.log"
    chrome_options.add_argument(f"--log-path={chrome_log_path}")
    
     # Initialize Chromium driver for VPS
    try:
        # Try to find the Chromium binary path
        chromium_path = None
        try:
            # Try to find Chromium using which command
            result = subprocess.run(['which', 'chromium-browser'], capture_output=True, text=True)
            if result.returncode == 0:
                chromium_path = result.stdout.strip()
        except:
            pass

        # If Chromium not found, try with default path
        if not chromium_path:
            chromium_path = '/usr/bin/chromium-browser'

        # Set the binary location
        chrome_options.binary_location = chromium_path

        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver,15)

        print(f"{fechalog} - Successfully initialized Chromium driver")

    except Exception as e:
        print(f"{fechalog} - Error initializing Chromium driver: {str(e)}")
        sys.exit(1)
    
    try:
        # Navigate to aimharder.com
        driver.get("https://login.aimharder.com/")
        
        # Wait for the login form to load
        try:
            wait.until(EC.presence_of_element_located((By.ID, "mail")))
            print(f"{fechalog} - Login form found")
        except Exception as e:
            print(f"{fechalog} - Could not find login form: {str(e)}")
            driver.quit()
            return
            
        # Enter username and password
        try:
            # Click cookie remove button
            try:
                cookie_remove_button = driver.find_element(By.CLASS_NAME, "removeCookie")
                cookie_remove_button.click()
                print(f"{fechalog} - Cookie removal button clicked")
                time.sleep(1)
            except Exception as e:
                print(f"{fechalog} - Could not find or click cookie removal button: {str(e)}")
                # Continue anyway since this might not be critical
                pass
            # Enter username
            username_field = driver.find_element(By.ID, "mail")
            username_field.clear()
            username_field.send_keys(username)
            
            # Enter password
            password_field = driver.find_element(By.ID, "pw")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            submit_button = driver.find_element(By.ID, "loginSubmit")
            submit_button.click()
            
            # Wait for login to complete
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ahPicReservations")))
            print(f"{fechalog} - Login successful")
            
            # Click reservations
            reservations_link = driver.find_element(By.CLASS_NAME, "ahPicReservations")
            reservations_link.click()
            print(f"{fechalog} - Clicked reservations link")
            
            # Wait for the class list to load       
            return driver  # ✅ devolver SOLO si todo fue bien   
        except Exception as e:
            print(f"{fechalog} - Error during login process: {str(e)}")
            driver.quit()
            return
            
    except Exception as e:
        print(f"{fechalog} - An error occurred: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None

def send_email(subject, body, to_email):
    from_email = email_account  
    from_password = email_password        
    smtp_server = email_smtp_server
    smtp_port = email_smtp_port

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        print(f"{fechalog} - Correo enviado")
    except Exception as e:
        print(f"{fechalog} - No se pudo enviar el correo: {str(e)}")

if __name__ == "__main__":
    # Example usage - replace these with your actual credentials
    try:
        with conn:
            with conn.cursor() as cur:
                # Obtener configuraciones de todos los usuarios que tengan una
                cur.execute("SELECT u.id,u.usuario,u.full_name,u.email,c.clase,c.dias,c.hora,c.aimharder_user,c.aimharder_pass,c.gym,c.periodicidad from usuarios u LEFT JOIN configs c ON u.id=c.id")
                usuarios = cur.fetchall()
                usuarios=usuarios # para hacer pruebas solo con el usuario tipo semanal.
                for usuario in usuarios:
                    user_id = usuario['id']
                    aimharder_user = usuario['aimharder_user']
                    aimharder_pass = usuario['aimharder_pass']
                    gym = usuario['gym']
                    periodicidad = usuario['periodicidad']
                    email_to = usuario['email']
                    cur.execute("SELECT * from bookings where user_id=%s", (user_id,))
                    reservas = cur.fetchall()
                    #print(reservas)
                    #dias_deseados = [item['dia'] for item in reservas]
                    #print(f"{fechalog} - [{user_id}] Ejecutando con Días: {dias_deseados}")

                    ##PARA USUARIOS TIPO XISME25 QUE HA DE EJECUTAR CADA DIA
                    if periodicidad == 'daily':
                        print(f" ⏭️ ⏭️ {aimharder_user} tiene daily")
                        tomorrow_name = tomorrow_week_map[today.weekday()] #quitar el menos 1, es para pruebas despues de medianoche
                        
                        #print("Mañana",tomorrow_name)
                        clase_manana = next(item for item in reservas if item['dia'] == tomorrow_name)
                        #print(f"Mañana es {clase_manana}")
                        #print(f"Los días seleccionados son: {dias_deseados}")
                        if clase_manana['activo']:
                            print(f"{fechalog} - ⏭️ Mañana es {clase_manana['dia']}, está en los días seleccionados de {aimharder_user}. Haciendo reserva...")
                            driver_conexion=login_to_aimharder(aimharder_user,aimharder_pass)
                            if driver_conexion:
                                tomorrow = today + timedelta(days=1)
                                nextClase = "wds"+tomorrow.strftime("%Y%m%d")
                                resultado= book_class(driver_conexion,clase_manana,nextClase)
                                print("Resultado:", resultado)
                                #gestionar_resultado_email(resultado, email_to, email_to_dev)
                                driver_conexion.quit()
                            else:
                                print(f"Error en login de {aimharder_user}")
                        else:
                            print(f"{fechalog} - ⏭️ Mañana es {clase_manana['dia']}, no está en los días seleccionados de {aimharder_user}. No se hace reserva.")
                            continue
                        
                    ##PARA USUARIOS TIPO JAVI QUE HA DE EJECUTAR CADA DOMINGO
                    elif periodicidad == 'weekly':
                        print(f" ⏭️ ⏭️ {aimharder_user} tiene weekly y hoy es {today}")
                        #if(today.weekday() == 6 ): # si es domingo POR LO QUE ESTO SE EJECUTARA SIEMPRE UN DOMINGO (DIA 6)
                        if True:
                            print(f"{fechalog} - Hoy es {today.weekday()}")
                            #print(reservas)
                            driver_conexion=login_to_aimharder(aimharder_user,aimharder_pass)

                            for i in range(len(reservas)):
                                if reservas[i]['activo']:
                                    proxima=dias.get(reservas[i]['dia']) #traduce el dia de la semana de la reserva en un numero del 1 al 7
                                    #print("P",proxima)
                                    tomorrow = today + timedelta(days=proxima) # Proxima reserva será today(domingo (dia 6)) + i
                                    nextClase = "wds"+tomorrow.strftime("%Y%m%d")
                                    print(f"{fechalog} - ⏭️ Reservando: {nextClase} - {reservas[i]}")
                                    if driver_conexion:
                                        resultado=book_class(driver_conexion,reservas[i],nextClase)
                                        print("Resultado:", resultado)
                                        #gestionar_resultado_email(resultado, email_to, email_to_dev)
                                    else:
                                        print(f"Error en login de {aimharder_user}")
                            driver_conexion.quit()
                        else:
                            print("No es domingo")

    except Exception as e:
        print(f"{fechalog} - Error GLOBAL al hacer reserva: {str(e)}")
        send_email(subject="Error al hacer reserva ❌", body=f"Ocurrió un error GLOBAL al reservar:\n{str(e)}",to_email=email_to_dev)
