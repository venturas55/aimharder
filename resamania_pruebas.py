from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import date,datetime, timedelta
import time
from urllib.parse import quote
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


def login_to_resamania(username, password,gym):

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
        gym_encoded = quote(gym)

        url = (
            "https://api.resamania.com/oauth/login/enjoy?"
            "client_id=142_vrmofh03k8omedrabc6ei1hq6l5aogu9zxmspp74cfu3i7bakur"
            f"&redirect_uri=https://member.resamania.com/{gym_encoded}/"
            "&response_type=code&locale=es"
        )

        driver.get(url)
        #driver.get(f"https://api.resamania.com/oauth/login/enjoy?client_id=142_vrmofh03k8omedrabc6ei1hq6l5aogu9zxmspp74cfu3i7bakur&redirect_uri=https://member.resamania.com/{gym}/&response_type=code&locale=es")
        
        # Wait for the login form to load
        try:
            wait.until(EC.presence_of_element_located((By.ID, "login_step_login_username")))
            print(f"{fechalog} - Login form found")
        except Exception as e:
            print(f"{fechalog} - Could not find login form: {str(e)}")
            driver.quit()
            return
            
        # Enter username and password
        try:
            # Enter username
            username_field = wait.until(EC.presence_of_element_located((By.ID, "login_step_login_username")))
            username_field.clear()
            username_field.send_keys(username)

            login_button = wait.until(EC.element_to_be_clickable((By.ID,"login_step_login_submit")))
            login_button.click()

            # Enter password
            password_field = driver.find_element(By.ID, "_password")
            password_field.clear()
            password_field.send_keys(password)
            #password_field.send_keys(Keys.RETURN)
            login_button = wait.until(EC.element_to_be_clickable((By.ID,"submit")))
            login_button.click()
            driver.save_screenshot("/tmp/resamania_wait.png")
            return driver,tmpdir  # ✅ devolver SOLO si todo fue bien   
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

def scrape_current_classes_resemania(driver, gym, tmpdir):
    try:
        clases_unicas = set()
        horas_unicas = set()
        #driver.get(f"https://member.resamania.com/{gym}/planning?club=%2Fenjoy%2Fclubs%2F2374")
        driver.save_screenshot("/tmp/resamania_scrap.png")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "mui-component-select-activity")))
        #PRIMERO TODAS LAS ACTIVIDADES
        select_clicable=driver.find_element( By.ID,"mui-component-select-activity")
        select_clicable.click()
        ul = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//ul[@role='listbox']")    ))

        items = ul.find_elements(By.TAG_NAME, "li")

        for item in items:
            texto = item.text.strip()
            if texto:
                clases_unicas.add(texto)
        
        #SEGUNDO EL SCROLL Y TAL
       
        containerScrolleable = driver.execute_script("""
                return Array.from(document.querySelectorAll('div'))
                .find(el =>
                    window.getComputedStyle(el).overflowY === 'auto'
                );
                """)
        #tarjetas = driver.find_elements(By.XPATH, "//div[.//button[contains(.,'Inscribirse')]]")
        #print("NUM TARJETAS:", len(tarjetas))
        for i in range(0, 3000, 500):
            driver.execute_script("""
                arguments[0].scrollTop = arguments[1];
            """, containerScrolleable, i)
            time.sleep(0.5)
            driver.save_screenshot("/tmp/resamania_scrap{i}.png")
            
            #SEGUNDO TODAS LAS HORAS
            tarjetas = driver.find_elements( By.XPATH,  "//div[.//button[contains(.,'Inscribirse')]]")

            for tarjeta in tarjetas:
                try:
                    hora = tarjeta.find_element(By.XPATH, ".//h5").text.strip()
                    if hora:
                        horas_unicas.add(hora)
                except:
                    print("H5 Horas no encontradas")
                    continue






        #tarjetas = driver.find_elements(By.XPATH, "//div[.//button[contains(.,'Inscribirse')]]")

        #print("NUM TARJETAS:", len(tarjetas))
        #driver.save_screenshot("/tmp/resamania_scrap2.png")
      
    



        


        print("DEBUG - Clases encontradas:", clases_unicas)
        print("DEBUG - Horas encontradas:", horas_unicas)
        return clases_unicas, horas_unicas

    except Exception as e:
        print("❌ ERROR COMPLETO:")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()
        shutil.rmtree(tmpdir, ignore_errors=True)

def save_classes_to_db(datos):
    if datos != None:
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
                cur.execute(f"DELETE FROM current_classes WHERE user_id=%s AND class_name NOT IN ({placeholders})", [user_id] + clases )

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
    
            conn.commit()
            print(f"SCRAPPING - Clases actualizadas para {datos['usuario']}:\nClases: {datos['clases']}\nHoras: {datos['horas']}")

        conn.close() 

def get_usuarios():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM usuarios u left join configs c ON c.user_id=u.id")
        result = cur.fetchall()
    conn.close()
    return result          

if __name__ == "__main__":
    usuarios=get_usuarios()
    for usuario in usuarios:
        result = None
        print(f"{usuario['id']}   con nombre {usuario['full_name']}  {usuario['email']}  {usuario['gym']} {usuario['aimharder_user']} ")
       
        if(usuario['tipo_app']=="resamania"):
            result = login_to_resamania(usuario['aimharder_user'],usuario['aimharder_pass'],usuario['gym'])

        if not result:
            print(f"{fechalog} - Error login usuario {usuario['usuario']}")
            continue

        driver, tmpdir = result
      
        if(usuario['tipo_app']=="resamania"):
            result = scrape_current_classes_resemania(driver,usuario['gym'],tmpdir)
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






