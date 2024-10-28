from PyQt5.QtWidgets import QCheckBox, QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QLineEdit, QCompleter
from PyQt5.QtCore import Qt
import sys,re
from comunas import Comunas_list


class Inscripcion(QWidget):
    def __init__(self):
        super().__init__() 
        self.id = None
        self.cbr =  ""
        self.foja = ""
        self.vta = False
        self.num = ""
        self.anio = ""
        
        self.inicializar_ui()

    def inicializar_ui(self):
        
        comunas_formatted_list = [
            comuna.upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
            for comuna in Comunas_list
        ]
        
        self.completer = QCompleter(comunas_formatted_list)
        self.completer.setCompletionMode(QCompleter.InlineCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        self.layout_cbr = QHBoxLayout()
        self.label_cbr =  QLabel("CBR")
        self.input_cbr = QLineEdit()
        self.input_cbr.setCompleter(self.completer)
        self.layout_cbr.addWidget(self.label_cbr)
        self.layout_cbr.addWidget(self.input_cbr)
        self.input_cbr.textChanged.connect(self.capture_cbr)
        self.input_cbr.returnPressed.connect(self.select_completion)
        
        self.layout_foja = QHBoxLayout()
        self.label_foja = QLabel("FOJA")
        self.input_foja = QLineEdit()
        self.layout_foja.addWidget(self.label_foja)
        self.layout_foja.addWidget(self.input_foja)
        self.input_foja.textChanged.connect(self.allow_only_numbers)
        
        self.layout_vta_num_anio = QHBoxLayout()
        self.label_vta = QLabel("V")
        self.checkbox_vta = QCheckBox()
        self.layout_vta_num_anio.addWidget(self.label_vta)
        self.layout_vta_num_anio.addWidget(self.checkbox_vta)
        self.checkbox_vta.stateChanged.connect(self.capturar_estado_vta)
        
        self.label_num = QLabel("N°")
        self.input_num = QLineEdit()
        self.layout_vta_num_anio.addWidget(self.label_num)
        self.layout_vta_num_anio.addWidget(self.input_num)
        self.input_num.textChanged.connect(self.allow_only_numbers)
        
        self.label_anio = QLabel("AÑO")
        self.input_anio = QLineEdit()
        self.layout_vta_num_anio.addWidget(self.label_anio)
        self.layout_vta_num_anio.addWidget(self.input_anio)
        self.input_anio.textChanged.connect(self.allow_only_four_digits)
        
        self.vLayout = QVBoxLayout()
        self.vLayout.addLayout(self.layout_cbr)
        self.vLayout.addLayout(self.layout_foja)
        
        self.layoutContainer = QWidget()
        self.layoutContainer.setLayout(self.vLayout)
        
        self.layoutContainer1 = QWidget()
        self.layout_vta_num_anio.setAlignment(Qt.AlignBottom)
        self.layoutContainer1.setLayout(self.layout_vta_num_anio)

        self.layoutContainer.setMinimumWidth(220)
        self.layoutContainer.setMaximumWidth(280)
        
        self.inscripcion_layout = QHBoxLayout()
        self.inscripcion_layout.addWidget(self.layoutContainer)
        self.inscripcion_layout.addWidget(self.layoutContainer1)
    
        self.setLayout(self.inscripcion_layout)
    
    def select_completion(self):
        if self.completer.completionCount() > 0:
            self.input_cbr.setText(self.completer.currentCompletion())
            self.completer.popup().hide()
        
    def on_delete(self):
        None
        
    def capturar_estado_vta(self, state):
        self.vta = (state == Qt.Checked)  
        
    def capture_cbr(self, text):
        
        cleaned_text = text.upper()
        cleaned_text = (cleaned_text
            .replace('Á', 'A')
            .replace('É', 'E')
            .replace('Í', 'I')
            .replace('Ó', 'O')
            .replace('Ú', 'U')
        )
        self.input_cbr.blockSignals(True)
        self.input_cbr.setText(cleaned_text)
        self.input_cbr.blockSignals(False)
        self.cbr = cleaned_text

    def allow_only_numbers(self, text):
        cleaned_text = re.sub(r'\D', '', text)

        sender = self.sender()
        if sender == self.input_foja:
            self.foja = cleaned_text 
        
            
        if sender == self.input_num:
            self.num = cleaned_text 
        
        sender.blockSignals(True)
        sender.setText(cleaned_text)
        sender.blockSignals(False)
        
    def allow_only_four_digits(self, text):
        cleaned_text = re.sub(r'\D', '', text)

        if len(cleaned_text) > 4:
            cleaned_text = cleaned_text[:4]

        self.anio = cleaned_text
        
        self.input_anio.blockSignals(True)
        self.input_anio.setText(cleaned_text)
        self.input_anio.blockSignals(False)
        
    def get_id(self):
        return self.id
    
    def set_id(self, id):
        self.id = id

    def set_cbr(self, text):
        self.cbr = text
        self.input_cbr.setText(text)

    def set_foja(self, text):
        self.foja = text
        self.input_foja.setText(text)

    def set_vta(self, valor):
        self.vta = valor
        self.checkbox_vta.setChecked(valor)

    def set_numero(self, text):
        self.num = text
        self.input_num.setText(text)

    def set_anio(self, text):
        self.anio = text
        self.input_anio.setText(text)
        

        
if __name__ == "__main__":
    app = QApplication(sys.argv)  
    main_window = QMainWindow()  
    inscripcion_widget = Inscripcion()
    main_window.setCentralWidget(inscripcion_widget)  
    main_window.setWindowTitle("Formulario de Inscripción")  
    main_window.show()  
    sys.exit(app.exec_())
