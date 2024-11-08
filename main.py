from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QDialog, QProgressBar
import sys
import requests
from windows.next_window import NextWindow  # Asegúrate de tener esta clase si la vas a usar
from data.comunas import *  # Asegúrate de que los módulos necesarios estén presentes
from auto_update import main_update  # Asumo que esto es una función para comprobar actualizaciones

class LoadingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Cargando...')
        self.setGeometry(100, 100, 300, 100)
        layout = QVBoxLayout()
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        self.label = QLabel("Cargando usuarios...", self)
        layout.addWidget(self.label)
        self.setLayout(layout)

class UserSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Seleccionar Usuario')
        self.setGeometry(100, 100, 300, 50)
        self.center_window()
        self.layout = QVBoxLayout()
        self.label = QLabel("Seleccione un usuario:", self)
        self.layout.addWidget(self.label)
        self.user_select = QComboBox(self)       
        self.layout.addWidget(self.user_select)
        self.continue_button = QPushButton("Continuar", self)
        self.continue_button.clicked.connect(self.load_next_interface)
        self.layout.addWidget(self.continue_button)
        self.setLayout(self.layout)

        self.loading_dialog = None  # La ventana de carga se inicializa aquí

    def load_users(self):
        # Mostrar la ventana de carga
        self.loading_dialog = LoadingDialog()
        self.loading_dialog.show()

        # Forzar la actualización de la interfaz para que la ventana de carga se muestre
        QApplication.processEvents()

        # Crear un hilo para hacer la solicitud a la API
        self.thread = LoadUsersThread()
        self.thread.users_loaded.connect(self.on_users_loaded)
        self.thread.start()  # Inicia el hilo

    def on_users_loaded(self, users):
        # Ocultar el diálogo de carga
        self.loading_dialog.accept()

        # Llenar el combo box con los usuarios
        for user in users:
            user_info = f"{user['name']} ({int(user['asignados'])+int(user['Pendiente'])} Asignados| {user['terminados']} Terminados)"
            self.user_select.addItem(user_info, {
                'id': user['id'],
                'name': user['name'],
                'terminados': user['terminados']
            })

    def center_window(self):
        window_size = self.sizeHint()
        screen = self.screen().geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.setGeometry(x, y, 300, 50)

    def load_next_interface(self):
        # Aquí puedes manejar el cambio a la siguiente ventana, por ejemplo:
        selected_user = self.user_select.currentData()  # Obtener datos del usuario seleccionado
        if selected_user:
            next_window = NextWindow(selected_user)  # Asumiendo que NextWindow es otra ventana
            next_window.show()
            self.close()  # Cierra la ventana actual

class LoadUsersThread(QThread):
    # Señal que se emite cuando los usuarios han sido cargados
    users_loaded = pyqtSignal(list)

    def run(self):
        # Hacer la solicitud HTTP para cargar los usuarios
        try:
            response = requests.get('https://api.loverman.net/dbase/dga2024/apiv3/api.php?action=getUsers')
            if response.status_code == 200:
                users = response.json()
                self.users_loaded.emit(users)  # Emitir la señal con los usuarios
            else:
                self.users_loaded.emit([])  # Emitir lista vacía si hay error
        except requests.RequestException as e:
            print(f"Error al obtener los usuarios: {e}")
            self.users_loaded.emit([])  # Emitir lista vacía si ocurre un error

if __name__ == '__main__':
    if main_update():  # Verifica si hay actualizaciones antes de continuar
        app = QApplication(sys.argv)
        main_window = UserSelectionWindow()
        main_window.load_users()  # Llamar a la función que carga los usuarios
        main_window.show()
        sys.exit(app.exec_())
