from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from datetime import date,datetime, timedelta
import subprocess
import tempfile
import os
import shutil, glob
import sys
import pymysql
from dotenv import load_dotenv
load_dotenv()

ahora = datetime.now()
today = date.today()
fechalog= str(today) + " " + ahora.strftime("%H:%M")

gym="hybridboxgraudefault"


# Conexión con MySQL usando PyMySQL
def get_db_connection():
    return pymysql.connect(
        host= os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor  # Para obtener resultados como diccionarios
    )

for old_profile in glob.glob("/tmp/aimharder-profile-*"):
    try:
        shutil.rmtree(old_profile)
    except Exception:
        pass

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
            

        
            return driver,tmpdir  # ✅ devolver SOLO si todo fue bien   
        except Exception as e:
            print(f"{fechalog} - Error during login process: {str(e)}")
            driver.quit()
            return
            
    except Exception as e:
        print(f"{fechalog} - An error occurred: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None


def scrape_current_classes(driver,gym,tmpdir):
       
    try:
        # Abrir la página web
        #driver.get("https://"+gym+".aimharder.com/schedule")
        driver.get("https://"+gym+".aimharder.com/timetable") #necesita logarse

        # Esperar a que la página cargue completamente y los bloques estén disponibles
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bloqueClase")))

        # Crear un set para almacenar las clases únicas
        clases_unicas = set()
        horas_unicas = set()

        # Encontrar todos los bloques de la semana en curso
        class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")

        # Recorrer los bloques y extraer las clases rvNombreCl
        for block in class_blocks:
            try:
                class_name = block.find_element(By.CLASS_NAME, "pbcNombreCl").text.strip()
                hora_name = block.find_element(By.CLASS_NAME, "timeRowDesc").text.strip()
                clases_unicas.add(class_name)  # Añadir al set, asegurando que sean únicos
                horas_unicas.add(hora_name)  # Añadir al set, asegurando que sean únicos
            except Exception as e:
                print(f"Error al procesar un bloque: {e}")
        # Cerrar el driver después de la tarea
        return clases_unicas,horas_unicas
    except Exception as e:
        print(f"Scrap FlaskApp - An error occurred: {str(e)}")
        return None
    finally:
        # Close the browser
        driver.quit()
        shutil.rmtree(tmpdir, ignore_errors=True)

def save_classes_to_db(datos):
    conn = get_db_connection()
    with conn.cursor() as cur:

        user_id = datos['id']
        usuario = datos['usuario']

        clases = list(set(datos['clases']))  # evitar duplicados en input
        horas = list(set(datos['horas']))

        # --- CLASES ---

        # Insertar nuevas (ignora duplicados por UNIQUE)
        if clases:
            values = [(user_id, usuario, c) for c in clases]
            cur.executemany(
                "INSERT IGNORE INTO current_classes (user_id, usuario, class_name) VALUES (%s,%s,%s)",
                values
            )

            # Borrar las que ya no están
            placeholders = ','.join(['%s'] * len(clases))
            cur.execute(
                f"DELETE FROM current_classes WHERE user_id=%s AND class_name NOT IN ({placeholders})",
                [user_id] + clases
            )
        else:
            # Si no hay clases, borrar todas
            cur.execute("DELETE FROM current_classes WHERE user_id=%s", (user_id,))

        # --- HORAS ---

        if horas:
            values = [(user_id, usuario, h) for h in horas]
            cur.executemany(
                "INSERT IGNORE INTO current_hours (user_id, usuario, hora) VALUES (%s,%s,%s)",
                values
            )

            placeholders = ','.join(['%s'] * len(horas))
            cur.execute(
                f"DELETE FROM current_hours WHERE user_id=%s AND hora NOT IN ({placeholders})",
                [user_id] + horas
            )
        else:
            cur.execute("DELETE FROM current_hours WHERE user_id=%s", (user_id,))

        conn.commit()
        print(f"SCRAPPING - Clases actualizadas para {datos['usuario']}:\nClases: {datos['clases']}\nHoras: {datos['horas']}")

    conn.close() 

def get_usuarios():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM usuarios u left join configs c ON c.id=u.id")
        result = cur.fetchall()
    conn.close()
    return result          


if __name__ == "__main__":
    usuarios=get_usuarios()
    for usuario in usuarios:
        print(f"{usuario['id']}   con nombre {usuario['full_name']}  {usuario['email']}  {usuario['gym']} {usuario['aimharder_user']} ")
        result = login_to_aimharder(usuario['aimharder_user'],usuario['aimharder_pass'])

        if not result:
            print(f"{fechalog} - Error login usuario {usuario['usuario']}")
            continue

        driver, tmpdir = result
        result = scrape_current_classes(driver, usuario['gym'], tmpdir)

        if not result:
            print(f"{fechalog} - Error scraping usuario {usuario['usuario']}")
            continue

        clases, horas = result

        datos = {
            "id": usuario['id'],
            "gym": usuario['gym'],
            "usuario":usuario['usuario'],
            "clases":clases,
            "horas":horas
        }
        #print(datos)
        save_classes_to_db(datos)






