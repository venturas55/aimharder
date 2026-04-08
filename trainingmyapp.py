from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, TimeoutException
import time
from datetime import date,datetime, timedelta
import os
import subprocess
import sys
import pymysql
import tempfile
import shutil, glob
from dotenv import load_dotenv
import unicodedata
import re
import traceback


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

def normalize(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

    # 🔥 elimina TODO lo que no sea número, letra, : o -
    text = re.sub(r'[^a-z0-9:-]', '', text)
    text=text.replace("-", "")

    return text

def get_text_or_empty(parent, by, value):
    elements = parent.find_elements(by, value)
    return elements[0].text.strip() if elements else ""

def book_class_trainning(driver, reserva_deseada):
    driver.get("https://www.trainingymapp.com/webtouch/actividades")
    wait = WebDriverWait(driver, 20)
    try:
        actividades_icon = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[@class='menu-item-icon']/i[contains(@class, 'icon-menu-horarios')]/.."
        )))
        actividades_icon.click()
        print(f"{fechalog} - Click en Actividades vía icono en book_class_trainning")
    except TimeoutException:
        print(f"{fechalog} - ❌ No se encontró el icono de Actividades en book_class_trainning")
    #driver.save_screenshot("/tmp/aimharder_book_class.png")
    # Esperar a que carguen las clases
    bloques = wait.until(
    EC.presence_of_all_elements_located(
        (By.XPATH, '//*[@id="scrollCalendar"]//div[contains(@class,"item-dia")][3]//div[contains(@class,"item-dias")]')
    )
)
    for bloque in bloques:
        try:
            # 🕒 HORARIO
            horario = normalize(bloque.find_element(By.CSS_SELECTOR, ".etiquetaHora").text)

            # 🏷️ NOMBRE CLASE
            nombre = normalize(bloque.find_element(By.CSS_SELECTOR, ".actividad span").text)
            print(nombre,horario,"   ==   >", reserva_deseada['clase'], reserva_deseada['hora'])
            
            # Filtrar lo que buscas
            if reserva_deseada['clase'] in nombre and reserva_deseada['hora'] in horario:

                print(f"\t\tEncontrada: {nombre} - {horario}")

                texto_bloque = bloque.text

                # ❌ Clase completa
                if "Completa" in texto_bloque:
                    print("La clase está completa")
                    break

                # ✅ Reservar
                if "RESERVAR YA" in texto_bloque:
                    print("Intentando reservar...")
                    print("---- BLOQUE ----")
                    print("Nombre:", nombre)
                    print("Hora:", horario)
                    print("Texto:", bloque.get_attribute("innerText"))
                    print("----------------")
                    # Esperar a que desaparezca el overlay
                    try:
                        wait.until(
                        EC.invisibility_of_element_located((By.CLASS_NAME, "modal-backdrop"))
                        )
                    except TimeoutException:
                        print("⚠️ No desapareció el overlay, intentando click fuera")
                    driver.execute_script("document.body.click();")
                    # 1. Click en el primer puesto libre
                    driver.execute_script("arguments[0].scrollIntoView(true);", bloque)
                    time.sleep(0.5)
                    try:
                        bloque.click()
                    except:
                        driver.execute_script("arguments[0].click();", bloque)
                    #primer_libre = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#puestos-horario .puesto_libre")))
                    #primer_libre.click()
                    wait.until(EC.presence_of_element_located((By.ID, "puestos-horario")))

                    libree = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"puesto_libre")]')))
                    libree.click()
                    libree = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@ng-click="changePlace(place)"]')))
                    driver.execute_script("arguments[0].click();", libree)
                    print("Seleccionado el primer puesto libre")
                    driver.save_screenshot("/tmp/aimharder_puesto_libre.png")

                    # 2. Click en el botón reservar
                    try:
                        reservar = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@ng-click="actionSelectPlace()"]')))
                        driver.execute_script("arguments[0].click();", reservar)
                        driver.save_screenshot("/tmp/aimharder_reservar.png")
                    except (StaleElementReferenceException, ElementClickInterceptedException):
                        print("⚠️ Retry click reservar")
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", reservar)
                        driver.save_screenshot("/tmp/aimharder_reservar.png")
                    # Esperar a que aparezca el modal
                    try:
                        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Por favor, espere')]")))
                        print("⏳ Modal detectado")

                        # Esperar un poco a que termine la acción
                        time.sleep(2)

                        # Click fuera del modal
                        driver.execute_script("document.body.click();")
                        print("✅ Click fuera del modal")
                        driver.save_screenshot("/tmp/aimharder_reservar2.png")

                        # Esperar a que desaparezca el modal
                        wait.until(
                            EC.invisibility_of_element_located((By.XPATH, "//span[contains(text(),'Por favor, espere')]"))
                        )
                        print("✅ Modal desaparecido")
                        
                    except TimeoutException:
                        print("⚠️ No apareció el modal de espera")
                    
                    # Click fuera del modal
                    driver.execute_script("document.body.click();")
                    print("✅ Click fuera del modal")
                    driver.save_screenshot("/tmp/aimharder_reservar2.png")
                                        # Esperar a que aparezca el modal
                    try:
                        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Por favor, espere')]")))
                        print("⏳ Modal detectado")

                        # Esperar un poco a que termine la acción
                        time.sleep(2)

                        # Click fuera del modal
                        driver.execute_script("document.body.click();")
                        print("✅ Click fuera del modal")
                        driver.save_screenshot("/tmp/aimharder_reservar2.png")

                        # Esperar a que desaparezca el modal
                        wait.until(
                            EC.invisibility_of_element_located((By.XPATH, "//span[contains(text(),'Por favor, espere')]"))
                        )
                        print("✅ Modal desaparecido")
                        
                    except TimeoutException:
                        print("⚠️ No apareció el modal de espera")
                    
                    return "Reserva realizada"
                
        except Exception as e:
            print("Error en bloque:")
            traceback.print_exc()
            return "Error al intentar reservar"
                    
