from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from .invoice_form import InvoiceForm

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Invoice Generator')
        self.setMinimumSize(1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create and add invoice form
        self.invoice_form = InvoiceForm()
        layout.addWidget(self.invoice_form)
        
        # Center the window
        self.setGeometry(100, 100, 1200, 800) 