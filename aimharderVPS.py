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
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")  # Reemplaza con tu nombre de usuario de MySQL
DB_PASS = os.getenv("DB_PASS") # Reemplaza con tu contraseña de MySQL
DB_NAME = os.getenv("DB_NAME")  # Reemplaza con el nombre de tu base de datos

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor
)
# Default class time
dias_deseados = ['LunesE', 'MiercolEes', 'ViernEes']  # <- Esta línea se actualizará automáticamente
hora_deseada = '08:05 - 09:05'  # Default time
clase_deseada = 'HYROX-EnduranceE'  # Default class name


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

def login_to_aimharder(username, password, clase_deseada, hora_deseada,dias_deseados,email_to):
    # Mapea weekday() a nombres
    week_map = {
        1: 'Lunes',
        2: 'Martes',
        3: 'Miercoles',
        4: 'Jueves',
        5: 'Viernes',
        6: 'Sábado',
        0: 'Domingo'
    }

    today_name = week_map[datetime.today().weekday()]
    #print(f"Hoy es {today_name}")
    #print(f"Los días seleccionados son: {dias_deseados}")
    if today_name not in dias_deseados:
        print(f"⏭️ Hoy es {today_name}, mañana no está en los días seleccionados ({dias_deseados}). No se hace reserva.")
        exit()


    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")  # New headless mode for Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    
    # For VPS environment
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--remote-debugging-address=0.0.0.0")
    
    # Set environment variables for VPS
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOCAL'] = '1'
    
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
        print(f"{fechalog} - Successfully initialized Chromium driver")

    except Exception as e:
        print(f"{fechalog} - Error initializing Chromium driver: {str(e)}")
        sys.exit(1)
    
    try:
        # Navigate to aimharder.com
        driver.get("https://www.aimharder.com/login")
        
        # Wait for the login form to load
        wait = WebDriverWait(driver, 10)
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
            if(today.weekday() == 6):
                #print(f"{fechalog} - Hoy es domingo")
                nextWeek = driver.find_element(By.ID, "nextWeek")
                nextWeek.click()

            tomorrow = today + timedelta(days=1)
            nextClase = "wds"+tomorrow.strftime("%Y%m%d")
            #print(f"{fechalog} - Hoy es {today} y la clase es {nextClase}")
            anchor = driver.find_element(By.CSS_SELECTOR, f"div#weekDays a.{nextClase}")
            anchor.click()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bloqueClase")))
            time.sleep(1)
            print(f"{fechalog} - Clicked day link")
            
            # Find the {clase_deseada}  class
            try:
                # Find all class blocks
                class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")
                # Look for the {clase_deseada}  class at 8:00 - 9:00
                for block in class_blocks:
                    # Check if this block contains the H{clase_deseada}  class name
                    #print(f"{fechalog} - Clase: ", block.text)
                    class_name = block.find_element(By.CLASS_NAME, "rvNombreCl").text.strip()
                    class_horario = block.find_element(By.CLASS_NAME, "rvHora").text.strip()
                    #print("Class: ", class_name+ " - ", class_horario)
               
                    if clase_deseada in class_name and class_horario == hora_deseada:
                        instructor_name = block.find_element(By.CLASS_NAME, "rvCoach").text
                        box_name = block.find_element(By.CLASS_NAME, "rvBox").text  
                        # Find and click the reservation link within this block
                        reserve_link = block.find_element(By.XPATH, ".//a[contains(text(), 'Reservar')]")
                        #driver.execute_script("arguments[0].scrollIntoView();", reserve_link)
                        #print()
                        try:
                             #eucookielaw = driver.find_element(By.ID, 'eucookielaw')
                             #print(eucookielaw.get_attribute('outerHTML'))
                             driver.execute_script("document.getElementById('eucookielaw').style.display = 'none';")
                        except:
                            print("sin cookie")
                        reserve_link.click()
                        print(f"{fechalog} - Clicked on Reservar button")

                        try:
                                # Espera hasta 3 segundos para que el div con id 'infoDialogBox' esté presente en el DOM
                                wait = WebDriverWait(driver,3)
                                wait.until(EC.presence_of_element_located((By.ID, 'infoDialogBox')))
                                # Después de esperar, buscamos el div y verificamos su texto
                                info_dialog = driver.find_element(By.ID, 'infoDialogBox')
                                if "La clase está llena" in info_dialog.text:
                                    print(f"{fechalog} - ❌ Lista de espera llena para la clase {clase_deseada} en {box_name} con el {instructor_name} para mañana a las {class_horario}. ❌")
                                    send_email(   subject="Clase llena en AimHarder ❌",  body=f"La clase {clase_deseada}  en {box_name} con el {instructor_name} fue no pudo reservarse para mañana a las {class_horario} por estar llena.", to_email=email_to  )
                                    
                        except:
                                try:
                                    # Espera hasta 5 segundos a que aparezca el span con el texto "LISTA DE ESPERA"
                                    #lista_espera =   WebDriverWait(driver, 5).until( EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'rvLista') and contains(text(), 'En lista de espera')]")))
                                    lista_espera = WebDriverWait(driver, 5).until( EC.visibility_of_element_located((By.XPATH, "//span[contains(@class, 'rvLista') and contains(text(), 'En lista de espera')]")))
                                    #print("Lista Espera: ",lista_espera)
                                    print(f"{fechalog} - ✅ Estas anotado en lista de espera par la clase {clase_deseada}  en {box_name} con el {instructor_name} para mañana a las {class_horario}. ✅")
                                    send_email( subject="Reserva AimHarder realizada ✅", body=f"✅ Estas anotado en lista de espera par la clase {clase_deseada}  en {box_name} con el {instructor_name} para mañana a las {class_horario}. ✅",to_email=email_to)
                                except:
                                    #print("El div con el aviso no ha aparecido en 3 segundos.")
                                    print(f"{fechalog} - ✅ La clase {clase_deseada}  en {box_name} con el {instructor_name} fue reservada correctamente para mañana a las {class_horario}. ✅")
                                    send_email(subject="Reserva AimHarder realizada ✅",body=f"La clase {clase_deseada}  en {box_name} con el {instructor_name} fue reservada correctamente para mañana a las {class_horario}.",to_email=email_to)
                        break
                        
                    else:
                        print(f"{fechalog} - Could not find {clase_deseada}  class in the list")
                    
            except Exception as e:
                print(f"{fechalog} - Error finding button or clicking RESERVAR {clase_deseada} a las {hora_deseada}   class: {str(e)}")
                send_email(
                    subject="Error al hacer reserva ❌",
                    body=f"Ocurrió un error al reservar:\n{str(e)}",
                    to_email=email_to_dev
                )
            
        except Exception as e:
            print(f"{fechalog} - Error during login process: {str(e)}")
            driver.quit()
            return
            
    except Exception as e:
        print(f"{fechalog} - An error occurred: {str(e)}")
    finally:
        # Close the browser
        driver.quit()

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
                cur.execute("SELECT u.id,u.usuario,u.full_name,u.email,c.clase,c.dias,c.hora,c.aimharder_user,c.aimharder_pass from usuarios u LEFT JOIN configs c ON u.id=c.id")
                configs = cur.fetchall()

                for config in configs:
                    user_id = config['id']
                    dias_deseados = json.loads(config['dias'])
                    hora_deseada = config['hora']
                    clase_deseada = config['clase']
                    aimharder_user = config['aimharder_user']
                    aimharder_pass = config['aimharder_pass']
                    email_to = config['email']
                    #print(f"Configuración para el usuario {user_id}: {dias_deseados}, {hora_deseada}, {clase_deseada}")
                    print(f"{fechalog} - [{user_id}] Ejecutando con Días: {dias_deseados}   Hora: {hora_deseada}   Clase: {clase_deseada}")
                    login_to_aimharder(aimharder_user, aimharder_pass, clase_deseada, hora_deseada, dias_deseados,email_to)

    except Exception as e:
        print(f"{fechalog} - Error GLOBAL al hacer reserva: {str(e)}")
        send_email(
            subject="Error al hacer reserva ❌",
            body=f"Ocurrió un error GLOBAL al reservar:\n{str(e)}",
            to_email=email_to_dev
        )
