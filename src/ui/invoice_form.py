from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QPushButton, QFrame)
from PyQt5.QtCore import Qt

class InvoiceForm(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout()
        
        # Form layout (left side)
        form_container = QWidget()
        form_layout = QFormLayout()
        
        # Group Name
        self.group_name_combo = QComboBox()
        form_layout.addRow('Group Name:', self.group_name_combo)
        
        # Company Name
        self.company_name_combo = QComboBox()
        form_layout.addRow('Company Name:', self.company_name_combo)
        
        # Year
        self.year_combo = QComboBox()
        current_year = 2024
        for year in range(2022, current_year + 1):
            self.year_combo.addItem(str(year))
        form_layout.addRow('Year:', self.year_combo)
        
        # Invoice Period From
        self.period_from_combo = QComboBox()
        months = ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        self.period_from_combo.addItems(months)
        form_layout.addRow('Period From:', self.period_from_combo)
        
        # Invoice Period To
        self.period_to_combo = QComboBox()
        self.period_to_combo.addItems(months)
        form_layout.addRow('Period To:', self.period_to_combo)
        
        # Unit Sale Price
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setMaximum(999999.99)
        self.unit_price_spin.setDecimals(2)
        form_layout.addRow('Unit Sale Price (USD):', self.unit_price_spin)
        
        # Success Fee
        self.success_fee_spin = QDoubleSpinBox()
        self.success_fee_spin.setMaximum(100.0)
        self.success_fee_spin.setDecimals(2)
        form_layout.addRow('Success Fee (%):', self.success_fee_spin)
        
        # Exchange Rates
        self.usd_rate_spin = QDoubleSpinBox()
        self.usd_rate_spin.setMaximum(999.99)
        self.usd_rate_spin.setDecimals(4)
        form_layout.addRow('USD Exchange Rate:', self.usd_rate_spin)
        
        self.eur_rate_spin = QDoubleSpinBox()
        self.eur_rate_spin.setMaximum(999.99)
        self.eur_rate_spin.setDecimals(4)
        form_layout.addRow('EUR Exchange Rate:', self.eur_rate_spin)
        
        # Generate Button
        self.generate_btn = QPushButton('Generate Invoice')
        form_layout.addRow('', self.generate_btn)
        
        form_container.setLayout(form_layout)
        
        # Preview layout (right side)
        preview_container = QWidget()
        preview_layout = QVBoxLayout()
        
        preview_label = QLabel('Invoice Preview')
        preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        # Add a placeholder frame for the preview
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        preview_frame.setMinimumSize(400, 600)
        preview_layout.addWidget(preview_frame)
        
        preview_container.setLayout(preview_layout)
        
        # Add both containers to main layout
        main_layout.addWidget(form_container)
        main_layout.addWidget(preview_container)
        
        self.setLayout(main_layout) 