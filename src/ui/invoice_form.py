from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QPushButton, QFrame, QCheckBox, QScrollArea, QGroupBox,
                             QMessageBox, QTextBrowser)
from PyQt5.QtCore import Qt
from ..database.query import (get_all_sellers_data, get_devices_by_pan, 
                           get_invoice_data, get_registered_devices)
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
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout()
        
        # Generate Button
        self.generate_btn = QPushButton('Generate Invoice')
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
                
            # Create Invoice directory if it doesn't exist
            invoice_dir = os.path.join(os.getcwd(), "Invoice")
            if not os.path.exists(invoice_dir):
                os.makedirs(invoice_dir)
                
            # Save file in Invoice directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoice_worksheet_{timestamp}.pdf"
            filepath = os.path.join(invoice_dir, filename)
            
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

            # Get company details from the current selection
            group_name = self.group_name_combo.currentText()
            company_name = self.company_name_combo.currentText()
            
            # Get seller details directly from sellers_data
            seller_info = next(
                seller for seller in self.sellers_data[group_name] 
                if seller["seller"] == company_name
            )
            
            # Get all unique projects from invoice data
            projects = list(set(device['Project'] for device in self.current_invoice_data))
            project_text = ' and '.join(projects)
            
            # Get selected year
            selected_year = self.year_combo.currentText()
            
            # Prepare data for Excel generation
            excel_data = {
                'company_name': company_name,
                'pan': seller_info['pan'],
                'gst': seller_info['gst'],
                'address': seller_info['address'],
                'period_from': self.period_from_combo.currentText(),
                'period_to': self.period_to_combo.currentText(),
                'project': project_text,
                'year': selected_year
            }

            # Create Invoice directory if it doesn't exist
            invoice_dir = os.path.join(os.getcwd(), "Invoice")
            if not os.path.exists(invoice_dir):
                os.makedirs(invoice_dir)

            # Initialize Excel generator with template
            template_path = os.path.join(os.getcwd(), "src", "public", "template.xlsx")
            excel_generator = ExcelInvoiceGenerator(template_path)

            # Generate Excel invoice
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(invoice_dir, f"invoice_{timestamp}.xlsx")
            
            excel_generator.generate_invoice(excel_data, self.current_calculations)
            excel_generator.save(output_path)

            QMessageBox.information(
                self,
                "Success",
                f"Excel invoice saved to: {output_path}"
            )

        except Exception as e:
            logger.error(f"Error generating Excel invoice: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate Excel invoice: {str(e)}"
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
        
        # Join all text with line breaks and set to preview
        self.preview_text.setHtml("\n".join(preview_text)) 