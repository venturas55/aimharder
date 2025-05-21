from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess

# Configurar el driver de Selenium

# Set up Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")  # New headless mode for Chrome
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("--remote-debugging-address=0.0.0.0")
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


def get_current_clases():
    # Abrir la página web
    driver.get("https://hybridboxgrau.aimharder.com/schedule")

    # Esperar a que la página cargue completamente y los bloques estén disponibles
    WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bloqueClase")))

    # Crear un set para almacenar las clases únicas
    clases_unicas = set()

    # Encontrar todos los bloques de la semana en curso
    class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")

    # Recorrer los bloques y extraer las clases rvNombreCl
    for block in class_blocks:
        try:
            class_name = block.find_element(By.CLASS_NAME, "rvNombreCl").text.strip()
            clases_unicas.add(class_name)  # Añadir al set, asegurando que sean únicos
        except Exception as e:
            print(f"Error al procesar un bloque: {e}")
    # Cerrar el driver después de la tarea
    driver.quit()
    return clases_unicas