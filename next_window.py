from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QCompleter, QFrame, QHBoxLayout, QListWidget, QPushButton, QLabel, QScrollArea, QSpacerItem, QSizePolicy, QTextEdit, QDateEdit, QGridLayout, QSplitter, QComboBox, QLineEdit, QCheckBox, QMessageBox, QListWidgetItem,QInputDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QDate, QEvent,QRegExp
from PyQt5.QtGui import QIntValidator,QRegExpValidator, QColor
import requests,json,sys,re
from comunas import Comunas_list
from InscriptionModal import InscriptionModal
from ResolucionModal import ResolucionModal
from Titulo_Anterior_Modal import TituloModal
from UsuarioModal import UsuarioModal
from DetallesModal import DetallesModal
from datetime import datetime
from HistoryModal import HistoryModal

class NextWindow(QMainWindow):
    def __init__(self, user_id, user_name,Cantidad):
        super().__init__()
        self.user_id = user_id
        self.current_trabajo_id = None
        self.current_trabajo_info = None
        self.session_history = []
        self.current_formulario_id = None
        self.user_name = user_name
        self.inscripcion_layouts = {} 
        self.modal_abierto = False
        self.API_BASE_URL = 'https://api.loverman.net/dbase/dga2024/apiv3/api.php?action='
        self.api_base_url = self.API_BASE_URL
        self.setWindowTitle("SOLICITUD Formulario")
        self.setGeometry(1, 30, 1980, 1080)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        self.pdf_paths = []
        self.entries = []
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        
        self.set_title(Cantidad)
        self.create_left_frame()
        self.create_middle_frame()
        self.create_right_frame()
        
    def set_title(self,Cantidad):
        self.setWindowTitle(f"DPs Formulario ({self.user_name}) - {Cantidad} Terminados")
        
        
    def buscar_rut_api(self, rut):
        try:
            url = f"https://api.loverman.net/api/buscar_rut.php?rut={rut}"
            response = requests.get(url)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            print(f"Error al buscar RUT: {e}")
            return False, {}

    def create_left_frame(self):
        self.left_frame = QFrame(self)
        self.left_frame.setFrameShape(QFrame.StyledPanel)
        self.left_frame.setMaximumWidth(300)  # Establecer el ancho máximo a 300px
        self.layout.addWidget(self.left_frame)

        self.left_layout = QVBoxLayout(self.left_frame)
        
        self.history_layout = QHBoxLayout()

        self.dir_label = QLabel("Seleccione trabajo", self)
        
        self.history_layout.addWidget(self.dir_label)

        self.history_button = QPushButton("📋")
        self.history_button.setFixedWidth(30)
        self.history_button.clicked.connect(lambda: self.open_history_modal(history_list = self.session_history))
        self.history_layout.addWidget(self.history_button)

        self.left_layout.addLayout(self.history_layout)

        self.dir_listwidget = QListWidget(self)
        self.dir_listwidget.setMaximumHeight(180)
        self.dir_listwidget.itemSelectionChanged.connect(self.on_directory_select)
        self.left_layout.addWidget(self.dir_listwidget)
        
        self.dir_label = QLabel("Trabajos pendientes", self)
        self.left_layout.addWidget(self.dir_label)

        self.dir_pendientes_list = QListWidget(self)
        self.dir_pendientes_list.setMaximumHeight(180)
        self.dir_pendientes_list.itemSelectionChanged.connect(self.on_directory_select)
        self.left_layout.addWidget(self.dir_pendientes_list)

        self.devolver_button = QPushButton("Devolver a asignados", self)
        self.devolver_button.clicked.connect(self.devolver_a_asignados)
        self.devolver_button.setEnabled(False)
        self.left_layout.addWidget(self.devolver_button)

        self.dir_label = QLabel("Seleccione PDF", self)
        self.left_layout.addWidget(self.dir_label)
        self.pdf_listbox = QListWidget(self)
        self.pdf_listbox.itemSelectionChanged.connect(self.on_pdf_select)
        self.left_layout.addWidget(self.pdf_listbox)
        
        self.dir_listwidget.itemClicked.connect(lambda item: self.cambiar_seleccion(item, self.dir_listwidget))
        self.dir_pendientes_list.itemClicked.connect(lambda item: self.cambiar_seleccion(item, self.dir_pendientes_list))
        self.pdf_listbox.itemClicked.connect(lambda item: self.cambiar_seleccion(item, self.pdf_listbox))
        
        self.load_trabajos()

    def devolver_a_asignados(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de presionar el botóm.")
            return
        selected_items = self.dir_pendientes_list.selectedItems()

        if selected_items:
            self.update_trabajo_estado("Asignado")
            self.load_trabajos()
        self.current_trabajo_id = None
        self.devolver_button.setEnabled(False)

    def cambiar_seleccion(self, item, lista):
        current_item = lista.currentItem()
        selected_row = lista.row(item)

        if selected_row != current_item:
            lista.setCurrentRow(selected_row)
    
    def create_middle_frame(self):
        self.middle_frame = QFrame(self)
        self.middle_frame.setFrameShape(QFrame.StyledPanel)
        self.middle_frame.setMaximumWidth(800)
        self.middle_frame.setMinimumWidth(500)
        self.layout.addWidget(self.middle_frame)
        self.middle_layout = QVBoxLayout(self.middle_frame)
        self.middle_layout.setSpacing(5)
        self.middle_section_title_layout = QHBoxLayout()
        self.form_label = QLabel("Formulario", self)
        self.middle_section_title_layout.addWidget(self.form_label)
        self.skip_inscription_button = QPushButton("Saltar Inscripción ⏩", self)
        self.skip_inscription_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.skip_inscription_button.clicked.connect(self.skip_inscription)
        self.skip_inscription_button.setEnabled(False)
        self.middle_section_title_layout.addWidget(self.skip_inscription_button)
        self.middle_layout.addLayout(self.middle_section_title_layout)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.middle_layout.addWidget(self.scroll_area)
        self.form_widget = QWidget()
        self.scroll_area.setWidget(self.form_widget)
        self.form_layout = QVBoxLayout(self.form_widget)

        # APARTADO: INSCRIPCIONES
        self.add_section_title("DATOS SOLICITUD")
        self.principal_layout = QGridLayout()
        self.form_layout.addLayout(self.principal_layout)

        SOLICITUD_entry = self.add_input_field("SOLICITUD", "select", ['--','B.1', 'B.2','B.3','B.4','B.5','B.6','B.7','B.8','B.9'],parent_layout=self.principal_layout,row=0, col=0)
        self.add_input_field("F_RECEPCION", "date", parent_layout=self.principal_layout, row=0, col=1)

        SOLICITUD_entry.setFixedWidth(50)
        self.add_section_title("USUARIO")
        self.user_layout = QGridLayout()
        self.form_layout.addLayout(self.user_layout)
        self.add_input_field("RUT", "text", parent_layout=self.user_layout, row=0, col=0)
        self.add_button_rut = QPushButton("Buscar", self)
        self.add_button_rut.clicked.connect(self.handle_rut_search)
        self.user_layout.addWidget(self.add_button_rut, 0, 1)

        self.add_input_field("NAC", "select", ['--','CHILENA','EXTRANJERA'], parent_layout=self.user_layout, row=1, col=0)
        self.add_input_field("TIPO", "select", ['--','NATURAL','JURIDICA'], parent_layout=self.user_layout, row=1, col=1)
        self.add_input_field("GENERO", "select", ['--','F','M'], parent_layout=self.user_layout, row=1, col=2)
        self.add_input_field("NOMBRE", "text", parent_layout=self.user_layout, row=2, col=0)
        self.add_input_field("PARTERNO", "text", parent_layout=self.user_layout, row=3, col=0)
        self.add_input_field("MATERNO", "text", parent_layout=self.user_layout, row=3, col=1)

        self.add_section_title("RESOLUCION/SENTENCIA/EP")
        self.res_layout = QGridLayout()
        self.form_layout.addLayout(self.res_layout)
        self.add_input_field("N° DOC", "text", parent_layout=self.res_layout, row=0, col=0, size=0)
        self.add_input_field("F_DOC", "date", parent_layout=self.res_layout, row=0, col=1)
        self.add_res_button = QPushButton("Agregar RES/SENT/EP", self)
        self.add_res_button.clicked.connect(self.open_resolucion_modal)
        self.form_layout.addWidget(self.add_res_button)

        self.comunas_formatted_list = [
            comuna.upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
            for comuna in Comunas_list
        ]

        self.completer = QCompleter(self.comunas_formatted_list)
        self.completer.setCompletionMode(QCompleter.InlineCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.add_section_title("INSCRIPCIONES")
        self.inscriptions_layout = QGridLayout()
        self.form_layout.addLayout(self.inscriptions_layout)
        self.add_input_field("F_INSCRIPCION", "date", parent_layout=self.inscriptions_layout, row=0, col=0)
        self.add_input_field("CBR", "text", parent_layout=self.inscriptions_layout, row=2, col=0, size=0)
        self.add_input_field("FOJA", "number", parent_layout=self.inscriptions_layout, row=3, col=0, size=0)
        self.add_input_field("V", "checkbox", parent_layout=self.inscriptions_layout, row=3, col=1, size=0)
        self.add_input_field("N°", "number", parent_layout=self.inscriptions_layout, row=3, col=2, size=0)
        self.add_input_field("AÑO", "number", parent_layout=self.inscriptions_layout, row=3, col=3, size=0)
        self.add_inscription_button = QPushButton("Agregar Inscripción", self)
        self.add_inscription_button.clicked.connect(self.open_inscription_modal)
        self.form_layout.addWidget(self.add_inscription_button)
        # self.add_section_title("TIPO TRANSACCIÓN Y TIPO DE DERECHO")
        # self.transaction_and_right_layout = QGridLayout()
        # self.form_layout.addLayout(self.transaction_and_right_layout)
        # self.add_input_field("TIPO TRANSACCIÓN", "select", ['--', 'ARRENDAMIENTO', 'USUFRUCTO', 'NUDA PROPIEDAD', 'OTROS'], parent_layout=self.transaction_and_right_layout, row=0, col=0)
        # self.add_input_field("TIPO DERECHO", "select", ['--', 'PERFECTO', 'IMPERFECTO'], parent_layout=self.transaction_and_right_layout, row=0, col=1)


        self.add_section_title("TIPO DE DOCUMENTO")
        self.tipo_and_right_layout  = QComboBox()
        self.tipo_and_right_layout.wheelEvent = lambda event: event.ignore()
        opciones = ["--","SENTENCIA", "RESOLUCION DGA", "COMPRAVENTA", "COMUNIDAD DE AGUAS", "OTROS", "SIN DOC. AGUAS",'ARRENDAMIENTO', 'USUFRUCTO', 'NUDA PROPIEDAD']
        self.tipo_and_right_layout.addItems(opciones)
        self.tipo_and_right_layout.currentIndexChanged.connect(self.toggle_extra)
        self.form_layout.addWidget(self.tipo_and_right_layout)
        
      
        self.section_title_2 = QLabel("\nTÍTULO ANTERIOR", self)
        self.section_title_2.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.form_layout.addWidget(self.section_title_2)
        self.add_inscripcion_button = QPushButton("Agregar Titulo Anterior", self)
        self.form_layout.addWidget(self.add_inscripcion_button)
        self.add_inscripcion_button.clicked.connect(self.open_titulo_anterior_modal)
        
        self.section_title_2.hide()
        self.add_inscripcion_button.hide()
        
        self.extra_form_widget = QWidget(self)
        self.extra_form_layout = QVBoxLayout(self.extra_form_widget)
        
        # TIPO DE EXPEDIENTE
        title_label = QLabel("TIPO DE EXPEDIENTE")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 5px;")
        self.extra_form_layout.addWidget(title_label)
        self.add_input_field("NATURALEZA DEL AGUA", "select", ['--','SUPERFICIAL', 'SUBTERRANEA', "S. Y DETENIDA", "SUP. Y CORRIENTE", "SUP. CORRIENTES/DETENIDAS"], parent_layout=self.extra_form_layout)
        self.add_input_field("TIPO DE DERECHO", "select", ['--','CONSUNTIVO','NO CONSUNTIVO'], parent_layout=self.extra_form_layout)
        self.add_input_field("NOMBRE DE COMUNIDAD", "text", parent_layout=self.extra_form_layout)
        self.add_input_field("PROYECTO DE PARCELACIÓN", "text", parent_layout=self.extra_form_layout)
        self.add_input_field("SITIO", "text", parent_layout=self.extra_form_layout)
        self.add_input_field("PARCELA", "text", parent_layout=self.extra_form_layout)

        # USUARIOS
        self.add_section_title("USUARIOS", parent_layout=self.extra_form_layout)
        self.user_layout = QGridLayout()
        self.add_user_button = QPushButton("Agregar Usuarios", self)
        self.add_user_button.clicked.connect(self.open_usuarios_modal)
        self.user_layout.addWidget(self.add_user_button)
        self.extra_form_layout.addLayout(self.user_layout)

        # EJERCICIO
        self.add_section_title("EJERCICIO", parent_layout=self.extra_form_layout)
        self.add_input_field("EJERCICIO DEL DERECHO", "select", ['--','PERMANENTE Y CONTINUO', 'EVENTUAL Y CONTINUO', 'PERM. Y CONT. Y PROVICIONALES'], parent_layout=self.extra_form_layout)
        self.add_input_field("METODO DE EXTRACCION", "select", ['--','MECANICA','GRAVITACIONAL','MECANICA Y/O GRAVITACIONAL'], parent_layout=self.extra_form_layout)

        # CAUDAL
        self.add_section_title("CAUDAL", parent_layout=self.extra_form_layout)
        self.add_input_field("CANTIDAD", "text", parent_layout=self.extra_form_layout)
        self.add_input_field("UNIDAD", "select", ['--','LT/S','M3/S','MM3/AÑO','M3/AÑO','LT/MIN','M3/H','LT/H','M3/MES','ACCIONES','M3/DIA','M3/MIN','LT/DIA','REGADORES','CUADRAS','TEJAS','HORAS TURNO','%','PARTES','LT/MES','MMM3/MES','M3/HA/MES', 'ETC'], parent_layout=self.extra_form_layout)
        self.add_input_field("UTM NORTE", "text", parent_layout=self.extra_form_layout)
        self.add_input_field("UTM ESTE", "text", parent_layout=self.extra_form_layout)
        self.add_input_field("UNIDAD UTM", "select", ['--','KM', 'MTS'], parent_layout=self.extra_form_layout)
        self.add_input_field("HUSO", "select", ['--','18', '19'], parent_layout=self.extra_form_layout)
        self.add_input_field("DATUM", "select", ['--','56', '69','84'], parent_layout=self.extra_form_layout)

        # APARTADO: REFERENCIAS
        self.add_section_title("REFERENCIAS", parent_layout=self.extra_form_layout)
        self.add_input_field("PTOS CONOCIDOS DE CAPTACION", "textarea", parent_layout=self.extra_form_layout)
        self.add_detalles_button = QPushButton("Agregar Caudales Extra", self)
        self.add_detalles_button.clicked.connect(self.open_detalles_modal)
        self.extra_form_layout.addWidget(self.add_detalles_button)


        self.extra_form_widget.hide()
        self.form_layout.addWidget(self.extra_form_widget)
        
        # INTERNO
        self.extra_form_obs_widget = QWidget(self)
        self.extra_form_obs_layout = QVBoxLayout(self.extra_form_obs_widget)
        self.add_input_field("OBS", "select", ['--','SIN RUT', 'PERFECTO','NO SE LEE'], parent_layout=self.extra_form_obs_layout)
        self.add_section_title("INTERNO", parent_layout=self.extra_form_obs_layout)
        self.add_input_field("COMENTARIO", "textarea", parent_layout=self.extra_form_obs_layout)
        self.extra_form_obs_widget.hide()
        self.form_layout.addWidget(self.extra_form_obs_widget)
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.form_layout.addItem(spacer)
        self.save_button = QPushButton("Guardar", self)
        self.save_button.clicked.connect(self.save_form)
        self.middle_layout.addWidget(self.save_button)
        
        self.submit_button = QPushButton("Registrar", self)
        self.submit_button.clicked.connect(self.submit_form)
        self.middle_layout.addWidget(self.submit_button)
        
    def skip_inscription(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de presionar el boton.")
            return
        self.save_form(True)
        self.update_trabajo_estado("Pendiente")
        self.load_trabajos()
        self.clear_pdf_viewer()
        self.clear_pdf_list()
        self.current_trabajo_id = None
        self.skip_inscription_button.setEnabled(False)
        

    def toggle_extra(self):
        tipo = self.tipo_and_right_layout.currentText()
        self.section_title_2.hide()
        self.add_inscripcion_button.hide()
        self.extra_form_widget.hide()
        self.extra_form_obs_widget.hide()
        if tipo == 'COMPRAVENTA':
            self.section_title_2.show()
            self.add_inscripcion_button.show()
            self.add_inscripcion_button.setFocus()
        elif tipo == 'OTROS':
            self.extra_form_widget.show()
        else:
            pass
        self.extra_form_obs_widget.show()

    def fill_form(self, formulario):
        self.clear_form()

        field_mapping = {
            'f_recepcion': 'F_RECEPCION',
            'solicitud': 'SOLICITUD',
            'n_doc': 'N° DOC',
            'f_doc': 'F_DOC',
            'f_inscripcion': 'F_INSCRIPCION',
            'comuna': 'COMUNA',
            'cbr': 'CBR',
            'foja': 'FOJA',
            'v': 'V',
            'numero': 'N°',
            'anio': 'AÑO',
            'rut': 'RUT',
            'nac': 'NAC',
            'tipo': 'TIPO',
            'genero': 'GENERO',
            'nombre': 'NOMBRE',
            'paterno': 'PARTERNO',
            'materno': 'MATERNO',
            'comentario': 'COMENTARIO',
            'tipo_transaccion': 'TIPO TRANSACCIÓN',
            'tipo_de_derecho': 'TIPO DERECHO',
            'OBS': 'OBS'
        }

        for json_key, form_label in field_mapping.items():
            if json_key in formulario:
                entry_value = formulario[json_key]
                
                if json_key == 'rut' and entry_value:
                    entry_value = self.verificar_rut(entry_value)['rut']
                
                for label, entry in self.entries:
                    if label == form_label:
                        if isinstance(entry, QLineEdit):
                            entry.setText(entry_value if entry_value is not None else "")
                        elif isinstance(entry, QComboBox):
                            index = entry.findText(entry_value if entry_value is not None else "")
                            if index >= 0:
                                entry.setCurrentIndex(index)
                        elif isinstance(entry, QCheckBox):
                            entry.setChecked(entry_value.lower() in ['true', '1'] if entry_value is not None else False)
                        elif isinstance(entry, QTextEdit):
                            entry.setPlainText(entry_value if entry_value is not None else "")
                        elif isinstance(entry, QDateEdit) and entry_value:
                            entry.setDate(QDate.fromString(entry_value, "dd/MM/yyyy"))

        print("Formulario cargado 2:", formulario)

    def load_trabajos(self):
        try:
            self.dir_listwidget.clear()
            self.dir_pendientes_list.clear()
            response = requests.get(f'{self.API_BASE_URL}getTrabajos&user_id={self.user_id}')
            response.raise_for_status()
            trabajos = response.json()
            for trabajo in trabajos:
                item = QListWidgetItem(f"{trabajo['id']} - {trabajo['carpeta']} ({trabajo['estado']})")
                item.setData(Qt.UserRole, trabajo['id'])
                if trabajo['estado']=="Pendiente":
                    self.dir_pendientes_list.addItem(item)
                elif trabajo['estado']=="Terminado":
                    item.setForeground(QColor('green'))
                    self.dir_listwidget.addItem(item)
                else:
                    self.dir_listwidget.addItem(item)
        except requests.RequestException as e:
            self.show_message("Error", "Error al cargar trabajos", str(e))

    def load_formulario(self, trabajo_id):

        self.clear_form()
        try:
            response = requests.get(f'{self.API_BASE_URL}getFormulario&trabajo_id={trabajo_id}')
            response.raise_for_status()
            formulario = response.json()
            self.current_formulario_id = formulario.get("formulario_id")
            self.current_trabajo_id = formulario.get("trabajo_id")
            self.fill_form(formulario)
            tipo_documento = formulario.get("tipo_documento", "--")
            tipo_documento_index = self.tipo_and_right_layout.findText(tipo_documento)
            self.tipo_and_right_layout.setCurrentIndex(tipo_documento_index)
            self.toggle_extra()
            if tipo_documento == "OTROS":
                self.fill_extra_fields(formulario)
            
        except requests.RequestException as e:
            self.show_message("Error", "Error al cargar el formulario", str(e))

    def fill_extra_fields(self, formulario):
        """
        Llena los campos adicionales en el formulario extra cuando el tipo de documento es 'OTROS'.
        """
        extra_field_mapping = {
            'naturaleza_agua': "NATURALEZA DEL AGUA",
            'tipo_derecho': "TIPO DE DERECHO",
            'nombre_comunidad': "NOMBRE DE COMUNIDAD",
            'proyecto_parcelacion': "PROYECTO DE PARCELACIÓN",
            'sitio': "SITIO",
            'parcela': "PARCELA",
            'ejercicio_derecho': "EJERCICIO DEL DERECHO",
            'metodo_extraccion': "METODO DE EXTRACCION",
            'cantidad': "CANTIDAD",
            'unidad': "UNIDAD",
            'utm_norte': "UTM NORTE",
            'utm_este': "UTM ESTE",
            'unidad_utm': "UNIDAD UTM",
            'huso': "HUSO",
            'datum': "DATUM",
            'pto_conocidos_captacion': "PTOS CONOCIDOS DE CAPTACION"
        }

        for json_key, form_label in extra_field_mapping.items():
            if json_key in formulario:
                entry_value = formulario[json_key]
                for label, entry in self.entries:
                    if label == form_label:
                        if isinstance(entry, QLineEdit):
                            entry.setText(entry_value if entry_value is not None else "")
                        elif isinstance(entry, QComboBox):
                            index = entry.findText(entry_value if entry_value is not None else "")
                            if index >= 0:
                                entry.setCurrentIndex(index)
                        elif isinstance(entry, QCheckBox):
                            entry.setChecked(entry_value.lower() in ['true', '1'] if entry_value is not None else False)
                        elif isinstance(entry, QTextEdit):
                            entry.setPlainText(entry_value if entry_value is not None else "")
                        elif isinstance(entry, QDateEdit) and entry_value:
                            entry.setDate(QDate.fromString(entry_value, "dd/MM/yyyy"))
        print("Campos adicionales llenados para 'OTROS'")            
                
    def on_directory_select(self):
        selected_items = []

        if self.sender() == self.dir_listwidget:
            self.dir_pendientes_list.clearSelection()
            selected_items = self.dir_listwidget.selectedItems()
            self.devolver_button.setEnabled(False)
            self.skip_inscription_button.setEnabled(True)

        elif self.sender() == self.dir_pendientes_list:
            self.dir_listwidget.clearSelection()
            selected_items = self.dir_pendientes_list.selectedItems()
            self.devolver_button.setEnabled(True)
            self.skip_inscription_button.setEnabled(False)
            
        if selected_items:
            selected_item = selected_items[0]
            selected_trabajo_id = selected_item.data(Qt.UserRole)
            
            if self.current_trabajo_id is not None and self.current_trabajo_id != selected_trabajo_id:
                self.save_form(True)

            self.current_trabajo_id = selected_trabajo_id
            
            item_info = selected_item.text()

            self.current_trabajo_info = {
                "trabajo": item_info.split("(")[0].strip(),
                "estado_anterior": item_info.split("(")[-1].replace(")","").strip()
            }

            if self.current_trabajo_info['estado_anterior']=="Terminado":
                self.skip_inscription_button.setEnabled(False)
            
            print(f"Trabajo seleccionado: {selected_trabajo_id}")
            self.load_formulario(selected_trabajo_id)
            self.clear_pdf_list()
            self.clear_pdf_viewer()
            self.load_pdfs(selected_trabajo_id)

    def load_pdfs(self, trabajo_id):
        try:
            response = requests.get(f'{self.API_BASE_URL}getPDFs&trabajo_id={trabajo_id}')
            response.raise_for_status()
            pdfs = response.json()
            self.pdf_listbox.clear()
            self.pdf_paths = []
            for pdf in pdfs:
                self.pdf_listbox.addItem(pdf['nombre'])
                self.pdf_paths.append(pdf['ruta'])
        except requests.RequestException as e:
            self.show_message("Error", "Error al cargar PDFs", str(e))

    def on_pdf_select(self):
        selected_items = self.pdf_listbox.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            index = self.pdf_listbox.row(selected_item)
            pdf_url = self.pdf_paths[index]
            print(f"PDF seleccionado: {pdf_url}")
            self.load_pdf(pdf_url)

    def load_pdf(self, encoded_pdf_path):
        try:
            pdf_url = f"https://loverman.net/dbase/dga2024/viewer.html?file={encoded_pdf_path}#page=1"
            self.browser.load(QUrl(pdf_url))
            print(f"Mostrando PDF desde URL: {pdf_url}")
        except Exception as e:
            self.show_message("Error", "Error al cargar PDF", str(e))

    def load_text_file(self, pdf_url):
        txt_url = pdf_url.replace('.pdf', '.txt').replace('.PDF', '.txt')
        try:
            response = requests.get(txt_url)
            response.raise_for_status()
            if response.status_code == 200:
                content = response.text
                self.text_edit.setText(content)
            else:
                self.text_edit.clear()
        except requests.RequestException as e:
            print(f"Error al cargar el archivo de texto: {e}")
            self.text_edit.clear()

    def navigate_pdf(self, direction):
        if self.pdf_doc:
            self.page_number = max(0, min(self.pdf_doc.page_count - 1, self.page_number + direction))
            self.show_pdf_page(self.page_number)
            self.page_label.setText(f"Página {self.page_number + 1} de {self.pdf_doc.page_count}")

    def handle_rut_search(self):
        rut_entry = None
        for label, entry in self.entries:
            if label == "RUT":
                rut_entry = entry
                break

        if rut_entry:
            rut = rut_entry.text().split("-")[0]
            success, data = self.buscar_rut_api(rut)
            print(f"{success} - {data}")
            if success:
                self.fill_user_fields(data)
            else:
                self.show_message("Info", "Buscar RUT", "No se encontraron datos para el RUT ingresado.")
                
    def fill_user_fields(self, data):
        field_mapping = {
            'NAC': 'NAC',
            'TIPO': 'P',
            'GENERO': 'G',
            'NOMBRE': 'Nombre',
            'PARTERNO': 'Apa',
            'MATERNO': 'Ama'
        }

        for json_key, form_label in field_mapping.items():
            entry_value = data.get(form_label, "")
            for label, entry in self.entries:
                if label == json_key:
                    if isinstance(entry, QLineEdit):
                        entry.setText(entry_value)
                    elif isinstance(entry, QComboBox):
                        index = entry.findText(entry_value)
                        if index >= 0:
                            entry.setCurrentIndex(index)
                            
    def create_right_frame(self):
        self.right_frame = QFrame(self)
        self.right_frame.setFrameShape(QFrame.StyledPanel)
        self.layout.addWidget(self.right_frame, stretch=1)
        self.right_layout = QVBoxLayout(self.right_frame)
        self.top_frame = QFrame(self)
        self.right_layout.addWidget(self.top_frame)
        self.top_layout = QHBoxLayout(self.top_frame)
        self.splitter = QSplitter(Qt.Vertical)
        self.right_layout.addWidget(self.splitter, stretch=1)
        self.browser = QWebEngineView()
        self.splitter.addWidget(self.browser)
        self.splitter.setSizes([800, 400])

    def add_input_field(self, label_text, field_type="text", options=None, parent_layout=None, row=0, col=0, size=None):
        if parent_layout is None:
            parent_layout = self.form_layout
        container = QFrame(self.form_widget)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(3)

        label = QLabel(label_text)
        container_layout.addWidget(label)

        field_type = field_type.strip().lower()
        entry = None

        if field_type == "text":
            entry = QLineEdit()
            entry.textChanged.connect(lambda: self.to_uppercase(entry))
            if size:
                entry.setFixedWidth(size)
            if label_text == "RUT":
                entry.focusOutEvent = lambda event: self.on_rut_focus_out(entry, event)
            if label_text == "CBR":
                entry.setCompleter(self.completer)
                entry.returnPressed.connect(self.select_completion)
                
        elif field_type == "number":
            entry = QLineEdit()
            entry.setValidator(QIntValidator())
            if size:
                entry.setFixedWidth(size)
            if label_text == "AÑO":
                entry.setMaxLength(4)
        elif field_type == "select":
            entry = QComboBox()
            entry.wheelEvent = lambda event: event.ignore()
            if options:
                entry.addItems(options)
        elif field_type == "date":
            entry = QLineEdit()
            entry.setPlaceholderText("--/--/----")
            if size:
                entry.setFixedWidth(size)
            date_regex = QRegExp(r"\d{0,8}")
            date_validator = QRegExpValidator(date_regex)
            entry.setValidator(date_validator)
            entry.textChanged.connect(lambda: self.auto_format_date(entry))
        elif field_type == "checkbox":
            entry = QCheckBox()
        elif field_type == "textarea":
            entry = QTextEdit()
            entry.setMinimumHeight(100)  # Altura mínima
            entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum) 
            entry.textChanged.connect(lambda: self.adjust_height(entry))
            entry.textChanged.connect(lambda: self.to_uppercase(entry))
        else:
            raise ValueError(f"Tipo de campo desconocido: {field_type}")

        container_layout.addWidget(entry)
        self.entries.append((label_text, entry))

        if isinstance(parent_layout, QGridLayout):
            parent_layout.addWidget(container, row, col)
        else:
            parent_layout.addWidget(container)
        print(f"Campo agregado: {label_text}, tipo: {field_type}")
        return entry
    
    def select_completion(self):
        if self.completer.completionCount() > 0:
            self.sender().setText(self.completer.currentCompletion())
        self.sender().focusNextPrevChild(True)
    
    def adjust_height(self,entry):
        height = int(entry.document().size().height()) + 5
        entry.setFixedHeight(max(height, 100))

    def auto_format_date(self, entry):
        sender = self.sender()
        text = sender.text()
        cursor_pos = sender.cursorPosition()
        
        cleaned_text = ''.join(filter(str.isdigit, text))
        
        if len(cleaned_text) > 8:
            cleaned_text = cleaned_text[:8]
        
        formatted_text = ''
        for i, char in enumerate(cleaned_text):
            if i == 2 or i == 4:
                formatted_text += '/'
            formatted_text += char

        prev_barras = text[:cursor_pos].count('/')
        new_barras = formatted_text[:cursor_pos].count('/')
        adjustment = new_barras - prev_barras
        new_cursor_pos = cursor_pos + adjustment
        
        sender.blockSignals(True)
        sender.setText(formatted_text)
        sender.setCursorPosition(new_cursor_pos)
        sender.blockSignals(False)
    
    def add_section_title(self, title, parent_layout=None):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 5px;")
        
        if parent_layout:
            parent_layout.addWidget(title_label)
        else:
            self.form_layout.addWidget(title_label)

    def add_inscription(self):
        count = len([entry for entry in self.entries if entry[0].startswith("F_INSCRIPCION")]) + 1
        self.add_input_field(f"F_INSCRIPCION_{count}", "date")
        self.add_input_field(f"COMUNA_{count}", "select", ["--", "Comuna1", "Comuna2"])
        self.add_input_field(f"CBR_{count}", "text")
        self.add_input_field(f"FOJA_{count}", "number")
        self.add_input_field(f"V_{count}", "checkbox")
        self.add_input_field(f"N°_{count}", "number")
        self.add_input_field(f"AÑO_{count}", "number")

    def buscar_rut(self):
        rut = None
        for label_text, entry in self.entries:
            if label_text.startswith("RUT"):
                rut = entry.text()
                break
        self.show_message("Info", "Buscar RUT", f"Buscando información para RUT: {rut}")

    def save_form(self,silence=False):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de guardar.")
            return
        form_data = {}
        for label_text, entry in self.entries:
            if isinstance(entry, QLineEdit):
                form_data[label_text] = {"type": "QLineEdit", "value": entry.text()}
            elif isinstance(entry, QComboBox):
                form_data[label_text] = {"type": "QComboBox", "value": entry.currentText()}
            elif isinstance(entry, QCheckBox):
                form_data[label_text] = {"type": "QCheckBox", "value": entry.isChecked()}
            elif isinstance(entry, QTextEdit):
                form_data[label_text] = {"type": "QTextEdit", "value": entry.toPlainText()}
            elif isinstance(entry, QDateEdit):
                form_data[label_text] = {"type": "QDateEdit", "value": entry.date().toString("dd/MM/yyyy")}

        form_data['user_id'] = self.user_id
        form_data['trabajo_id'] = self.current_trabajo_id
        form_data['formulario_id'] = self.current_formulario_id
        form_data['tipo_doc'] = self.tipo_and_right_layout.currentText()
        print("Datos del formulario que se enviarán:", json.dumps(form_data, indent=4))

        try:
            response = requests.post('https://api.loverman.net/dbase/dga2024/apiv3/api.php?action=saveForm', json=form_data)
            print(f"Response: {response.text}")
            response.raise_for_status()
            if not silence:
                self.show_message("Info", "Guardar", "Formulario guardado exitosamente.")
                print("Formulario guardado:", form_data)
        except requests.RequestException as e:
            if not silence:
                self.show_message("Error", "Error al guardar formulario", str(e))
                print(f"Error al guardar formulario: {e}")

    def load_form(self, trabajo_id):
        self.section_title_2.hide()
        self.add_inscripcion_button.hide()
        self.extra_form_widget.hide()
        self.clear_form()
        try:
            response = requests.get(f'{self.API_BASE_URL}getForm&trabajo_id={trabajo_id}')
            response.raise_for_status()
            form_data = response.json()
            for label_text, data in form_data.items():
                entry_type = data["type"]
                entry_value = data["value"]
                if not any(label == label_text for label, _ in self.entries):
                    if entry_type == "QLineEdit":
                        self.add_input_field(label_text, "text")
                    elif entry_type == "QComboBox":
                        self.add_input_field(label_text, "select", [])
                    elif entry_type == "QCheckBox":
                        self.add_input_field(label_text, "checkbox")
                    elif entry_type == "QTextEdit":
                        self.add_input_field(label_text, "textarea")
                    elif entry_type == "QDateEdit":
                        self.add_input_field(label_text, "date")
                for label, entry in self.entries:
                    if label == label_text:
                        if entry_type == "QLineEdit":
                            entry.setText(entry_value)
                        elif entry_type == "QComboBox":
                            index = entry.findText(entry_value)
                            if index >= 0:
                                entry.setCurrentIndex(index)
                        elif entry_type == "QCheckBox":
                            entry.setChecked(entry_value)
                        elif entry_type == "QTextEdit":
                            entry.setPlainText(entry_value)
                        elif entry_type == "QDateEdit":
                            entry.setDate(QDate.fromString(entry_value, "dd/MM/yyyy"))
            print("Formulario cargado 1:", form_data)
            
        except requests.RequestException as e:
            print(f"Fallo cargar: {e}")
            self.show_message("Error", "Error al cargar formulario", str(e))
            
    def clear_form(self):
        for _, entry in self.entries:
            if isinstance(entry, QLineEdit):
                entry.clear()
            elif isinstance(entry, QComboBox):
                entry.setCurrentIndex(-1)
            elif isinstance(entry, QDateEdit):
                entry.setDate(QDate.fromString("01/01/1985", "dd/MM/yyyy"))
            elif isinstance(entry, QTextEdit):
                entry.clear()
            elif isinstance(entry, QCheckBox):
                entry.setChecked(False)
        print("Formulario limpiado")

    def submit_form(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de guardar.")
            return
        self.save_form()
        self.update_trabajo_estado("Terminado")
        self.load_trabajos()
        self.clear_pdf_viewer()
        self.clear_pdf_list()
        self.current_trabajo_id = None
        self.skip_inscription_button.setEnabled(False)
        self.devolver_button.setEnabled(False)

    def clear_pdf_list(self):
        self.pdf_listbox.clear()
        self.pdf_paths = []

    def clear_pdf_viewer(self):
        self.browser.setUrl(QUrl())
    
    
    def update_trabajo_estado(self, estado):
        try:
            if not self.current_trabajo_id or not self.current_formulario_id:
                self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de guardar.")
                return
            if self.current_trabajo_info['estado_anterior'] == "Terminado":
                return
            
            response = requests.post(f'{self.API_BASE_URL}updateTrabajoEstado', json={
                'trabajo_id': self.current_trabajo_id,
                'estado': estado
            })
            response.raise_for_status()
            
            response_data = response.json()

            terminados_count = response_data['terminados_count'] if "terminados_count" in response_data else  "<Sin respuesta>"
            
            self.set_title(terminados_count)
                
            history_record = {
                "trabajo":self.current_trabajo_info['trabajo'],
                "estado_anterior": self.current_trabajo_info['estado_anterior'],
                "estado_nuevo": estado,
                "terminados_count":  terminados_count,
                "datetime": self.get_datetime()
            }
            
            self.session_history.insert(0, history_record)

            self.show_message("Info", "Estado Actualizado", f"El estado del trabajo se ha actualizado a {estado}.")
            self.scroll_area.verticalScrollBar().setValue(0)
            
        except requests.RequestException as e:
            self.show_message("Error", "Error al actualizar estado", str(e))
            print(f"Error al actualizar estado: {e}")

    def show_message(self, message_type, title, message):
        msg_box = QMessageBox()
        if message_type == "Error":
            msg_box.setIcon(QMessageBox.Critical)
        elif message_type == "Info":
            msg_box.setIcon(QMessageBox.Information)
        elif message_type == "Warning":
            msg_box.setIcon(QMessageBox.Warning)
        else:
            msg_box.setIcon(QMessageBox.NoIcon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    def open_inscription_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        self.modal_abierto = True
        self.inscription_modal = InscriptionModal(self)
        self.inscription_modal.show()
        self.inscription_modal.finished.connect(self.on_modal_closed)
        
        
    def open_titulo_anterior_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        self.modal_abierto = True
        self.Titulo_modal = TituloModal(self)
        self.Titulo_modal.show()
        self.Titulo_modal.finished.connect(self.on_modal_closed)
        
    def open_detalles_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        
        self.modal_abierto = True
        self.details_modal = DetallesModal(self)
        self.details_modal.show()
        self.details_modal.finished.connect(self.on_modal_closed)

    def open_usuarios_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        
        self.modal_abierto = True
        self.usuario_modal = UsuarioModal(self)
        self.usuario_modal.show() 
        self.usuario_modal.finished.connect(self.on_modal_closed)
        if self.usuario_modal.loaded_ruts_with_error:
            message = "Los siguientes ruts son inválidos:\n"
            for rut in self.usuario_modal.loaded_ruts_with_error:
                message += f"\n'{rut}'"
            self.show_message("Info", "Ruts inválidos", message)
            
    def open_history_modal(self, history_list):
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        self.modal_abierto = True
        self.history_modal = HistoryModal(self, history_list=history_list)
        self.history_modal.show()
        self.history_modal.finished.connect(self.on_modal_closed)

    def open_resolucion_modal(self):
        if not self.current_trabajo_id or not self.current_formulario_id:
            self.show_message("Error", "Seleccionar Trabajo", "Debe seleccionar un trabajo antes de continuar.")
            return
        if self.modal_abierto:
            self.show_message("Error", "Acción no permitida", "Ya hay un modal abierto.")
            return
        self.modal_abierto = True
        self.resolucion_modal = ResolucionModal(self)
        self.resolucion_modal.show()
        self.resolucion_modal.finished.connect(self.on_modal_closed)

    def on_modal_closed(self):
        self.modal_abierto = False

        
    def on_rut_focus_out(self, entry, event):
        try:
            formatted_rut=""
            text = entry.text()
            base_rut = re.sub(r'\D', '', text.strip().split("-")[0])

            if len(base_rut) > 8:
                base_rut = base_rut[:8] 
            
            if len(base_rut)>=6:
                dv = self.calculate_dv(base_rut)
                formatted_rut = f"{base_rut}-{dv}"
            entry.blockSignals(True)
            entry.setText(formatted_rut)
            entry.blockSignals(False)
        except:
            pass
        QLineEdit.focusOutEvent(entry, event)
        
    def calculate_dv(self, rut):
        reversed_digits = map(int, reversed(rut))
        factors = [2, 3, 4, 5, 6, 7] 
        s = sum(d * f for d, f in zip(reversed_digits, factors * 3))
        dv = 11 - (s % 11)
        if dv == 11:
            return '0'
        elif dv == 10:
            return 'K'
        else:
            return str(dv)
        
    def show_rut_error(self, rut,error):
        self.show_message("Info", "Rut inválido", f'Rut "{rut}" con formato incorrecto, por favor corregir. (xxxxxxxx-x)\n\nError: {error}')
        
    def verificar_rut(self, rut, show_messages = True):
        rut = rut.replace(" ","").upper()
        errorWasFounded = False
        try:
            rut = rut.replace(" ","").upper()
            if "-" not in rut:
                errorWasFounded = True
                if show_messages:
                    self.show_rut_error(rut, "Falta '-'")
            elif not rut.replace("-","")[:-1].isdigit() and (rut.replace("-","")[-1].isdigit() or rut.replace("-","")[-1] == 'K'):
                errorWasFounded = True
                if show_messages:
                    self.show_rut_error(rut, "Hay caracteres no permitidos")
            else:
                base = rut.split("-")[0]
                dv = rut.split("-")[-1]

                if 6 > len(base) > 8:
                    errorWasFounded = True
                    if show_messages:
                        self.show_rut_error(rut, "Comprobación de longitud")

                else:
                    calculated_dv = self.calculate_dv(base)
                    if dv!=calculated_dv:
                        errorWasFounded = True
                        if show_messages:
                            self.show_rut_error(rut, "Dígito verificador incorrecto")

            return {"rut":rut, "errorWasFounded": errorWasFounded}


        except (ValueError, IndexError) as e:
            print(f"Error al verificar rut")
            return {"rut":rut, "errorWasFounded": False}
    
    def get_datetime(self):
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
    def to_uppercase(self, entry):
        entry.blockSignals(True)
        if isinstance(entry, QLineEdit):
            cursor_position = entry.cursorPosition() 
            entry.setText(entry.text().upper())  
            entry.setCursorPosition(cursor_position)
        elif isinstance(entry, QTextEdit):
            cursor_position = entry.textCursor().position()
            entry.setPlainText(entry.toPlainText().upper())
            cursor = entry.textCursor()
            cursor.setPosition(cursor_position)
            entry.setTextCursor(cursor)
        entry.blockSignals(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    next_window = NextWindow(1,'Ed',1)
    next_window.showMaximized()
    next_window.show()
    sys.exit(app.exec_())
