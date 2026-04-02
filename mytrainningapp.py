from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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
user_env = os.getenv("AIMHARDER_USERNAME")
passw_env = os.getenv("AIMHARDER_PASSWORD")

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

    return text

def get_text_or_empty(parent, by, value):
    elements = parent.find_elements(by, value)
    return elements[0].text.strip() if elements else ""

def book_class(driver, reserva_deseada, nextClase):
    wait = WebDriverWait(driver, 20)

    try:
        wait.until(EC.presence_of_element_located((By.ID, "weekDays")))
    except TimeoutException:
        return {"status": "error", "msg": "No cargó weekDays"}
    
    dias_disponibles = driver.find_elements(By.CSS_SELECTOR, "div#weekDays a")
    print("Días disponibles:")
    for d in dias_disponibles:
        print(d.get_attribute("class"))


    try:
        anchor = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"div#weekDays a.{nextClase}")
            )
        )
        anchor.click()

    except TimeoutException:
        clases = [d.get_attribute("class") for d in dias_disponibles]
        return {
            "status": "error",
            "msg": f"No existe {nextClase}. Disponibles: {clases}"
        }
    
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

        print(f"DEBUG -> '{class_horario}' vs '{reserva_deseada['hora']}'")
        #print(f"LEN -> {len(class_horario)} vs {len(reserva_deseada['hora'])}")
        if reserva_deseada['clase'] == normalize(class_name) and normalize(class_horario) == reserva_deseada['hora']:
            print("Clase encontrada")
            instructor_name = get_text_or_empty(block, By.CLASS_NAME, "rvCoach")
            box_name = get_text_or_empty(block, By.CLASS_NAME, "rvBox")

            # Ocultar cookies
            try:
                driver.execute_script("document.getElementById('eucookielaw').style.display = 'none';")
            except Exception:
                pass

            try:
                reserve_link = block.find_element(By.XPATH, ".//a[contains(@onclick, 'bookClass')]")
                reserve_link.click()
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
                wait.until(
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
        else:
            print("Clase no encontrada")
    return {
        "status": "no_encontrada",
        "clase": reserva_deseada['clase'],
        "hora": reserva_deseada['hora']
    }

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
            print("usuario")
            # Enter password
            password_field = driver.find_element(By.XPATH, "//input[@ng-model='pass']")
            password_field.clear()
            password_field.send_keys(password)
            print("password")
            #password_field.send_keys(Keys.RETURN)
            # Click login (case insensitive)
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH,"//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login') "    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'entrar')]")))
            login_button.click()
            print("parece que loguea")
            # 🔥 Esperar confirmación real de login
            # abrir dropdown
            dropdown_btn = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                "//button[@dropdown-toggle='dropdown-toggle']"
            )))

            driver.execute_script("arguments[0].click();", dropdown_btn)
            print(f"{fechalog} - Hace click en dropdown")
            #club_option = wait.until(EC.element_to_be_clickable((By.XPATH,"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'nou mestalla')]")))
            club_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'activaclub nou mestalla')]")))
            driver.save_screenshot("/tmp/aimharder_dropdown.png")
            driver.execute_script("arguments[0].click();", club_option)

            print(f"{fechalog} - Hace click en nou mestalla")
            driver.save_screenshot("/tmp/aimharder_wait.png")


                # --- Ir a Actividades usando el icono ---
            try:
                actividades_icon = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[@class='menu-item-icon']/i[contains(@class, 'icon-menu-horarios')]/.."
                )))
                actividades_icon.click()
                print(f"{fechalog} - Click en Actividades vía icono")
                driver.save_screenshot("/tmp/actividades_icon.png")
            except TimeoutException:
                print(f"{fechalog} - ❌ No se encontró el icono de Actividades")
                driver.save_screenshot("/tmp/actividades_icon_fail.png")
                
            print(f"{fechalog} - Hace click en actividades")
            driver.save_screenshot("/tmp/aimharder_actividades_final.png")
            
            # Esperar a que aparezca el modal de "Por favor espere"
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Por favor espere un momento')]")))
                print("⏳ Modal de espera activo")
            except TimeoutException:
                print("⚠️ No apareció el modal")

            # Esperar a que el modal desaparezca o simular click fuera
            time.sleep(1)  # breve espera para asegurar que el modal está completamente cargado
            driver.execute_script("document.body.click();")  # click fuera del modal
            print("✅ Click fuera del modal hecho")

            # Ahora hacemos click en el icono de actividades (robusto, usando el i.fa adecuado)
            actividades_icon = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                "//div[@class='menu-item-icon']/i[contains(@class,'icon-menu-horarios')]"
            )))
            driver.execute_script("arguments[0].click();", actividades_icon)
            print("✅ Click en Actividades realizado")
            driver.save_screenshot("/tmp/after_click_actividades.png")
                  
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
                # Obtener configuraciones de todos los usuarios que tengan una
             
                    user_id = 3
                    aimharder_user = user_env
                    aimharder_pass = passw_env
                    periodicidad = 'daily'
                    email_to = email_to_dev

                    cur.execute("SELECT * from bookings where user_id=%s", (user_id,))
                    reservas = cur.fetchall()

                    #print(reservas)
                    #dias_deseados = [item['dia'] for item in reservas]
                    #print(f"{fechalog} - [{user_id}] Ejecutando con Días: {dias_deseados}")

                    # ------------------ DAILY ------------------
                    if periodicidad == 'daily' and int(ahora.strftime("%H"))<20:
                        print(f" ⏭️ {aimharder_user} tiene daily")

                        tomorrow_name = tomorrow_week_map[today.weekday()]

                        clase_manana ={'id': 22, 'user_id': 3, 'dia': 'Sabado', 'hora': '09:00 - 09:30', 'clase': 'Quick core', 'activo': 1, 'created_at': datetime(2026, 3, 17, 12, 12, 49)}
                        print("clase_manana:",clase_manana)
                        clase_manana['clase']=normalize(clase_manana['clase'])
                        clase_manana['hora']=normalize(clase_manana['hora'])
                        print("normalize clase_manana:",clase_manana)

                        if not clase_manana:
                            print(f"{fechalog} - No hay configuración para mañana")

                        if not clase_manana['activo']:
                            print(f"{fechalog} - Día no activo → no se reserva")

                        driver = login_to_trainning(aimharder_user, aimharder_pass)

                        if not driver:
                            print(f"Error en login de {aimharder_user}")

                        try:
                            tomorrow = today + timedelta(days=1)
                            nextClase = "wds" + tomorrow.strftime("%Y%m%d")

                            resultado = book_class(driver, clase_manana, nextClase)
                            print("Resultado:", resultado)

                        finally:
                            driver.quit()
    except Exception as e:
        print(f"{fechalog} - Error GLOBAL: {str(e)}")