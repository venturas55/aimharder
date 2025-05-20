from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import date
import sys
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import winreg

load_dotenv()

# Accede a las variables del .env
email_account = os.getenv("EMAIL_ACCOUNT")
email_password = os.getenv("EMAIL_PASSWORD")
email_to = os.getenv("EMAIL_TO")
email_to_dev = os.getenv("EMAIL_TO_DEV")
email_smtp_server = os.getenv("EMAIL_SMTP_SERVER")
email_smtp_port = os.getenv("EMAIL_SMTP_PORT")
user_name = os.getenv("AIMHARDER_USERNAME")
passw = os.getenv("AIMHARDER_PASSWORD")

# Default class time
desired_class_time = '8:00 - 9:00'  # Default time

def login_to_aimharder(username, password):
    try:
        # Set up Chrome options for Windows
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # New headless mode for Chrome
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        
        # Initialize Chrome driver with explicit error handling
        try:
            # Try to use ChromeDriverManager first
            print("Attempting to initialize Chrome driver...")
            
            # Use ChromeDriverManager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("Successfully initialized Chrome driver")
                return driver
            except Exception as e:
                print(f"Error with ChromeDriverManager: {str(e)}")
                print("Falling back to direct Chrome initialization...")
                
                # Try direct initialization
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                    print("Successfully initialized Chrome driver")
                except Exception as e:
                    print(f"Error with direct initialization: {str(e)}")
                    raise
                    
        except Exception as e:
            print(f"Error initializing Chrome driver: {str(e)}")
            raise

        # Add explicit wait
        wait = WebDriverWait(driver, 10)
        
        # Navigate to aimharder.com
        driver.get("https://www.aimharder.com/login")
        
        # Wait for the login form to load
        try:
            wait.until(EC.presence_of_element_located((By.ID, "mail")))
            print("Login form found")
        except Exception as e:
            print(f"Could not find login form: {str(e)}")
            driver.quit()
            return None
            
        # Enter username and password
        try:
            # Click cookie remove button
            try:
                cookie_remove_button = driver.find_element(By.CLASS_NAME, "removeCookie")
                cookie_remove_button.click()
                print("Cookie removal button clicked")
                time.sleep(2)
            except Exception as e:
                print(f"Could not find or click cookie removal button: {str(e)}")
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
            print("Login successful")
            
            # Click reservations
            reservations_link = driver.find_element(By.CLASS_NAME, "ahPicReservations")
            reservations_link.click()
            print("Clicked reservations link")
            
            # Wait for the class list to load
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bloqueClase")))

            hoy = date.today()
            clase =  'wds'+hoy.strftime("%Y/%m/%d")
            print(clase)

            
            # Find the HYROX-Endurance class
            try:
                # Find all class blocks
                class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")
                
                # Look for the HYROX-Endurance class at the selected time
                for block in class_blocks:
                    # Check if this block contains the HYROX-Endurance class name
                    class_name = block.find_element(By.CLASS_NAME, "rvNombreCl").text
                    class_horario = block.find_element(By.CLASS_NAME, "rvHora").text
                    
                    if "HYROX-Endurance" in class_name and class_horario == desired_class_time:
                        instructor_name = block.find_element(By.CLASS_NAME, "rvCoach").text
                        box_name = block.find_element(By.CLASS_NAME, "rvBox").text  
                        # Find and click the reservation link within this block
                        reserve_link = block.find_element(By.XPATH, ".//a[contains(text(), 'Reservar')]")
                        print(f"La clase HYROX-Endurance en {box_name} con el {instructor_name} fue reservada correctamente para {hoy} a las {class_horario}.")
                        break
                else:
                    print("Could not find HYROX-Endurance class in the list")
                    
            except Exception as e:
                print(f"Error finding button or clicking RESERVAR: {str(e)}")
                
        except Exception as e:
            print(f"Error during login process: {str(e)}")
            driver.quit()
            return None
            
        return driver
            
        # Add explicit wait
        wait = WebDriverWait(driver, 10)
            
        # Navigate to aimharder.com
        driver.get("https://www.aimharder.com/login")
            
        # Wait for the login form to load
        try:
            wait.until(EC.presence_of_element_located((By.ID, "mail")))
            print("Login form found")
        except Exception as e:
            print(f"Could not find login form: {str(e)}")
            driver.quit()
            return
                
            # Enter username and password
            try:
                # Click cookie remove button
                try:
                    cookie_remove_button = driver.find_element(By.CLASS_NAME, "removeCookie")
                    cookie_remove_button.click()
                    print("Cookie removal button clicked")
                    time.sleep(2)
                except Exception as e:
                    print(f"Could not find or click cookie removal button: {str(e)}")
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
                print("Login successful")
                
                # Click reservations
                reservations_link = driver.find_element(By.CLASS_NAME, "ahPicReservations")
                reservations_link.click()
                print("Clicked reservations link")
                
                # Wait for the class list to load
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bloqueClase")))

                hoy = date.today()
                clase =  'wds'+hoy.strftime("%Y/%m/%d")
                print(clase)

                
                # Find the HYROX-Endurance class
                try:
                    # Find all class blocks
                    class_blocks = driver.find_elements(By.CLASS_NAME, "bloqueClase")
                    
                    # Look for the HYROX-Endurance class at the selected time
                    for block in class_blocks:
                        # Check if this block contains the HYROX-Endurance class name
                        class_name = block.find_element(By.CLASS_NAME, "rvNombreCl").text
                        class_horario = block.find_element(By.CLASS_NAME, "rvHora").text
                       
                        if "HYROX-Endurance" in class_name and class_horario == desired_class_time:
                            instructor_name = block.find_element(By.CLASS_NAME, "rvCoach").text
                            box_name = block.find_element(By.CLASS_NAME, "rvBox").text  
                            # Find and click the reservation link within this block
                            reserve_link = block.find_element(By.XPATH, ".//a[contains(text(), 'Reservar')]")
                            #reserve_link.click()
                            print(f"La clase HYROX-Endurance en {box_name} con el {instructor_name} fue reservada correctamente para {hoy} a las {class_horario}.")
                            break
                    else:
                        print("Could not find HYROX-Endurance class in the list")
                        
                except Exception as e:
                    print(f"Error finding button or clicking RESERVAR: {str(e)}")
                    
            except Exception as e:
                print(f"Error during login process: {str(e)}")
                driver.quit()
                return
                
        except Exception as e:
            print(f"Error initializing Chrome driver: {str(e)}")
            raise
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'driver' in locals():
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
        print("Correo enviado")
    except Exception as e:
        print(f"No se pudo enviar el correo: {str(e)}")


if __name__ == "__main__":
    # Example usage - replace these with your actual credentials
    try:
        login_to_aimharder(user_name, passw)

    except Exception as e:
        print(f"Error al hacer reserva: {str(e)}")
        #send_email(
        #    subject="Error al hacer reserva ❌",
        #    body=f"Ocurrió un error al reservar:\n{str(e)}",
        #    to_email=email_to_dev
        #)
