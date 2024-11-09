from PyQt5.QtWidgets import QVBoxLayout, QFrame, QListWidget, QPushButton, QLabel, QGridLayout, QComboBox, QLineEdit, QDialog, QListWidgetItem
import requests
import re


class UsuarioModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Usuarios")
        self.setGeometry(200, 200, 700, 700)
        self.layout = QVBoxLayout()
        
        self.loaded_ruts_with_error = []

        self.usuario_list = QListWidget(self)
        self.layout.addWidget(self.usuario_list)

        self.add_button = QPushButton("Agregar", self)
        self.add_button.clicked.connect(self.add_usuario)
        self.layout.addWidget(self.add_button)

        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_usuarios)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

        self.load_usuarios()

    def add_usuario(self, data=None):
        container = QFrame(self)
        layout = QGridLayout(container)

        # Campo oculto para ID
        id_hidden = QLineEdit()
        id_hidden.setVisible(False)
        if data and 'id' in data:
            id_hidden.setText(str(data['id']))
        layout.addWidget(id_hidden, 0, 0)

        rut_label = QLabel("RUT")
        layout.addWidget(rut_label, 0, 0)
        rut = QLineEdit()
        rut.textChanged.connect(lambda: self.parent().to_uppercase(rut))
        rut.focusOutEvent = lambda event: self.parent().on_rut_focus_out(rut, event)
        if data:
            verified_rut = self.parent().verificar_rut(rut=data['rut'], show_messages=False)
            rut.setText(verified_rut['rut'])
            if "errorWasFounded" in verified_rut and verified_rut["errorWasFounded"]:
                self.loaded_ruts_with_error.append(verified_rut['rut'])
            
        layout.addWidget(rut, 0, 1)

        buscar_button = QPushButton("Buscar", self)
        buscar_button.clicked.connect(lambda: self.buscar_rut(rut, container))
        layout.addWidget(buscar_button, 0, 2)

        nac_label = QLabel("Nacionalidad:")
        layout.addWidget(nac_label, 1, 0)
        nac = QComboBox()
        nac.wheelEvent = lambda event: event.ignore()
        nac.addItems(['--', 'CHILENA', 'EXTRANJERA'])
        
        if data:
            nac.setCurrentText(data['nac'])
        layout.addWidget(nac, 1, 1)

        tipo_label = QLabel("Tipo:")
        layout.addWidget(tipo_label, 1, 2)
        tipo = QComboBox()
        tipo.wheelEvent = lambda event: event.ignore()
        tipo.addItems(['--', 'NATURAL', 'JURIDICA'])
        if data:
            tipo.setCurrentText(data['tipo'])
        layout.addWidget(tipo, 1, 3)

        genero_label = QLabel("Género:")
        layout.addWidget(genero_label, 2, 0)
        genero = QComboBox()
        genero.wheelEvent = lambda event: event.ignore()
        genero.addItems(['--', 'F', 'M'])
        if data:
            genero.setCurrentText(data['genero'])
        layout.addWidget(genero, 2, 1)

        nombre_label = QLabel("Nombre:")
        layout.addWidget(nombre_label, 2, 2)
        nombre = QLineEdit()
        nombre.textChanged.connect(lambda: self.parent().to_uppercase(nombre))
        if data:
            nombre.setText(data['nombre'])
        layout.addWidget(nombre, 2, 3)

        paterno_label = QLabel("Apellido Paterno:")
        layout.addWidget(paterno_label, 3, 0)
        paterno = QLineEdit()
        paterno.textChanged.connect(lambda: self.parent().to_uppercase(paterno))
        if data:
            paterno.setText(data['paterno'])
        layout.addWidget(paterno, 3, 1)

        materno_label = QLabel("Apellido Materno:")
        layout.addWidget(materno_label, 3, 2)
        materno = QLineEdit()
        materno.textChanged.connect(lambda: self.parent().to_uppercase(materno))
        if data:
            materno.setText(data['materno'])
        layout.addWidget(materno, 3, 3)

        delete_button = QPushButton("Borrar", self)
        delete_button.clicked.connect(lambda: self.delete_usuario(container, data.get('id') if data else None))
        layout.addWidget(delete_button, 4, 0, 1, 4)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.usuario_list.addItem(list_item)
        self.usuario_list.setItemWidget(list_item, container)

    def delete_usuario(self, container, usuario_id=None):
        if usuario_id:
            try:
                response = requests.post(f'{self.parent().api_base_url}deleteUsuario', json={'id': usuario_id})
                response.raise_for_status()
                result = response.json()

                if result.get('message') == 'Usuario eliminado correctamente':
                    self.remove_usuario_from_list(container)
                    self.parent().show_message("Info", "Eliminar", "Usuario eliminado correctamente.")
                else:
                    self.parent().show_message("Error", "Eliminar", result.get('message', 'Error desconocido'))

            except requests.RequestException as e:
                self.parent().show_message("Error", "Eliminar", str(e))
        else:
            self.remove_usuario_from_list(container)
            
            
    def remove_usuario_from_list(self, container):
        for i in range(self.usuario_list.count()):
            item = self.usuario_list.item(i)
            if self.usuario_list.itemWidget(item) == container:
                self.usuario_list.takeItem(i)
                break

    def save_usuarios(self,silence=False):
        if not self.parent().current_formulario_id:
            self.parent().show_message("Error", "Guardar", "Seleccione un trabajo antes de guardar usuarios.")
            return

        usuarios_data = []
        for i in range(self.usuario_list.count()):
            container = self.usuario_list.itemWidget(self.usuario_list.item(i))
            data = {
                'id': container.layout().itemAt(0).widget().text() or None,  # ID oculto
                'rut': container.layout().itemAt(2).widget().text(),
                'nac': container.layout().itemAt(5).widget().currentText(),
                'tipo': container.layout().itemAt(7).widget().currentText(),
                'genero': container.layout().itemAt(9).widget().currentText(),
                'nombre': container.layout().itemAt(11).widget().text(),
                'paterno': container.layout().itemAt(13).widget().text(),
                'materno': container.layout().itemAt(15).widget().text(),
            }
            usuarios_data.append(data)

        try:
            response = requests.post(f'{self.parent().api_base_url}saveUsuarios', json={
                'trabajo_id': self.parent().current_trabajo_id,
                'formulario_id': self.parent().current_formulario_id,
                'usuarios': usuarios_data
            })
            response.raise_for_status()
            if not silence:
                self.accept()
                self.deleteLater()
                self.parent().show_message("Info", "Guardar", "Usuarios guardados exitosamente.")
                print("Usuarios guardados:", usuarios_data)
        except requests.RequestException as e:
            if not silence:
                self.parent().show_message("Error", "Error al guardar usuarios", str(e))
                print(f"Error al guardar usuarios: {e}")


    def load_usuarios(self):
        if not self.parent().current_formulario_id:
            return

        try:
            response = requests.get(f'{self.parent().api_base_url}getUsuarios&formulario_id={self.parent().current_formulario_id}')
            response.raise_for_status()
            usuarios_data = response.json()
            if isinstance(usuarios_data, list):
                for usuario in usuarios_data:
                    self.add_usuario(usuario)
        except requests.RequestException as e:
            print(f"Error al cargar usuarios: {e}")
            self.parent().show_message("Error", "Error al cargar usuarios", str(e))
    
    
    def buscar_rut(self, rut_entry, container):
        rut = rut_entry.text().split("-")[0]
        success, data = self.parent().buscar_rut_api(rut)

        if success:
            print(f"Data Rut: {data}")
            if '-' not in rut_entry.text():
                container.layout().itemAt(2).widget().setText(rut + "-" + self.parent().calculate_dv(rut))
            container.layout().itemAt(11).widget().setText(data['Nombre'])
            container.layout().itemAt(13).widget().setText(data['Apa'])
            container.layout().itemAt(15).widget().setText(data['Ama'])
            container.layout().itemAt(9).widget().setCurrentText(data['G'])
            container.layout().itemAt(7).widget().setCurrentText(data['P'])
            container.layout().itemAt(5).widget().setCurrentText(data['NAC'])
        else:
            self.parent().show_message("Error", "Error al buscar RUT", "No se encontraron datos para el RUT ingresado.")


                
    def closeEvent(self, event):
        self.save_usuarios(True)
        super().closeEvent(event)


