from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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
# Default class time
#dias_deseados = ['Lunes', 'Miercoles', 'Viernes']  # <- Esta línea se actualizará automáticamente
#hora_deseada = '08:00 - 09:00'  # Default time
#clase_deseada = 'HYROX-EnduranceE'  # Default class name


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

def book_class(driver,reserva_deseada,nextClase):
    wait = WebDriverWait(driver,15)

    if(today.weekday() == 6):
            #print(f"{fechalog} - Hoy es domingo")
            nextWeek = driver.find_element(By.ID, "nextWeek")
            nextWeek.click()

    #print(f"{fechalog} - Hoy es {today} y la clase es {nextClase}")
    anchor = driver.find_element(By.CSS_SELECTOR, f"div#weekDays a.{nextClase}")
    anchor.click()
     # Espera hasta 15 segundos para que el div con id 'infoDialogBox' esté presente en el DOM
    # Espera a que el contenido anterior desaparezca (clave)
    wait.until(EC.staleness_of(anchor))
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bloqueClase")))
    #time.sleep(1)
    print(f"{fechalog} - Clicked day link {nextClase}")
    # Find the {clase_deseada}  class
    try:
        # Find all class blocks
        class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")
        #print(class_blocks)
        # Look for the {clase_deseada}  class at 8:00 - 9:00
        for block in class_blocks:
            # Check if this block contains the H{clase_deseada}  class name
            #print(f"{fechalog} - Clase: ", block.text)
            class_name = get_text_or_empty(block, By.CLASS_NAME, "rvNombreCl")
            class_horario = get_text_or_empty(block, By.CLASS_NAME, "rvHora")
            print(f"DEBUG -> '{class_name}' | '{class_horario}'")
            print(f"BUSCO -> '{reserva_deseada['clase']}' | '{reserva_deseada['hora']}'")   
            if reserva_deseada['clase'] in class_name and class_horario == reserva_deseada['hora']:
                print("encontrado la clase deseada")
                instructor_name = get_text_or_empty(block, By.CLASS_NAME, "rvCoach")
                box_name =  get_text_or_empty(block, By.CLASS_NAME, "rvBox")
                #rvClaseDesc =  get_text_or_empty(block, By.CLASS_NAME, "rvClaseDesc")
                # Find and click the reservation link within this block
                #print("DESCRIPCION",instructor_name, box_name, rvClaseDesc)
                #reserve_link = block.find_element(By.XPATH, ".//a[contains(text(), 'Reservar')]")
                #reserve_link = block.find_element(By.XPATH, ".//a[contains(@onclick, 'bookClass')]")
                #print("RL",reserve_link)
                #driver.execute_script("arguments[0].scrollIntoView();", reserve_link)
                try:
                        #eucookielaw = driver.find_element(By.ID, 'eucookielaw')
                        #print(eucookielaw.get_attribute('outerHTML'))
                        driver.execute_script("document.getElementById('eucookielaw').style.display = 'none';")
                except:
                    print("sin cookie")
                try:
                    #print("B:",block.get_attribute("outerHTML"))
                    reserve_link = block.find_element(By.XPATH, ".//a[contains(@onclick, 'bookClass')]")
                    #reserve_link.click()
                    print(f"{fechalog} - virtually Clicked on Reservar button")
                except Exception as e:
                    print("Puta mierda:",e)

                try:
                        # Espera hasta 3 segundos para que el div con id 'infoDialogBox' esté presente en el DOM
                        wait.until(EC.presence_of_element_located((By.ID, 'infoDialogBox')))
                        # Después de esperar, buscamos el div y verificamos su texto
                        info_dialog = driver.find_element(By.ID, 'infoDialogBox')
                        if "La clase está llena" in info_dialog.text:
                            print(f"{fechalog} - ❌ Lista de espera llena para la clase {reserva_deseada['clase']} en {box_name} con el {instructor_name} para mañana a las {reserva_deseada['hora']}. ❌")
                            #send_email(   subject="Clase llena en AimHarder ❌",  body=f"La clase {reserva_deseada['clase']}  en {box_name} con el {instructor_name} fue no pudo reservarse para mañana a las {reserva_deseada['hora']} por estar llena.", to_email=email_to  )
                            
                except:
                        try:
                            # Espera hasta 5 segundos a que aparezca el span con el texto "LISTA DE ESPERA"
                            #lista_espera =   WebDriverWait(driver, 5).until( EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'rvLista') and contains(text(), 'En lista de espera')]")))
                            lista_espera = WebDriverWait(driver, 5).until( EC.visibility_of_element_located((By.XPATH, "//span[contains(@class, 'rvLista') and contains(text(), 'En lista de espera')]")))
                            #print("Lista Espera: ",lista_espera)
                            print(f"{fechalog} - ✅ Estas anotado en lista de espera par la clase {reserva_deseada['clase']}  en {box_name} con el {instructor_name} para mañana a las {reserva_deseada['hora']}. ✅")
                            #send_email( subject="Reserva AimHarder realizada ✅", body=f"✅ Estas anotado en lista de espera par la clase {reserva_deseada['clase']}  en {box_name} con el {instructor_name} para mañana a las {reserva_deseada['hora']}. ✅",to_email=email_to)
                        except:
                            #print("El div con el aviso no ha aparecido en 3 segundos.")
                            print(f"{fechalog} - ✅ La clase {reserva_deseada['clase']}  en {box_name} con el {instructor_name} fue reservada correctamente para mañana a las {reserva_deseada['hora']}. ✅")
                            #send_email(subject="Reserva AimHarder realizada ✅",body=f"La clase {reserva_deseada['clase']}  en {box_name} con el {instructor_name} fue reservada correctamente para mañana a las {reserva_deseada['hora']}.",to_email=email_to)
                break
                
            else:
                print(f"{fechalog} - Could not find {reserva_deseada['clase']} class in the list")
            
    except Exception as e:
        print(f"{fechalog} - Error finding button or clicking RESERVAR {reserva_deseada['clase']} a las {reserva_deseada['hora']}   ERROR: {str(e)}")
        #send_email(            subject="Error al hacer reserva ❌",            body=f"Ocurrió un error al reservar:\n{str(e)}",            to_email=email_to_dev        )

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

            # Check if today is Sunday (6) and click next week if it is
           
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
                #print(usuarios)
                for usuario in usuarios:
                    user_id = usuario['id']
                    aimharder_user = usuario['aimharder_user']
                    aimharder_pass = usuario['aimharder_pass']
                    gym = usuario['gym']
                    periodicidad = usuario['periodicidad']
                    email_to = usuario['email']
                    cur.execute("SELECT * from bookings where user_id=%s", (user_id,))
                    reservas = cur.fetchall()
                    print(aimharder_user,periodicidad)
                    dias_deseados = [item['dia'] for item in reservas]
                    #print(f"{fechalog} - [{user_id}] Ejecutando con Días: {dias_deseados}")

                    ##PARA USUARIOS TIPO XISME25 QUE HA DE EJECUTAR CADA DIA
                    if periodicidad == 'daily':
                        print(f" {aimharder_user} tiene daily")
                        tomorrow_name = tomorrow_week_map[today.weekday()] #quitar el menos 1, es para pruebas despues de medianoche
                        
                        #print("Mañana",tomorrow_name)
                        clase_manana = next(item for item in reservas if item['dia'] == tomorrow_name)
                        #print(f"Mañana es {clase_manana}")
                        #print(f"Los días seleccionados son: {dias_deseados}")
                        if tomorrow_name not in dias_deseados:
                            print(f"{fechalog} - ⏭️ Mañana es {clase_manana['dia']}, no está en los días seleccionados de {aimharder_user} {dias_deseados}. No se hace reserva.")
                            break
                        else:
                            print(f"{fechalog} - ⏭️ Mañana es {clase_manana['dia']}, está en los días seleccionados de {aimharder_user} {dias_deseados}. Haciendo reserva...")
                            driver_conexion=login_to_aimharder(aimharder_user,aimharder_pass)
                            if driver_conexion:
                                tomorrow = today + timedelta(days=1)
                                nextClase = "wds"+tomorrow.strftime("%Y%m%d")
                                book_class(driver_conexion,clase_manana,nextClase)
                                driver_conexion.quit()
                            else:
                                print(f"Error en login de {aimharder_user}")
                        
                    ##PARA USUARIOS TIPO JAVI QUE HA DE EJECUTAR CADA DOMINGO
                    elif periodicidad == 'weekly':
                        print(f" {aimharder_user} tiene weekly")
                        #if(today.weekday() == 6 ):
                        if True:
                            #print(f"{fechalog} - Hoy es {today.weekday()}")
                            print("RESERVAS:",reservas)
                            driver_conexion=login_to_aimharder(aimharder_user,aimharder_pass)

                            for i in range(len(reservas)):
                                proxima=dias.get(reservas[i]['dia'])
                                #print("P",proxima)
                                tomorrow = today + timedelta(days=proxima)
                                nextClase = "wds"+tomorrow.strftime("%Y%m%d")
                                print(nextClase," - ",reservas[i])
                                if driver_conexion:
                                    book_class(driver_conexion,reservas[i],nextClase)
                                else:
                                    print(f"Error en login de {aimharder_user}")
                            driver_conexion.quit()
                        else:
                            print("No es domingo")

    except Exception as e:
        print(f"{fechalog} - Error GLOBAL al hacer reserva: {str(e)}")
       #send_email(subject="Error al hacer reserva ❌", body=f"Ocurrió un error GLOBAL al reservar:\n{str(e)}",to_email=email_to_dev)
