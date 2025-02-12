from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os
import sys
from .invoice_form import InvoiceForm

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def init_ui(self):
        self.setWindowTitle('Solaura Invoice Generator')
        self.setMinimumSize(1200, 800)

        # Set window icon
        icon_path = self.resource_path(os.path.join('src', 'public', 'invoice.ico'))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file not found at {icon_path}")

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create and add invoice form
        self.invoice_form = InvoiceForm()
        layout.addWidget(self.invoice_form)
        
        # Center the window
        self.setGeometry(100, 100, 1200, 800) 