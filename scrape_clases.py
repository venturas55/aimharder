from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import tempfile
import os
import shutil, glob
import sys
import pymysql
from dotenv import load_dotenv
load_dotenv()


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

for old_profile in glob.glob("/tmp/aimharderFlask-profile-*"):
    try:
        shutil.rmtree(old_profile)
    except Exception:
        pass

def scrape_current_classes(gym):
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
    tmpdir = tempfile.mkdtemp(prefix="aimharder-Flask-profile-")
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
        #print("Scrap FlaskApp - Successfully initialized Chromium driver")

    except Exception as e:
        print("Scrap  FlaskApp - Error initializing Chromium driver: {str(e)}")
        #sys.exit(1)
    
    try:
        # Abrir la página web
        driver.get("https://"+gym+".aimharder.com/schedule")

        # Esperar a que la página cargue completamente y los bloques estén disponibles
        WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bloqueClase")))

        # Crear un set para almacenar las clases únicas
        clases_unicas = set()
        horas_unicas = set()

        # Encontrar todos los bloques de la semana en curso
        class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")

        # Recorrer los bloques y extraer las clases rvNombreCl
        for block in class_blocks:
            try:
                class_name = block.find_element(By.CLASS_NAME, "rvNombreCl").text.strip()
                hora_name = block.find_element(By.CLASS_NAME, "rvHora").text.strip()
                clases_unicas.add(class_name)  # Añadir al set, asegurando que sean únicos
                horas_unicas.add(hora_name)  # Añadir al set, asegurando que sean únicos
            except Exception as e:
                print(f"Error al procesar un bloque: {e}")
        # Cerrar el driver después de la tarea
        return clases_unicas,horas_unicas
    except Exception as e:
        print("Scrap FlaskApp - An error occurred: {str(e)}")
    finally:
        # Close the browser
        driver.quit()
        shutil.rmtree(tmpdir, ignore_errors=True)

def save_classes_to_db(datos):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM current_classes where user_id=%s",(datos['id'],))  # Limpiamos las tablas
        cur.execute("DELETE FROM current_hours where user_id=%s",(datos['id'],)) 
        for c in datos['clases']:
            cur.execute("INSERT INTO current_classes (user_id,usuario,class_name) VALUES (%s,%s,%s)", (datos['id'],datos['usuario'],c,))
        for h in datos['horas']:
            cur.execute("INSERT INTO current_hours (user_id,usuario,hora) VALUES (%s,%s,%s)", (datos['id'],datos['usuario'],h,))
        conn.commit()



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
        print(f"{usuario['id']}   con nombre {usuario['full_name']}  {usuario['email']}  {usuario['gym']}")
        clases,horas = scrape_current_classes(usuario['gym'])
        datos = {
            "id": id,
            "gym": gym,
            "usuario":usuario,
            "clases":clases,
            "horas":horas
        }
        print(datos)
        save_classes_to_db(datos)
        print("SCRAPPING - Clases actualizadas:", clases, " y horas " ,horas)






