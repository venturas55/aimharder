from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from datetime import date,datetime, timedelta
from urllib.parse import quote
import os
import subprocess
import sys
import pymysql
import json
import smtplib
import tempfile
import shutil, glob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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


# Mapea weekday() a nombres
after_tomorrow_week_map = {
    5: 'Lunes',
    6: 'Martes',
    0: 'Miercoles',
    1: 'Jueves',
    2: 'Viernes',
    3: 'Sababado',
    4: 'Domingo'
}

# Mapea weekday() a nombres
dia_a_buscar = {
    5: 'Lun',
    6: 'Mar',
    0: 'Mié',
    1: 'Jue',
    2: 'Vie',
    3: 'Sáb',
    4: 'Dom'
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

EMAIL_CONFIG = {
    "reservada": {
        "subject": "Reserva confirmada ✅",
        "title": "Reserva confirmada",
        "color": "#28a745",
        "to": "user"
    },
    "anticipacion": {
        "subject": "No se ha respetado el plazo de anticipación 🟡",
        "title": "Demasiado pronto",
        "color": "#ffc107",
        "to": "dev"
    },
    "llena": {
        "subject": "Clase llena ❌",
        "title": "Clase llena",
        "color": "#dc3545",
        "to": "user"
    },
    "no_encontrada": {
        "subject": "Clase no encontrada ❌",
        "title": "Clase no encontrada",
        "color": "#6c757d",
        "to": "dev"
    },
    "error": {
        "subject": "Error en reserva ❌",
        "title": "Error en la reserva",
        "color": "#dc3545",
        "to": "dev"
    }
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

def aparece_hora(driver, hora):
    cards = driver.find_elements(By.XPATH, "//div[contains(@class,'MuiPaper-root')]")
    for c in cards:
        if hora in c.text:
            return True
    return False

def hacer_scroll(driver, estado):
    container = driver.execute_script("""
        return Array.from(document.querySelectorAll('div'))
        .find(el => window.getComputedStyle(el).overflowY === 'auto');
    """)

    if container is None:
        print("❌ No se encontró contenedor scrolleable")
        return

    estado["scroll"] += 1000

    driver.execute_script(
        "arguments[0].scrollTop = arguments[1];",
        container,
        estado["scroll"]
    )

    time.sleep(0.7)

def book_class_resemania(driver, reserva_deseada):
    wait = WebDriverWait(driver,15)
    encontrada=False
    try:
        if today.weekday() == 6:
                try:
                    boton = driver.find_element(By.XPATH, '//button[.//svg[@data-testid="KeyboardArrowRightIcon"]]')
                    boton.click()
                except NoSuchElementException:
                    print(f"{fechalog} - No se encontró botón nextWeek")
        
        #driver.get(f"https://member.resamania.com/{gym}/planning?club=%2Fenjoy%2Fclubs%2F2374")
        #MuiGrid-root MuiGrid-container
        #print("Estoy buscando "+reserva_deseada['dia_click'])
        wait.until(EC.presence_of_element_located((By.ID, "mui-component-select-activity")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[.//button[contains(.,'Inscribirse')]]")))


        tarjetas = driver.find_elements(By.XPATH, "//div[.//button[contains(.,'Inscribirse')]]")
        #boton = wait.until(    EC.element_to_be_clickable(        (By.XPATH, f"//button[.//span[contains(., '{reserva_deseada['dia_click']}')]]")    ))
        boton = wait.until(    EC.element_to_be_clickable((By.XPATH, f"//button[@value='{reserva_deseada['fecha_pasado_mañana']}']")))    
        boton.click()
        time.sleep(3)
        cards = driver.find_elements(By.XPATH, "//div[contains(@class,'MuiPaper-root')]")

        driver.save_screenshot("/tmp/resamania_book1.png")
 

        #card = WebDriverWait(driver, 5).until(        EC.presence_of_element_located((By.XPATH, xpath_card))        )
        estado = {"scroll": 0}
        for i in range(10):
            if aparece_hora(driver, reserva_deseada['hora']):
                break
            hacer_scroll(driver,estado)
        #hacer un scroll mas para asegurarme y verlo en la captura
        hacer_scroll(driver,estado)

        #vuelvo a leer las cards
        cards = driver.find_elements(By.XPATH, "//div[contains(@class,'MuiPaper-root')]")
        #print("=============================")
        for card in cards:
            texto = card.text.replace("\n", " ").replace("\xa0", " ")
            #print(texto)

            if reserva_deseada['hora'] in texto and reserva_deseada['clase'] in texto:
                encontrada=True
                print("\t🎯 Card encontrada")
                #print(card.get_attribute("outerHTML"))
                #boton = card.find_element(By.XPATH, ".//button[contains(., 'Inscribirse')]")
                boton = card.find_element(By.XPATH, ".//button[starts-with(normalize-space(.), 'Inscribirse')]")
                driver.execute_script("arguments[0].click();", boton)
                #boton.click()
                break
        #print("=============================")
        time.sleep(4)
        driver.save_screenshot(f"/tmp/resamania_reserva_resultado.png")
 
        #Operación en curso
        #has superado el numero de reservas autorizado
        #Se ha realizado la reserva
        #Se ha anulado la reserva

        # Esperar a que aparezca el snackbar
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(
                By.CSS_SELECTOR,
                ".MuiSnackbarContent-message"
            ).text.strip()
        )

        # Esperar a que cambie del mensaje temporal
        mensaje_final = WebDriverWait(driver, 20).until(
            lambda d: (
                (texto := d.find_element(
                    By.CSS_SELECTOR,
                    ".MuiSnackbarContent-message"
                ).text.strip())
                and texto != "Operación en curso"
                and texto
            )
        )
        print("\tResultado final:", mensaje_final)
        if encontrada:
            if "realizado la reserva" in mensaje_final.lower():
                return {
                        "status": "reservada",
                        "clase": reserva_deseada['clase'],
                        "hora": reserva_deseada['hora'],
                    }
            elif "anticipación" in mensaje_final.lower():
                return {
                    "status":"anticipacion"
                }
            else:
                return {
                    "status": "error",
                    "mensaje": mensaje_final
                }
        else:
            return {
                        "status": "no_encontrada",
                    }


    except Exception as e:
        print("❌ ERROR COMPLETO:")
        import traceback
        traceback.print_exc()
        return None
    
def cancel_class_resemania(driver, cancelacion_deseada):
    wait = WebDriverWait(driver,15)
    encontrada=False
    try:
        if today.weekday() == 6:
                try:
                    boton = driver.find_element(By.XPATH, '//button[.//svg[@data-testid="KeyboardArrowRightIcon"]]')
                    boton.click()
                except NoSuchElementException:
                    print(f"{fechalog} - No se encontró botón nextWeek")
        
        #driver.get(f"https://member.resamania.com/{gym}/planning?club=%2Fenjoy%2Fclubs%2F2374")
        #MuiGrid-root MuiGrid-container
        #print("Estoy buscando "+reserva_deseada['dia_click'])
        wait.until(EC.presence_of_element_located((By.ID, "mui-component-select-activity")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[.//button[contains(.,'Inscribirse')]]")))

        fecha_evento = cancelacion_deseada['fecha_evento'].strftime("%Y-%m-%d")
        tarjetas = driver.find_elements(By.XPATH, "//div[.//button[contains(.,'Desinscribirse')]]")
        #boton = wait.until(    EC.element_to_be_clickable(        (By.XPATH, f"//button[.//span[contains(., '{reserva_deseada['dia_click']}')]]")    ))
        boton = wait.until(    EC.element_to_be_clickable((By.XPATH, f"//button[@value='{fecha_evento}']")))    
        boton.click()
        time.sleep(3)
        cards = driver.find_elements(By.XPATH, "//div[contains(@class,'MuiPaper-root')]")

        driver.save_screenshot("/tmp/resamania_book1.png")
 

        #card = WebDriverWait(driver, 5).until(        EC.presence_of_element_located((By.XPATH, xpath_card))        )
        estado = {"scroll": 0}
        for i in range(10):
            if aparece_hora(driver, cancelacion_deseada['hora']):
                break
            hacer_scroll(driver,estado)
        #hacer un scroll mas para asegurarme y verlo en la captura
        hacer_scroll(driver,estado)

        #vuelvo a leer las cards
        cards = driver.find_elements(By.XPATH, "//div[contains(@class,'MuiPaper-root')]")
        #print("=============================")
        for card in cards:
            texto = card.text.replace("\n", " ").replace("\xa0", " ")
            #print(texto)

            if cancelacion_deseada['hora'] in texto and cancelacion_deseada['clase'] in texto:
                encontrada=True
                print("\t🎯 Card encontrada")
                #print(card.get_attribute("outerHTML"))
                #boton = card.find_element(By.XPATH, ".//button[contains(., 'Inscribirse')]")
                boton = card.find_element(By.XPATH, ".//button[starts-with(normalize-space(.), 'Desinscribirse')]")
                driver.execute_script("arguments[0].click();", boton)
                #boton.click()
                break
        #print("=============================")
        time.sleep(4)
        driver.save_screenshot(f"/tmp/resamania_reserva_resultado.png")
 
        #Operación en curso
        #has superado el numero de reservas autorizado
        #Se ha realizado la reserva
        #Se ha anulado la reserva

        # Esperar a que aparezca el snackbar
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(
                By.CSS_SELECTOR,
                ".MuiSnackbarContent-message"
            ).text.strip()
        )

        # Esperar a que cambie del mensaje temporal
        mensaje_final = WebDriverWait(driver, 20).until(
            lambda d: (
                (texto := d.find_element(
                    By.CSS_SELECTOR,
                    ".MuiSnackbarContent-message"
                ).text.strip())
                and texto != "Operación en curso"
                and texto
            )
        )
        print("\tResultado final:", mensaje_final)
        if encontrada:
            if "anulado la reserva" in mensaje_final.lower():
                return {
                        "status": "cancelada",
                        "clase": cancelacion_deseada['clase'],
                        "hora": cancelacion_deseada['hora'],
                    }
            
            else:
                return {
                    "status": "error",
                    "mensaje": mensaje_final
                }
        else:
            return {
                        "status": "no_encontrada",
                    }


    except Exception as e:
        print("❌ ERROR COMPLETO:")
        import traceback
        traceback.print_exc()
        return None
   
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

def build_email_html(title, message, status_color):
   return f"""
    <html>
      <body style="margin:0; padding:0; background-color:#f4f6f8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
        
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td align="center" style="padding:20px 10px;">
              
              <!-- Card -->
              <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
                
                <!-- Header -->
                <tr>
                  <td style="background:{status_color}; padding:20px; text-align:center; color:white;">
                    <h2 style="margin:0; font-weight:600;">{title}</h2>
                  </td>
                </tr>

                <!-- Icon -->
                <tr>
                  <td align="center" style="padding:25px 20px 10px;">
                    <div style="font-size:40px;">
                      🎯
                    </div>
                  </td>
                </tr>

                <!-- Message -->
                <tr>
                  <td style="padding:10px 30px 20px; text-align:center; color:#333;">
                    <p style="font-size:16px; line-height:1.6; margin:0;">
                      {message}
                    </p>
                  </td>
                </tr>

                <!-- Button -->
                <tr>
                  <td align="center" style="padding:10px 20px 30px;">
                    <a href="#" style="background:{status_color}; color:white; text-decoration:none; padding:14px 24px; border-radius:8px; font-size:15px; font-weight:600; display:inline-block;">
                      Ver mis reservas
                    </a>
                  </td>
                </tr>

                <!-- Divider -->
                <tr>
                  <td style="padding:0 30px;">
                    <hr style="border:none; border-top:1px solid #eee;">
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="padding:15px 20px; text-align:center; font-size:12px; color:#888;">
                    Aimharder Booking System<br>
                    <span style="color:#bbb;">Mensaje automático · No responder</span>
                  </td>
                </tr>

              </table>

            </td>
          </tr>
        </table>

      </body>
    </html>
    """

def gestionar_resultado_email(res, email_to, email_to_dev):
    status = res["status"]

    if status not in EMAIL_CONFIG:
        return

    config = EMAIL_CONFIG[status]

    clase = res.get("clase", "N/A")
    hora = res.get("hora", "N/A")   
    match status:
        case "reservada":
            message = f"La clase de {clase} a las {hora} se ha reservado con exito. A darle duro."
        case "espera":
            message = f"La clase de {clase} a las {hora} esta llena, pero se te ha apuntado en lista de espera"
        case "llena":
            message = f"La clase de {clase}a las {hora} esta llena y el cupo de lista de espera tambien. Lo siento."
        case "no_encontrada":
            message = f"La clase de {clase} a las {hora} no se ha encontrado entre las clases disponibles para ese dia"
        case "error":
            message = f"Ha habido un error en el intento de reserva de la clase de {clase} a las {hora}. El desarrollador estará trabajando en ello para solventarlo."
        case _:
            message = res.get("msg", "Estado desconocido")
    

    body = build_email_html(config["title"], message, config["color"])

    to = email_to if config["to"] == "user" else email_to_dev

    send_email(config["subject"], body,message, to)

def send_email(subject, body,message, to_email):
    msg = MIMEMultipart("alternative")

    msg["Subject"] = subject
    msg["From"] = email_account
    msg["To"] = to_email

    # Versión texto plano (fallback)
    text_version = f"{subject}\n\n{message}\n\n---\nAimharder Booking System"

    msg.attach(MIMEText(text_version, "plain", "utf-8"))
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        server = smtplib.SMTP_SSL(email_smtp_server, int(email_smtp_port))
        server.login(email_account, email_password)
        server.send_message(msg)
        server.quit()
        print(f"\t{fechalog} - Correo enviado")
    except Exception as e:
        print(f"\t{fechalog} - No se pudo enviar el correo: {str(e)}")

if __name__ == "__main__":
    # Example usage - replace these with your actual credentials
    try:
        with conn:
            with conn.cursor() as cur:

                try:
                            
                    cur.execute("UPDATE bookings  SET reserva_realizada = 0, fecha_evento = fecha_evento + INTERVAL 7 DAY WHERE reserva_realizada = 1  AND fecha_evento < NOW()")
                    conn.commit()
                    #cur.execute("update bookings set reserva_realizada=1 where id=%s", (item['id'],))  #lo marco como reserva realizada y si la hora es superior lo reseteo a 0.
                except:
                    pass

                # Obtener configuraciones de todos los usuarios que tengan una
                cur.execute("SELECT * from usuarios u LEFT JOIN configs c ON u.id=c.user_id")
                usuarios = cur.fetchall()
                for usuario in usuarios:
                    alguna_reserva=False
                    user_id = usuario['id']
                    aimharder_user = usuario['aimharder_user']
                    aimharder_pass = usuario['aimharder_pass']
                    periodicidad = usuario['periodicidad']
                    email_to = usuario['email']
                    tipo_app = usuario['tipo_app']
                    gym = usuario['gym']
                    cur.execute("SELECT * from bookings where user_id=%s", (user_id,))
                    reservas = cur.fetchall()

                    if tipo_app == 'resamania':
                        print(f"{fechalog} - USUARIO: {aimharder_user}")
                        driver = None  # 👈 importante

                        try:
                            for item in reservas:
                                # Filtros base (ANTES de cualquier cálculo)
                                if not item['activo']:
                                    continue
                                if not item['hora']:
                                    continue                         
                                # 1. Inicializar fecha_evento si hace falta
                            #if not item['fecha_evento']:
                                # calcular como ya haces ahora
                                texto = item['dia'] + " " + item['hora']
                                dia_str, horas = texto.split(" ", 1)
                                hora_inicio = horas.strip()
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

                                # 🔥 guardarlo en BD
                                cur.execute("""
                                    UPDATE bookings 
                                    SET fecha_evento = %s 
                                    WHERE id = %s
                                """, (fecha_evento, item['id']))

                                item['fecha_evento'] = fecha_evento
                                
                                # 2. Filtros
                                if not item['activo'] and item['reserva_Realizada'] and fecha_evento > ahora :
                                    try:
                                        print("Cancelando clase")
                                        result = login_to_resamania(aimharder_user, aimharder_pass,gym)
                                        driver, tmpdir = result
                                        resultado = cancel_class_resemania(driver, item)
                                        cur.execute("update bookings set reserva_realizada=0 where id=%s", (item['id'],))
                                        conn.commit()
                                        continue
                                    except:
                                        print("Error intentando cancelar clase")
                                    
                                #if not item['activo'] or item['reserva_realizada']:
                                #    continue

                                # 3. Usar fecha_evento REAL (BD)
                                if not item['fecha_evento']:  #Por robustez
                                    continue
                                fecha_evento = item['fecha_evento']
                                diferencia = fecha_evento - ahora

                                #print(f"\t {ahora} vs {fecha_evento} => {diferencia}")
                                alguna_reserva=True

                                if diferencia.total_seconds() > 48 * 3600:
                                    print(f"\t - ❌  NO tiene reservas en las proximas 48h. {item['clase']} el {item['dia']} a las {item['hora']}")
                                    continue
                                
                                ## 🔥 4. LOGIN SOLO UNA VEZ
                                if driver is None:
                                    result = login_to_resamania(aimharder_user, aimharder_pass,gym)
                                    driver, tmpdir = result
                                    if not driver:
                                        print("\t Error en login")
                                        break  # no tiene sentido seguir

                                # 5. Reservar
                                item['clase']=item['clase']
                                item['hora']=normalize(item['hora'])
                                pasao = today + timedelta(days=2)
                                fechapasao =  pasao.strftime("%Y-%m-%d")
                                item['fecha_pasado_mañana']=fechapasao


                                print(f"\t - ✅ {user_id} - TIENE una clase en menos de 48h. {item['clase']} el {item['dia']} a las {item['hora']} ")

                                try:
                                    resultado = book_class_resemania(driver, item)
                                    print("\t Resultado:", resultado)
                                    gestionar_resultado_email(resultado, email_to, email_to_dev)

                                    if resultado.get("status")=="reservada":
                                        cur.execute("update bookings set reserva_realizada=1 where id=%s", (item['id'],))  #lo marco como reserva realizada y si la hora es superior lo reseteo a 0.
                                except Exception as e:
                                        print("\t Error reservando:", e)
                            conn.commit()
                        finally:
                            # 🔥 5. Cerrar driver UNA VEZ
                            if driver:
                                driver.quit()
                        if not alguna_reserva:
                                print(f"\t - 🤷‍♂️🤷 {user_id} - {aimharder_user} No tiene clases a reservar")

    except Exception as e:
        print(f"{fechalog} - Error GLOBAL: {str(e)}")

        try:
            send_email(
                subject="Error GLOBAL ❌",
                body=str(e),
                to_email=email_to_dev
            )
        except Exception:
            print("Error enviando email de fallo global")