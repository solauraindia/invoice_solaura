from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QPushButton, QFrame, QCheckBox, QScrollArea, QGroupBox,
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from ..database.query import get_all_sellers_data, get_devices_by_pan, get_seller_pan, get_invoice_data
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvoiceForm(QWidget):
    def __init__(self):
        super().__init__()
        self.sellers_data = {}
        self.init_ui()
        self.load_sellers_data()

    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout()
        
        # Form layout (left side)
        form_container = QWidget()
        form_layout = QFormLayout()
        
        # Group Name
        self.group_name_combo = QComboBox()
        self.group_name_combo.currentTextChanged.connect(self.on_group_changed)
        form_layout.addRow('Group Name:', self.group_name_combo)
        
        # Company Name
        self.company_name_combo = QComboBox()
        self.company_name_combo.currentTextChanged.connect(self.on_company_changed)
        form_layout.addRow('Company Name:', self.company_name_combo)

        # Device Selection Area
        self.devices_group = QGroupBox("Select Devices")
        devices_layout = QVBoxLayout()
        
        # Add "Select All" checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        devices_layout.addWidget(self.select_all_checkbox)
        
        # Scroll area for device checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)
        
        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout()
        self.devices_container.setLayout(self.devices_layout)
        scroll.setWidget(self.devices_container)
        
        devices_layout.addWidget(scroll)
        self.devices_group.setLayout(devices_layout)
        form_layout.addRow(self.devices_group)
        
        # Hide devices group initially
        self.devices_group.hide()
        
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
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        form_layout.addRow('', self.generate_btn)
        
        form_container.setLayout(form_layout)
        
        # Preview layout (right side)
        preview_container = QWidget()
        preview_layout = QVBoxLayout()
        
        preview_label = QLabel('Invoice Preview')
        preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        # Create table for preview
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(0)
        self.preview_table.setRowCount(0)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        preview_layout.addWidget(self.preview_table)
        
        preview_container.setLayout(preview_layout)
        
        # Add both containers to main layout
        main_layout.addWidget(form_container)
        main_layout.addWidget(preview_container)
        
        self.setLayout(main_layout)

    def load_sellers_data(self):
        """Load sellers data from database and populate dropdowns"""
        try:
            self.sellers_data = get_all_sellers_data()
            logger.info("Successfully retrieved sellers data")
            logger.info(f"Groups found: {list(self.sellers_data.keys())}")
            
            # Populate group dropdown
            self.group_name_combo.clear()
            self.group_name_combo.addItems(sorted(self.sellers_data.keys()))
            
        except Exception as e:
            logger.error(f"Error loading sellers data: {str(e)}")

    def on_group_changed(self, group_name):
        """Handle group selection change"""
        self.company_name_combo.clear()
        if group_name in self.sellers_data:
            companies = [seller["seller"] for seller in self.sellers_data[group_name]]
            logger.info(f"Companies for group {group_name}: {companies}")
            self.company_name_combo.addItems(companies)

    def on_company_changed(self, company_name):
        """Handle company selection change"""
        group_name = self.group_name_combo.currentText()
        if group_name in self.sellers_data:
            for seller in self.sellers_data[group_name]:
                if seller["seller"] == company_name:
                    logger.info(f"Setting values for {company_name}")
                    self.success_fee_spin.setValue(float(seller["success_fee"]))
                    self.unit_price_spin.setValue(float(seller["indicative_price"]))
                    
                    # Get and display device IDs
                    self.load_devices(company_name, group_name)
                    break

    def load_devices(self, company_name, group_name):
        """Load and display device checkboxes"""
        try:
            # Clear existing checkboxes
            for i in reversed(range(self.devices_layout.count())):
                self.devices_layout.itemAt(i).widget().setParent(None)
            
            # Get PAN number for the selected company
            pan = get_seller_pan(company_name, group_name)
            if not pan:
                logger.error(f"No PAN found for {company_name}")
                self.devices_group.hide()
                return
                
            # Get device IDs
            devices = get_devices_by_pan(pan)
            if not devices:
                logger.info(f"No devices found for PAN: {pan}")
                self.devices_group.hide()
                return
                
            # Show devices group and add checkboxes
            self.devices_group.show()
            for device_id in devices:
                checkbox = QCheckBox(device_id)
                self.devices_layout.addWidget(checkbox)
                
            logger.info(f"Loaded {len(devices)} devices for {company_name}")
            
        except Exception as e:
            logger.error(f"Error loading devices: {str(e)}")
            self.devices_group.hide()

    def on_select_all_changed(self, state):
        """Handle select all checkbox state change"""
        for i in range(self.devices_layout.count()):
            checkbox = self.devices_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(state == Qt.Checked)

    def get_selected_devices(self):
        """Get list of selected device IDs"""
        selected = []
        for i in range(self.devices_layout.count()):
            checkbox = self.devices_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected.append(checkbox.text())
        return selected

    def on_generate_clicked(self):
        """Handle generate invoice button click"""
        try:
            # Get selected devices
            selected_devices = self.get_selected_devices()
            if not selected_devices:
                QMessageBox.warning(self, "Warning", "Please select at least one device.")
                return
            
            # Get form data
            year = int(self.year_combo.currentText())
            period_from = self.period_from_combo.currentText()
            period_to = self.period_to_combo.currentText()
            
            # Get invoice data
            invoice_data = get_invoice_data(
                selected_devices,
                year,
                period_from,
                period_to
            )
            
            if not invoice_data:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No invoice data found for the selected devices and period."
                )
                return
                
            logger.info(f"Retrieved invoice data for {len(invoice_data)} devices")
            self.display_invoice_data(invoice_data)
            
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate invoice: {str(e)}"
            )

    def display_invoice_data(self, invoice_data):
        """Display invoice data in the preview table"""
        if not invoice_data:
            return
            
        # Get all columns from the first row
        columns = list(invoice_data[0].keys())
        
        # Set up table
        self.preview_table.setRowCount(len(invoice_data))
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)
        
        # Populate table
        for row_idx, row_data in enumerate(invoice_data):
            for col_idx, column in enumerate(columns):
                value = row_data.get(column, '')
                # Format decimal numbers to 4 decimal places if applicable
                if isinstance(value, (float, int)):
                    item = QTableWidgetItem(f"{value:.4f}")
                else:
                    item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignRight if isinstance(value, (float, int)) else Qt.AlignLeft)
                self.preview_table.setItem(row_idx, col_idx, item)
        
        # Adjust table appearance
        self.preview_table.resizeColumnsToContents()
        self.preview_table.resizeRowsToContents() 