def login_to_trainning(username, password):

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
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/118.0.5993.117 Safari/537.36")
    
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
        driver.get("https://www.trainingymapp.com/webtouch/")
        
        # Wait for the login form to load
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "caja-login")))
            print(f"{fechalog} - Login form found")
        except Exception as e:
            print(f"{fechalog} - Could not find login form: {str(e)}")
            driver.quit()
            return
            
        # Enter username and password
        try:
            # Enter username
            username_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@ng-model='user']")))
            username_field.clear()
            username_field.send_keys(username)
            # Enter password
            password_field = driver.find_element(By.XPATH, "//input[@ng-model='pass']")
            password_field.clear()
            password_field.send_keys(password)
            #password_field.send_keys(Keys.RETURN)
            # Click login (case insensitive)
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH,"//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login') "    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'entrar')]")))
            login_button.click()
            # 🔥 Esperar confirmación real de login
            # abrir dropdown
            dropdown_btn = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                "//button[@dropdown-toggle='dropdown-toggle']"
            )))

            driver.execute_script("arguments[0].click();", dropdown_btn)
            #club_option = wait.until(EC.element_to_be_clickable((By.XPATH,"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'nou mestalla')]")))
            club_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'activaclub nou mestalla')]")))
            #driver.save_screenshot("/tmp/aimharder_dropdown.png")
            driver.execute_script("arguments[0].click();", club_option)

            print(f"{fechalog} - Hace click en nou mestalla")
            #driver.save_screenshot("/tmp/aimharder_wait.png")


                # --- Ir a Actividades usando el icono ---
            try:
                actividades_icon = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[@class='menu-item-icon']/i[contains(@class, 'icon-menu-horarios')]/.."
                )))
                actividades_icon.click()
                print(f"{fechalog} - Click en Actividades vía icono")
                #driver.save_screenshot("/tmp/actividades_icon.png")
            except TimeoutException:
                print(f"{fechalog} - ❌ No se encontró el icono de Actividades")
                #driver.save_screenshot("/tmp/actividades_icon_fail.png")
                
            print(f"{fechalog} - Hace click en actividades")
            #driver.save_screenshot("/tmp/aimharder_actividades_final.png")
            
            # Esperar a que aparezca el modal de "Por favor espere"
            #try:
            #    wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Por favor espere un momento')]")))
            #    print("⏳ Modal de espera activo")
            #except TimeoutException:
            #    print("⚠️ No apareció el modal")

            # Esperar a que el modal desaparezca o simular click fuera
            time.sleep(3)  # breve espera para asegurar que el modal está completamente cargado
            driver.execute_script("document.body.click();")  # click fuera del modal
            print("✅ Click fuera del modal hecho")

            # Ahora hacemos click en el icono de actividades (robusto, usando el i.fa adecuado)
            #actividades_icon.click()
            time.sleep(3)  # breve espera para asegurar que el modal está completamente cargado
            print("✅ Click en Actividades realizado")
            #driver.save_screenshot("/tmp/aimharder_actividades_final2.png")

                  
            return driver  # ✅ devolver SOLO si todo fue bien   
        except Exception as e:
            print(f"{fechalog} - Error during login process: {repr(e)}")
            print("URL en el fallo:", driver.current_url)
            section_body = driver.find_element(By.TAG_NAME, "section").get_attribute("innerHTML")
            print(section_body[:9000]) # solo una parte
            driver.save_screenshot("/tmp/aimharder_error_login.png")
            driver.quit()
            return None
            
    except Exception as e:
        print(f"{fechalog} - An error occurred: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None

if __name__ == "__main__":
    # Example usage - replace these with your actual credentials
    try:
        with conn:
            with conn.cursor() as cur:
                #cur.execute("SELECT u.id,u.usuario,u.full_name,u.email,c.clase,c.dias,c.hora,c.aimharder_user,c.aimharder_pass,c.gym,c.periodicidad,c.tipo_app from usuarios u LEFT JOIN configs c ON u.id=c.id")
                cur.execute("SELECT * from usuarios u LEFT JOIN configs c ON u.id=c.user_id")
                usuarios = cur.fetchall()
                for usuario in usuarios:
                    user_id = usuario['user_id']
                    aimharder_user = usuario['aimharder_user']
                    aimharder_pass = usuario['aimharder_pass']
                    periodicidad = usuario['periodicidad']
                    email_to = usuario['email']
                    tipo_app = usuario['tipo_app']

                    cur.execute("SELECT * from bookings where user_id=%s", (user_id,))
                    reservas = cur.fetchall()

                    if tipo_app == 'trainingmyapp':
                        for item in reservas:
                            if item['activo'] == 1:
                                texto = item['dia'] + " " + item['hora']
                                dia_str, horas = texto.split(" ", 1)
                                hora_inicio = horas.split("/")[0].strip()

                                # 👇 adaptamos tu mapeo
                                dia_objetivo = dias[dia_str] - 1

                                dias_hasta = (dia_objetivo - ahora.weekday()) % 7

                                hora_evento = datetime.strptime(hora_inicio, "%H:%M").time()

                                fecha_evento = ahora + timedelta(days=dias_hasta)
                                fecha_evento = fecha_evento.replace(
                                    hour=hora_evento.hour,
                                    minute=hora_evento.minute,
                                    second=0,
                                    microsecond=0
                                )

                                # Si es hoy pero ya pasó la hora → siguiente semana
                                if dias_hasta == 0 and fecha_evento < ahora:
                                    fecha_evento += timedelta(days=7)

                                diferencia = fecha_evento - ahora

                                print(ahora, "vs", fecha_evento, "=>", diferencia)

                                if diferencia.total_seconds() > 48 * 3600:
                                    print(f"{fechalog} - ❌ No se encontró clase a reservar en las proximas 48h")
                                else:
                                    item['clase']=normalize(item['clase'])
                                    item['hora']=normalize(item['hora'])
                                    print(f"{fechalog} - ✅ Clase de {item['clase']} a reservar en las proximas 48h [ a las {item['hora']}] ")
                                    driver = login_to_trainning(aimharder_user, aimharder_pass)

                                    if not driver:
                                        print(f"Error en login de {aimharder_user}")

                                    try:
                                        resultado = book_class_trainning(driver, item)
                                        print("Resultado:", resultado)

                                    finally:
                                        driver.quit()
                            else:
                                print(f"{fechalog} - 🤷‍♂️🤷 No hay clases a reservar")

    except Exception as e:
        print(f"{fechalog} - Error GLOBAL: {str(e)}")