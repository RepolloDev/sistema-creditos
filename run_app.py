import os
import shutil
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Determinar directorios base
if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).resolve().parent
    DATA_DIR = APP_DIR / "data"
else:
    BUNDLE_DIR = Path(__file__).resolve().parent
    APP_DIR = BUNDLE_DIR
    DATA_DIR = APP_DIR / "database"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Copiar base de datos semilla a ubicación permanente si no existe
DB_TARGET = DATA_DIR / "db.sqlite3"
DB_SOURCE = BUNDLE_DIR / "database" / "db.sqlite3"

if not DB_TARGET.exists() and DB_SOURCE.exists():
    shutil.copyfile(DB_SOURCE, DB_TARGET)

# En Windows con console=False, sys.stdout y sys.stderr son None.
# Django call_command("migrate") intenta escribir a stdout y revienta.
import io

if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# Variables de entorno
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["SQLITE_DB_PATH"] = str(DB_TARGET)
os.environ["DEBUG"] = "False"

sys.path.insert(0, str(BUNDLE_DIR / "apps"))
sys.path.insert(0, str(BUNDLE_DIR))

import django
django.setup()

from django.core.management import call_command
# Aplicar migraciones pendientes redirigiendo salida
null_out = io.StringIO()
try:
    call_command("migrate", interactive=False, verbosity=0, stdout=null_out, stderr=null_out)
except Exception:
    pass

from config.wsgi import application
from waitress.server import create_server

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def start_tray_icon(url, stop_callback):
    """Bandeja del sistema con opción Salir y Reabrir"""
    try:
        import pystray
        from PIL import Image, ImageDraw

        # Crear ícono simple
        img = Image.new("RGBA", (64, 64), color=(30, 64, 175, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle((16, 16, 48, 48), fill=(255, 255, 255, 255))

        def open_url(icon, item):
            webbrowser.open(url)

        def exit_app(icon, item):
            icon.stop()
            stop_callback()

        menu = pystray.Menu(
            pystray.MenuItem("Abrir en navegador", open_url, default=True),
            pystray.MenuItem("Salir / Apagar", exit_app)
        )

        icon = pystray.Icon("sis_creditos", img, "Sistema Crediticio", menu)
        icon.run()
    except Exception:
        # Si entorno gráfico no tiene soporte de system tray, esperar señal o cierre
        pass

def main():
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/"
    server = create_server(application, host="127.0.0.1", port=port)

    # Iniciar servidor Waitress en hilo secundario
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # Abrir navegador automáticamente
    def open_browser():
        time.sleep(1)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    def shutdown():
        os._exit(0)

    # Correr ícono de bandeja en hilo principal
    start_tray_icon(url, shutdown)

if __name__ == "__main__":
    main()
