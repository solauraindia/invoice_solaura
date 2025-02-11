from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QPushButton, QFrame, QCheckBox, QScrollArea, QGroupBox,
                             QMessageBox, QTextBrowser)
from PyQt5.QtCore import Qt
from ..database.query import (get_all_sellers_data, get_devices_by_pan, get_seller_pan, 
                           get_invoice_data, get_registered_devices)
from ..calculations.invoice_calculator import InvoiceCalculator
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
        
        # Create text browser for preview
        self.preview_text = QTextBrowser()
        self.preview_text.setMinimumWidth(400)
        preview_layout.addWidget(self.preview_text)
        
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
            unit_price = self.unit_price_spin.value()
            success_fee = self.success_fee_spin.value()
            usd_rate = self.usd_rate_spin.value()
            eur_rate = self.eur_rate_spin.value()
            
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

            # Get registered devices
            device_ids = ','.join(d['Device ID'] for d in invoice_data)
            registered_devices = get_registered_devices(device_ids)
            
            # Calculate invoice amounts
            calculations = InvoiceCalculator.calculate_invoice_amounts(
                invoice_data,
                registered_devices,
                unit_price,
                success_fee,
                usd_rate,
                eur_rate
            )
                
            logger.info(f"Retrieved invoice data for {len(invoice_data)} devices")
            self.display_invoice_data(invoice_data, calculations)
            
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate invoice: {str(e)}"
            )

    def display_invoice_data(self, invoice_data, calculations):
        """Display invoice calculations in the preview"""
        if not invoice_data:
            return
            
        # Format the preview text
        preview_text = []
        preview_text.append("<h3>Invoice Calculations</h3>")
        
        # Device Information
        preview_text.append("<p><b>Device Information:</b></p>")
        preview_text.append(f"Total Devices: {calculations['total_devices']}")
        preview_text.append(f"Total Capacity: {calculations['capacity']:.2f} MW")
        preview_text.append(f"Total Issued: {calculations['total_issued']:.4f}")
        preview_text.append("<br>")
        
        # Fees Calculation
        preview_text.append("<p><b>Fees:</b></p>")
        preview_text.append(f"Registration Fee (EUR): {calculations['registration_fee']:.2f}")
        preview_text.append(f"Registration Fee (INR): {calculations['reg_fee_inr']:.4f}")
        preview_text.append(f"Issuance Fee (EUR): {calculations['issuance_fee']:.4f}")
        preview_text.append(f"Issuance Fee (INR): {calculations['issuance_fee_inr']:.4f}")
        preview_text.append("<br>")
        
        # Revenue Calculation
        preview_text.append("<p><b>Revenue Calculation:</b></p>")
        preview_text.append(f"Gross Amount (INR): {calculations['gross_amount']:.4f}")
        preview_text.append(f"Net Revenue (INR): {calculations['net_revenue']:.4f}")
        preview_text.append(f"Success Fee (INR): {calculations['success_fee']:.4f}")
        preview_text.append(f"Final Revenue (INR): {calculations['final_revenue']:.4f}")
        preview_text.append("<br>")
        
        # Final Rate
        preview_text.append("<p><b>Final Rate:</b></p>")
        preview_text.append(f"Net Rate: {calculations['net_rate']:.4f}")
        
        # Device Details
        preview_text.append("<br><p><b>Device Details:</b></p>")
        for device in invoice_data:
            preview_text.append(
                f"Device ID: {device['Device ID']}<br>"
                f"Project: {device['Project']}<br>"
                f"Capacity: {device['Capacity']:.2f} MW<br>"
                f"Total Issued: {device['TotalIssued']:.4f}<br>"
                "-------------------"
            )
        
        # Join all text with line breaks and set to preview
        self.preview_text.setHtml("<br>".join(preview_text)) 