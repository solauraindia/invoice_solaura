from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QPushButton, QFrame, QCheckBox, QScrollArea, QGroupBox,
                             QMessageBox, QTextBrowser, QSizePolicy)
from PyQt5.QtCore import Qt
from ..database.query import (get_all_sellers_data, get_devices_by_pan, 
                           get_invoice_data, get_registered_devices,
                           insert_invoice_data, register_devices)
from ..calculations.invoice_calculator import InvoiceCalculator
from ..utils.excel_handler import ExcelInvoiceGenerator
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
from datetime import datetime
from nanoid import generate

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
        
        # Add Remove Fees checkbox
        self.remove_fees_checkbox = QCheckBox('Remove Fees')
        form_layout.addRow('', self.remove_fees_checkbox)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout()
        
        # Generate Button
        self.generate_btn = QPushButton('Generate Calculations')
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        button_layout.addWidget(self.generate_btn)
        
        # Download Worksheet Button
        self.download_btn = QPushButton('Download Worksheet')
        self.download_btn.clicked.connect(self.on_download_clicked)
        self.download_btn.setEnabled(False)
        button_layout.addWidget(self.download_btn)
        
        # Confirm and Download Button
        self.confirm_download_btn = QPushButton('Confirm and Download')
        self.confirm_download_btn.clicked.connect(self.on_confirm_download_clicked)
        self.confirm_download_btn.setEnabled(False)
        button_layout.addWidget(self.confirm_download_btn)
        
        button_container.setLayout(button_layout)
        form_layout.addRow('', button_container)
        
        form_container.setLayout(form_layout)
        
        # Preview layout (right side)
        preview_container = QWidget()
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        preview_label = QLabel('Worksheet Calculations')
        preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        # Create text browser for preview with expanded width
        self.preview_text = QTextBrowser()
        self.preview_text.setMinimumWidth(500)  # Increased minimum width
        self.preview_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow expanding
        self.preview_text.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                padding: 0px;
                margin: 0px;
                border: none;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        preview_container.setLayout(preview_layout)
        
        # Add both containers to main layout with stretch factor
        main_layout.addWidget(form_container, 1)  # 1 part
        main_layout.addWidget(preview_container, 1)  # 1 part
        
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
            
            # Get seller info for the selected company
            seller_info = next(
                seller for seller in self.sellers_data[group_name] 
                if seller["seller"] == company_name
            )
            
            # Get PAN number from seller info
            pan = seller_info["pan"]
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
            success_fee = 0 if self.remove_fees_checkbox.isChecked() else self.success_fee_spin.value()
            usd_rate = self.usd_rate_spin.value()
            eur_rate = self.eur_rate_spin.value()
            remove_fees = self.remove_fees_checkbox.isChecked()
            
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
                eur_rate,
                remove_fees
            )
                
            # Enable both download buttons after successful generation
            self.download_btn.setEnabled(True)
            self.confirm_download_btn.setEnabled(True)
            
            logger.info(f"Retrieved invoice data for {len(invoice_data)} devices")
            self.display_invoice_data(invoice_data, calculations)
            
            # Store data for PDF and Excel generation
            self.current_invoice_data = invoice_data
            self.current_calculations = calculations
            
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate invoice: {str(e)}"
            )

    def on_download_clicked(self):
        """Handle download worksheet button click"""
        try:
            if not hasattr(self, 'current_invoice_data') or not hasattr(self, 'current_calculations'):
                QMessageBox.warning(self, "Warning", "Please generate invoice data first.")
                return
                
            # Get company and group names for directory
            company_name = self.company_name_combo.currentText()
            group_name = self.group_name_combo.currentText()
            year = self.year_combo.currentText()
            
            # Create directory structure for Worksheet
            worksheet_base_dir = os.path.join(os.getcwd(), "Worksheet", group_name, company_name, year)
            if not os.path.exists(worksheet_base_dir):
                os.makedirs(worksheet_base_dir)
                
            # Save file in company-specific directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoice_worksheet_{timestamp}.pdf"
            filepath = os.path.join(worksheet_base_dir, filename)
            
            self.generate_worksheet_pdf(filepath)
            
            QMessageBox.information(
                self,
                "Success",
                f"Worksheet saved to: {filepath}"
            )
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate PDF: {str(e)}"
            )

    def on_confirm_download_clicked(self):
        """Handle confirm and download button click"""
        try:
            if not hasattr(self, 'current_invoice_data') or not hasattr(self, 'current_calculations'):
                QMessageBox.warning(self, "Warning", "Please generate invoice data first.")
                return

            # Get company and group names for directory
            group_name = self.group_name_combo.currentText()
            company_name = self.company_name_combo.currentText()
            selected_year = self.year_combo.currentText()
            
            # Create directory structure for Invoices
            invoice_base_dir = os.path.join(os.getcwd(), "Invoices", group_name, company_name, selected_year)
            if not os.path.exists(invoice_base_dir):
                os.makedirs(invoice_base_dir)

            # Get seller details directly from sellers_data
            seller_info = next(
                seller for seller in self.sellers_data[group_name] 
                if seller["seller"] == company_name
            )
            
            # Get all unique projects from invoice data
            projects = list(set(device['Project'] for device in self.current_invoice_data))
            project_text = ' and '.join(projects)
            
            # Get selected year and device IDs
            selected_year = self.year_combo.currentText()
            device_ids = [device['Device ID'] for device in self.current_invoice_data]
            device_ids_str = ','.join(device_ids)
            
            # Get registered devices and find unregistered ones
            registered_devices = get_registered_devices(device_ids).split(',') if get_registered_devices(device_ids) else []
            unregistered_devices = [d for d in device_ids if d not in registered_devices]
            unregistered_devices_str = ','.join(unregistered_devices)
            
            # Format dates
            period_from = self.period_from_combo.currentText()
            period_to = self.period_to_combo.currentText()
            current_date = datetime.now().strftime("%d-%m-%Y")
            
            # Generate invoice ID using nanoid
            invoice_id = generate(size=21)  # Default nanoid length
            
            # Prepare invoice data for database
            invoice_data = {
                'invoiceid': invoice_id,
                'groupName': group_name,
                'capacity': self.current_calculations['capacity'],
                'regNo': len(device_ids),  # Total number of devices
                'regdevice': unregistered_devices_str,  # Only unregistered devices
                'issued': self.current_calculations['total_issued'],
                'ISP': self.unit_price_spin.value(),
                'registrationFee': self.current_calculations['registration_fee'],
                'issuanceFee': self.current_calculations['issuance_fee'],
                'USDExchange': self.usd_rate_spin.value(),
                'EURExchange': self.eur_rate_spin.value(),
                'invoicePeriodFrom': f"01-{datetime.strptime(period_from, '%B').strftime('%m')}-{selected_year}",
                'invoicePeriodTo': f"31-{datetime.strptime(period_to, '%B').strftime('%m')}-{selected_year}",
                'gross': self.current_calculations['gross_amount'],
                'regFeeINR': self.current_calculations['reg_fee_inr'],
                'issuanceINR': self.current_calculations['issuance_fee_inr'],
                'netRevenue': self.current_calculations['net_revenue'],
                'successFee': self.current_calculations['success_fee'],
                'finalRevenue': self.current_calculations['final_revenue'],
                'project': project_text,
                'netRate': self.current_calculations['net_rate'],
                'pan': seller_info['pan'],
                'gst': seller_info['gst'],
                'address': seller_info['address'],
                'date': current_date,
                'deviceIds': device_ids_str,
                'companyName': company_name
            }
            
            try:
                # Insert invoice data
                insert_invoice_data(invoice_data)
                
                # Register devices
                register_devices(device_ids)
                
                logger.info("Successfully inserted invoice data and registered devices")
            except Exception as e:
                logger.error(f"Database operation failed: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to save invoice data to database. Please try again."
                )
                return
            
            # Prepare data for Excel generation
            excel_data = {
                'company_name': company_name,
                'pan': seller_info['pan'],
                'gst': seller_info['gst'],
                'address': seller_info['address'],
                'period_from': period_from,
                'period_to': period_to,
                'project': project_text,
                'year': selected_year
            }

            # Initialize Excel generator with template
            template_path = os.path.join(os.getcwd(), "src", "public", "template.xlsx")
            excel_generator = ExcelInvoiceGenerator(template_path)

            # Generate Excel invoice
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(invoice_base_dir, f"invoice_{timestamp}.xlsx")
            
            excel_generator.generate_invoice(excel_data, self.current_calculations)
            excel_generator.save(output_path)

            QMessageBox.information(
                self,
                "Success",
                f"Invoice data saved and Excel file generated at: {output_path}"
            )

        except Exception as e:
            logger.error(f"Error in confirm and download: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to process invoice: {str(e)}"
            )

    def generate_worksheet_pdf(self, filepath):
        """Generate PDF worksheet"""
        doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=15, rightMargin=15)  # Reduced margins
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        elements.append(Paragraph("Invoice Worksheet", title_style))
        
        # Device Information
        elements.append(Paragraph("Device Information", styles['Heading2']))
        device_data = [
            ["Total Devices", str(self.current_calculations['total_devices'])],
            ["Total Capacity (MW)", f"{self.current_calculations['capacity']:.2f}"],
            ["Total Issued", f"{self.current_calculations['total_issued']:.4f}"]
        ]
        device_table = Table(device_data, colWidths=[3*inch, 3*inch])
        device_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(device_table)
        elements.append(Spacer(1, 20))
        
        # Fees
        elements.append(Paragraph("Fees", styles['Heading2']))
        fees_data = [
            ["Registration Fee (EUR)", f"{self.current_calculations['registration_fee']:.2f}"],
            ["Registration Fee (INR)", f"{self.current_calculations['reg_fee_inr']:.4f}"],
            ["Issuance Fee (EUR)", f"{self.current_calculations['issuance_fee']:.4f}"],
            ["Issuance Fee (INR)", f"{self.current_calculations['issuance_fee_inr']:.4f}"]
        ]
        fees_table = Table(fees_data, colWidths=[3*inch, 3*inch])
        fees_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(fees_table)
        elements.append(Spacer(1, 20))
        
        # Revenue Calculations
        elements.append(Paragraph("Revenue Calculations", styles['Heading2']))
        revenue_data = [
            ["Gross Amount (INR)", f"{self.current_calculations['gross_amount']:.4f}"],
            ["Net Revenue (INR)", f"{self.current_calculations['net_revenue']:.4f}"],
            ["Success Fee (INR)", f"{self.current_calculations['success_fee']:.4f}"],
            ["Final Revenue (INR)", f"{self.current_calculations['final_revenue']:.4f}"],
            ["Net Rate", f"{self.current_calculations['net_rate']:.4f}"]
        ]
        revenue_table = Table(revenue_data, colWidths=[3*inch, 3*inch])
        revenue_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(revenue_table)
        elements.append(Spacer(1, 20))
        
        # Device Details with Monthly Issuance
        elements.append(Paragraph("Device Details", styles['Heading2']))
        
        # Get all months from the first device's data
        months = []
        if self.current_invoice_data:
            for key in self.current_invoice_data[0].keys():
                if key.endswith('Issued') and key != 'TotalIssued':
                    month = key.replace('Issued', '')
                    # Use 3-letter month abbreviations
                    month = month[:3]
                    months.append(month)
        months.sort()  # Sort months alphabetically
        
        # Create headers for the table
        headers = ["Device ID"] + months + ["Tot"]
        device_details = [headers]
        
        # Add data for each device
        for device in self.current_invoice_data:
            row = [device['Device ID']]
            for month in months:
                # Find the full month name in the original data
                full_month = next(k.replace('Issued', '') for k in device.keys() 
                                if k.endswith('Issued') and k.startswith(month))
                month_key = f"{full_month}Issued"
                value = device.get(month_key, 0)
                row.append(f"{float(value):.2f}" if value else "0.00")  # Reduced decimal places
            row.append(f"{float(device['TotalIssued']):.2f}")  # Reduced decimal places
            device_details.append(row)
            
        # Calculate column widths based on number of columns
        total_width = 7.8  # Total width in inches (increased slightly)
        device_id_width = 1.3  # Slightly reduced Device ID column
        remaining_width = total_width - device_id_width
        month_width = remaining_width / (len(months) + 1)  # +1 for Total column
        col_widths = [device_id_width] + [month_width] * (len(months) + 1)
        
        details_table = Table(device_details, colWidths=[w*inch for w in col_widths])
        details_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Thinner grid lines
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 1),  # Minimal padding
            ('FONTSIZE', (0, 0), (-1, -1), 5),  # Even smaller font size
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Right align numeric columns
            ('TOPPADDING', (0, 0), (-1, -1), 0),  # No top padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # No bottom padding
            ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Minimal left padding
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Minimal right padding
        ]))
        elements.append(details_table)
        
        # Build PDF
        doc.build(elements)

    def display_invoice_data(self, invoice_data, calculations):
        """Display invoice calculations in the preview"""
        if not invoice_data:
            return
            
        # Format the preview text with a single HTML table
        preview_text = []
        preview_text.append("""
        <style>
            body {
                margin: 0;
                padding: 0;
            }
            .main-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
                padding: 0 20px;
            }
            .table-container {
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 0 auto;
                background-color: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            th, td {
                padding: 12px 15px;
                border: 1px solid #ddd;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            th {
                background-color: #f5f5f5;
                font-weight: bold;
                text-align: center;
                padding: 15px;
                font-size: 14px;
                text-transform: uppercase;
            }
            td:first-child {
                width: 60%;
                text-align: left;
                padding-left: 20px;
                font-size: 13px;
            }
            td:last-child {
                width: 40%;
                text-align: right;
                padding-right: 20px;
                font-size: 13px;
            }
            h3 {
                text-align: center;
                margin: 5px 0 15px 0;
                padding: 0;
                width: 100%;
                font-size: 16px;
            }
            tr:hover {
                background-color: #f9f9f9;
            }
        </style>
        <div class="main-container">
            <h3>Worksheet Calculations</h3>
            <div class="table-container">
        """)
        
        # Single comprehensive table
        preview_text.append("""
                <table>
                    <tr>
                        <th colspan='2'>Device Information</th>
                    </tr>
                    <tr>
                        <td>Total Devices</td>
                        <td>{}</td>
                    </tr>
                    <tr>
                        <td>Total Capacity</td>
                        <td>{:.2f} MW</td>
                    </tr>
                    <tr>
                        <td>Total Issued</td>
                        <td>{:.4f}</td>
                    </tr>
                    
                    <tr>
                        <th colspan='2'>Fees</th>
                    </tr>
                    <tr>
                        <td>Registration Fee (EUR)</td>
                        <td>{:.2f}</td>
                    </tr>
                    <tr>
                        <td>Registration Fee (INR)</td>
                        <td>{:.4f}</td>
                    </tr>
                    <tr>
                        <td>Issuance Fee (EUR)</td>
                        <td>{:.4f}</td>
                    </tr>
                    <tr>
                        <td>Issuance Fee (INR)</td>
                        <td>{:.4f}</td>
                    </tr>
                    
                    <tr>
                        <th colspan='2'>Revenue Calculation</th>
                    </tr>
                    <tr>
                        <td>Gross Amount (INR)</td>
                        <td>{:.4f}</td>
                    </tr>
                    <tr>
                        <td>Net Revenue (INR)</td>
                        <td>{:.4f}</td>
                    </tr>
                    <tr>
                        <td>Success Fee (INR)</td>
                        <td>{:.4f}</td>
                    </tr>
                    <tr>
                        <td>Final Revenue (INR)</td>
                        <td>{:.4f}</td>
                    </tr>
                    
                    <tr>
                        <th colspan='2'>Final Rate</th>
                    </tr>
                    <tr>
                        <td>Net Rate</td>
                        <td>{:.4f}</td>
                    </tr>
                </table>
            </div>
        </div>
        """.format(
            calculations['total_devices'],
            calculations['capacity'],
            calculations['total_issued'],
            calculations['registration_fee'],
            calculations['reg_fee_inr'],
            calculations['issuance_fee'],
            calculations['issuance_fee_inr'],
            calculations['gross_amount'],
            calculations['net_revenue'],
            calculations['success_fee'],
            calculations['final_revenue'],
            calculations['net_rate']
        ))
        
        # Set the HTML content
        self.preview_text.setHtml("\n".join(preview_text)) 