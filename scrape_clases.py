from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import traceback
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
    #print("User data dir que vamos a usar:", tmpdir)
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
            #print(f"{fechalog} - Login form found")
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
                #print(f"{fechalog} - Cookie removal button clicked")
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
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ahPicTimetable")))
            print(f"{fechalog} - Login successful")
            
            # Click reservations
            timtable_link = driver.find_element(By.CLASS_NAME, "ahPicTimetable")
            timtable_link.click()
            #print(f"{fechalog} - Clicked timetable_link link")
            

        
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

def scrape_current_classes(driver, gym, tmpdir):
    try:
        driver.get(f"https://{gym}.aimharder.com/timetable")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "timetable")))
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "timeRowDesc")))
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "ahBloqueClase")))


        clases_unicas = set()
        horas_unicas = set()

        # Contenedor principal
        timetable = driver.find_element(By.ID, "timetable")
        #print(timetable.get_attribute("innerHTML")[:1000])
        # Todas las filas de tiempo
        time_rows = timetable.find_elements(By.CLASS_NAME, "timeRow")



        for row in time_rows:
            try:
                # Verificar si existe el elemento antes de usarlo
                time_desc_elements = row.find_elements(By.CLASS_NAME, "timeRowDesc")
                #print(time_desc_elements.get_attribute("innerHTML")[:100])
                
                if not time_desc_elements:
                    continue  # saltar filas inválidas
                
                hora_name = time_desc_elements[0].text.strip()
                print(hora_name)
                # Espera hasta que haya al menos un bloque de clase visible
                # Todos los bloques de clase dentro de esa fila
                bloques = row.find_elements(By.CLASS_NAME, "ahBloqueClase")
                for block in bloques:
                    class_name = block.find_element(By.CLASS_NAME, "pbcNombreCl").text.strip()
                    clases_unicas.add(class_name)
                    horas_unicas.add(hora_name)
            except Exception as e:
                print(f"Error al procesar un timeRow: {e}")

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
        cur.execute("SELECT * FROM usuarios u left join configs c ON c.id=u.id")
        result = cur.fetchall()
    conn.close()
    return result          

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
            driver.save_screenshot("/tmp/aimharder_actividades_final2.png")

                  
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

def scrape_current_classes_trainning(driver, tmpdir):
    try:
        driver.get("https://www.trainingymapp.com/webtouch/actividades")
        wait = WebDriverWait(driver,15)

        clases = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.actividad > span")))
        horas = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.horaPlazas > span")))

        clases_unicas = set()
        horas_unicas = set()

        print(clases)
        print(horas)
        for item in clases:
            try:
                clases_unicas.add(item.text.strip())
            except Exception as e:
                print(f"Error al procesar una clase: {e}")
        for item in horas:
            try:
                horas_unicas.add(item.text.strip())
            except Exception as e:
                print(f"Error al procesar una hora: {e}")
        return clases_unicas, horas_unicas

    except Exception as e:
        print("❌ ERROR COMPLETO:")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    usuarios=get_usuarios()
    for usuario in usuarios:
        print(f"{usuario['id']}   con nombre {usuario['full_name']}  {usuario['email']}  {usuario['gym']} {usuario['aimharder_user']} ")
        if(usuario['tipo_app']=="aimharder"):
            result = login_to_aimharder(usuario['aimharder_user'],usuario['aimharder_pass'])
        else:
            result = login_to_trainning(usuario['aimharder_user'],usuario['aimharder_pass'])

        if not result:
            print(f"{fechalog} - Error login usuario {usuario['usuario']}")
            continue

        driver, tmpdir = result
        if(usuario['tipo_app']=="aimharder"):
            result = scrape_current_classes(driver, usuario['gym'], tmpdir)
        else:
            result = scrape_current_classes_trainning(driver, tmpdir)

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






