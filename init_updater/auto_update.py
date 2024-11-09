import os
import sys
import time
import requests
import subprocess
from PyQt5 import QtWidgets, QtCore
from version import version
import shutil

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
    def __init__(self, download_url, dir_path):
        super().__init__()
        self.download_url = download_url
        self.current_path = dir_path
        self.temp_path = os.path.join(os.path.dirname(dir_path),"temporal.exe")
        self.batch_file_path = os.path.join(os.path.dirname(dir_path),"version_file_replacer (Eliminar).bat")
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
        self.create_batch_file()
        self.close_application()

    def create_batch_file(self):
        """Crea un archivo batch para reemplazar el ejecutable."""
        
        current_file = f'"{self.current_path}"'
        temp_file = f'"{self.temp_path}"'
        
        batch_text = f"""
@echo off
setlocal EnableDelayedExpansion

:: Contador de intentos
set attempts=0
set max_attempts=10
set max_time=20
set /a time_start=%time:~6,2%

:: Bucle para eliminar el archivo
:delete_file
echo Intentando eliminar version anterior...
echo.

:: Verificar si el archivo existe
if exist {current_file} (
    del {current_file}
    echo Version anterior eliminada.
    echo.
    timeout /t 1 /nobreak > NUL
) else (
    echo El archivo anterior ya no existe.
    echo.
    goto rename_file
)

:: Contar intentos y tiempo
set /a attempts+=1
set /a time_now=%time:~6,2%
set /a elapsed_time=%time_now% - %time_start%

:: Si el archivo no se eliminó y no se agotaron los intentos, intenta nuevamente
if !attempts! lss %max_attempts% (
    if !elapsed_time! lss %max_time% (
        goto delete_file
    ) else (
        echo Se ha agotado el tiempo de espera de 20 segundos.
        echo.
        goto result_script
    )
) else (
    echo No se pudo eliminar la version anterior después de %max_attempts% intentos.
    echo.
    goto result_script
)

:: Bucle para renombrar el archivo
:rename_file
echo Intentando renombrar {temp_file}...
echo.
if exist {temp_file} (
    move {temp_file} {current_file}
    echo Version nueva renombrada correctamente.
    echo.
    timeout /t 1 /nobreak > NUL
) else (
    echo El archivo temporal no existe.
    echo.
    goto rename_file
)

:: Mostrar el resultado con una ventana emergente
:result_script
if %errorlevel% equ 0 (
    color 0A
    echo Exito... El proceso se completo correctamente.
    echo.
) else (
    color 0C
    echo Error: No se pudo completar el proceso.
    echo.
)
goto exit_script

:: Eliminar el archivo batch después de que todo se haya completado correctamente
:exit_script
echo Presione ENTER para finalizar...
echo.
pause >nul
echo Eliminando el archivo batch...
del "%~f0"

exit
"""
        
        with open(self.batch_file_path, 'w') as batch_file:
            batch_file.write(batch_text)
        print(f"Archivo batch creado: {self.batch_file_path}")

    def close_application(self):
        """Cierra la aplicación principal de forma ordenada."""
        self.run_batch()
        sys.exit()  # Cierra el programa de forma segura

    def run_batch(self):
        """Ejecuta el archivo batch después de que el programa se cierra."""
        subprocess.Popen([self.batch_file_path])

def main_update():
    latest_version, download_url = get_latest_version()
    if latest_version and latest_version != LOCAL_VERSION:
        exe_path = sys.executable
        app = QtWidgets.QApplication(sys.argv)
        download_window = DownloadWindow(download_url, exe_path)
        app.exec_()  # Ejecutamos la ventana de descarga
        return False  # Indica que se está ejecutando la actualización
    return True  # No hay actualizaciones, continúa el programa normalmente
