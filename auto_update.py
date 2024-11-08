import os
import sys
import time
import requests
import subprocess
from PyQt5 import QtWidgets, QtCore
from version import version

GITHUB_API_URL = "https://api.github.com/repos/eahumadaed/SOLIAPPV3/releases/latest"
LOCAL_VERSION = version

def get_latest_version():
    response = requests.get(GITHUB_API_URL)
    if response.status_code == 200:
        data = response.json()
        return data["tag_name"], data["assets"][0]["browser_download_url"]
    return None, None

class DownloadThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished_download = QtCore.pyqtSignal(bool)

    def __init__(self, download_url, temp_path):
        super().__init__()
        self.download_url = download_url
        self.temp_path = temp_path

    def run(self):
        response = requests.get(self.download_url, stream=True)
        total_length = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(self.temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress_percent = int((downloaded / total_length) * 100)
                    self.progress.emit(progress_percent)

        self.finished_download.emit(True)

class DownloadWindow(QtWidgets.QWidget):
    def __init__(self, download_url, temp_path):
        super().__init__()
        self.download_url = download_url
        self.temp_path = temp_path
        self.initUI()
        self.start_download()

    def initUI(self):
        self.setWindowTitle("Actualización")
        self.setGeometry(500, 300, 400, 150)
        
        self.label = QtWidgets.QLabel("Descargando nueva versión...", self)
        self.label.setGeometry(20, 20, 360, 20)
        
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(20, 60, 360, 30)
        self.progress_bar.setValue(0)
        
        self.show()

    def start_download(self):
        self.thread = DownloadThread(self.download_url, self.temp_path)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished_download.connect(self.on_download_complete)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_download_complete(self):
        self.replace_file()

    def replace_file(self):
        try:
            # Ruta del archivo destino
            current_path = "Formulario SOL + DPs.exe"

            # Verifica si el archivo actual existe
            if os.path.exists(current_path):
                print(f"Reemplazando archivo existente: {current_path}")
                os.remove(current_path)  # Elimina el archivo original
            else:
                print(f"Creando nuevo archivo: {current_path}")

            # Renombra el archivo temporal al archivo destino
            os.rename(self.temp_path, current_path)

            # Mostrar mensaje de éxito
            print("Archivo reemplazado correctamente.")

            # Cerrar la aplicación después de realizar la operación
            
            QtWidgets.QMessageBox.information(self, "Actualización", "Descarga completa!\nVuelva a abrir la aplicación")
            self.close()

        except Exception as e:
            # Manejo de errores en caso de fallo
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al reemplazar el archivo: {e}")
            self.close()  # También cerramos la ventana en caso de error




def main_update():
    latest_version, download_url = get_latest_version()
    if latest_version and latest_version != LOCAL_VERSION:
        temp_path = sys.argv[0] + ".tmp"  # Archivo temporal para la nueva versión
        app = QtWidgets.QApplication(sys.argv)
        download_window = DownloadWindow(download_url, temp_path)
        app.exec_()
        return False  # Indica que se está ejecutando la actualización
    return True  # No hay actualizaciones, continúa el programa normalmente
