from PyQt5.QtWidgets import QVBoxLayout, QFrame, QListWidget, QPushButton, QLabel, QLineEdit, QGridLayout, QCheckBox, QDialog, QListWidgetItem
from PyQt5.QtGui import QIntValidator
import requests

class ResolucionModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Resoluciones")
        self.setGeometry(200, 200, 700, 500)

        self.layout = QVBoxLayout()

        self.resolucion_list = QListWidget(self)
        self.layout.addWidget(self.resolucion_list)

        self.add_button = QPushButton("Agregar", self)
        self.add_button.clicked.connect(self.add_resolucion)
        self.layout.addWidget(self.add_button)

        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_resoluciones)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)
        self.load_resoluciones()

    def add_resolucion(self, data=None):
        container = QFrame(self)
        layout = QGridLayout(container)

        id_hidden = QLineEdit()
        id_hidden.setVisible(False)
        if data and 'id' in data:
            id_hidden.setText(str(data['id']))
        layout.addWidget(id_hidden, 0, 0)

        n_resolucion_label = QLabel("Número:")
        layout.addWidget(n_resolucion_label, 1, 0)
        n_resolucion = QLineEdit(self)
        if data:
            n_resolucion.setText(data['n_resolucion'])
        layout.addWidget(n_resolucion, 1, 1)

        f_resolucion_label = QLabel("Fecha:")
        layout.addWidget(f_resolucion_label, 2, 0)
        f_resolucion = QLineEdit(self)
        f_resolucion.setPlaceholderText("dd/mm/yyyy")
        if data:
            f_resolucion.setText(data['f_resolucion'])
        else:
            f_resolucion.setText("--/--/----")
        
        f_resolucion.textChanged.connect(self.auto_format_date)
        layout.addWidget(f_resolucion, 2, 1)

        delete_button = QPushButton("Borrar", self)
        delete_button.clicked.connect(lambda: self.delete_resolucion(container, data.get('id') if data else None))
        layout.addWidget(delete_button, 4, 0, 1, 2)

        list_item = QListWidgetItem()
        list_item.setSizeHint(container.sizeHint())
        self.resolucion_list.addItem(list_item)
        self.resolucion_list.setItemWidget(list_item, container)

    def auto_format_date(self, text):
        clean_text = text.replace("/", "")
        
        if len(clean_text) > 8:
            clean_text = clean_text[:8]
        formatted_text = ""
        cursor_position = self.sender().cursorPosition()
        
        if len(clean_text) >= 2:
            formatted_text += clean_text[:2] + "/"
        else:
            formatted_text += clean_text
        
        if len(clean_text) >= 4:
            formatted_text += clean_text[2:4] + "/"
        elif len(clean_text) > 2:
            formatted_text += clean_text[2:4]
        
        if len(clean_text) > 4:
            formatted_text += clean_text[4:]
        
        prev_length = len(self.sender().text())
        
        self.sender().blockSignals(True)
        self.sender().setText(formatted_text)
        self.sender().blockSignals(False)
        
        if len(formatted_text) > prev_length:
            cursor_position += 1
        elif len(formatted_text) < prev_length:
            cursor_position -= 1
        
        self.sender().setCursorPosition(cursor_position)

    def delete_resolucion(self, container, resolucion_id=None):
        if resolucion_id:
            try:
                response = requests.post(f'{self.parent().api_base_url}deleteResolucion', json={'id': resolucion_id})
                response.raise_for_status()
                result = response.json()

                if result.get('message') == 'Resolución eliminada correctamente':
                    self.remove_resolucion_from_list(container)
                    self.parent().show_message("Info", "Eliminar", "Resolución eliminada correctamente.")
                else:
                    self.parent().show_message("Error", "Eliminar", result.get('message', 'Error desconocido'))

            except requests.RequestException as e:
                self.parent().show_message("Error", "Eliminar", str(e))
        else:
            self.remove_resolucion_from_list(container)

    def remove_resolucion_from_list(self, container):
        for i in range(self.resolucion_list.count()):
            item = self.resolucion_list.item(i)
            if self.resolucion_list.itemWidget(item) == container:
                self.resolucion_list.takeItem(i)
                break

    def save_resoluciones(self, silence=False):
        if not self.parent().current_formulario_id:
            self.parent().show_message("Error", "Guardar", "Seleccione un trabajo antes de guardar resoluciones.")
            return

        resoluciones_data = []
        for i in range(self.resolucion_list.count()):
            container = self.resolucion_list.itemWidget(self.resolucion_list.item(i))
            data = {
                'id': container.layout().itemAt(0).widget().text() or None,
                'n_resolucion': container.layout().itemAt(2).widget().text(),
                'f_resolucion': container.layout().itemAt(4).widget().text(),
            }
            resoluciones_data.append(data)

        try:
            response = requests.post(f'{self.parent().api_base_url}saveResoluciones', json={
                'trabajo_id': self.parent().current_trabajo_id,
                'formulario_id': self.parent().current_formulario_id,
                'resoluciones': resoluciones_data
            })
            response.raise_for_status()
            if not silence:
                self.accept()
                self.parent().show_message("Info", "Guardar", "Resoluciones guardadas exitosamente.")

            print("Resoluciones guardadas:", resoluciones_data)
        except requests.RequestException as e:
            if not silence:
                self.parent().show_message("Error", "Error al guardar resoluciones", str(e))
            print(f"Error al guardar resoluciones: {e}")

    def load_resoluciones(self):
        if not self.parent().current_formulario_id:
            return

        try:
            response = requests.get(f'{self.parent().api_base_url}getResoluciones&formulario_id={self.parent().current_formulario_id}')
            response.raise_for_status()
            resoluciones_data = response.json()
            if isinstance(resoluciones_data, list):
                for resolucion in resoluciones_data:
                    self.add_resolucion(resolucion)
        except requests.RequestException as e:
            print(f"Error al cargar resoluciones: {e}")
            self.parent().show_message("Error", "Error al cargar resoluciones", str(e))

    def closeEvent(self, event):
        self.save_resoluciones(silence=True)
        super().closeEvent(event)
