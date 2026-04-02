# AimHarder Login Automation

This Python script uses Selenium to automate the login process for aimharder.com.

## Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver (automatically managed by webdriver-manager)

## Installation

1. Install the required packages:
```bash
pip install -r requirements.txt

pip install pymysql

sudo apt install chromium-browser chromium-driver
sudo apt install chromium


```

## Usage

1. Replace the content of .env_template file with your actual credentials/config info.
2. Run the script:
```bash
python aimharderVPS.py  # For VPS ubuntu

or

python aimharderWIN.py  # For Windows
```

3. There is also an app developed in Flask to schedule the script to run at a specific time.
It just modify aimharderVPS.py or aimharderWIN.py file to run at a specific time which should be run in     cron jobs in ubuntu VPS or Task Scheduler in Windows. Next line running:
        crontab -e

And adding next line to run it everyday at 05:01 

    1 5 * * * /usr/bin/python3 /home/ubuntu/aimharder/aimharderVPS.py >> /home/ubuntu/aimharder/log.txt 2>&1
    0 6 * * 1 /usr/bin/python3 /home/ubuntu/aimharder/scrape_clases.py >> /home/ubuntu/aimharder/log.txt 2>&1


4. Run Flask App using systemd
    sudo nano /etc/systemd/system/aimharderFlaskApp.service

aimharderFlaskApp.service
================
[Unit]
Description=Aimharder Flask App running on port 5050
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/aimharder
ExecStart=/usr/bin/gunicorn --workers 3 --bind 0.0.0.0:5050 app:app
Restart=always
Environment="FLASK_ENV=production"

[Install]
WantedBy=multi-user.target

====================

    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
    sudo systemctl restart aimharderFlaskApp
    sudo systemctl status aimharderFlaskApp

    sudo systemctl enable aimharderFlaskApp
    sudo systemctl start aimharderFlaskApp
    sudo systemctl stop aimharderFlaskApp

    journalctl -u aimharderFlaskApp -f

    -----
    se ha creado un aimharder2 para javi:

    sudo systemctl enable aimharder2
    sudo systemctl start aimharder2
    sudo systemctl stop aimharder2

5. Check Gunicorn logs
journalctl -u aimharderFlaskApp.service -b --no-pager | tail -n 50
journalctl -u aimharder2.service -b --no-pager | tail -n 50





## Note

- The script uses Chrome browser by default.
- Make sure Chrome is installed on your system.
- The script includes error handling and proper cleanup.
- You may need to adjust the XPaths if the website structure changes.

## UPGRADE 08/10/2025:
Se crea un nuevo script de scrapping de classes que existen (current_classes) que vuelva los nombres de todas las clases en una tabla de la base de datos de aimharder
Se añade al crontab. Así que se ejecutan dos crontabs.

  0 6 * * 1 /usr/bin/python3 /home/ubuntu/aimharder/scrape_clases.py >> /home/ubuntu/aimharder/log.txt 2>&1

Ahora la app de Flask, solo leerá de la base de datos dichos datos.


## para ver imagenes del VPS
cd /tmp
python3 -m http.server 8000