class InvoiceCalculator:
    @staticmethod
    def calculate_registration_fee(capacity):
        """Calculate registration fee based on capacity"""
        if capacity >= 3:
            return 1000
        elif capacity > 1:
            return 500
        else:  # capacity <= 1
            return 100

    @staticmethod
    def calculate_invoice_amounts(invoice_data, registered_devices, unit_sale_price, 
                                success_fee_percent, usd_rate, eur_rate, remove_fees=False):
        """Calculate all invoice amounts"""
        # Split registered and unregistered devices
        registered = set(registered_devices.split(',')) if registered_devices else set()
        
        total_capacity = 0
        total_issued = 0
        registration_fee = 0
        
        # Process each device
        for device in invoice_data:
            device_id = device['Device ID']
            capacity = float(device['Capacity'])
            issued = float(device['TotalIssued'])
            
            total_capacity += capacity
            total_issued += issued
            
            # Calculate registration fee only for unregistered devices and if fees are not removed
            if not remove_fees and device_id not in registered:
                registration_fee += InvoiceCalculator.calculate_registration_fee(capacity)
        
        # Calculate all amounts
        issuance_fee = 0.025 * total_issued if not remove_fees else 0
        gross_amount = total_issued * unit_sale_price * usd_rate
        reg_fee_inr = registration_fee * eur_rate if not remove_fees else 0
        issuance_fee_inr = issuance_fee * eur_rate if not remove_fees else 0
        net_revenue = gross_amount - (reg_fee_inr + issuance_fee_inr)
        success_fee = (success_fee_percent / 100) * net_revenue if not remove_fees else 0
        final_revenue = net_revenue - success_fee
        net_rate = final_revenue / total_issued if total_issued > 0 else 0
        
        return {
            'capacity': round(total_capacity, 2),
            'total_devices': len(invoice_data),
            'total_issued': round(total_issued, 4),
            'registration_fee': round(registration_fee, 2),
            'issuance_fee': round(issuance_fee, 4),
            'gross_amount': round(gross_amount, 4),
            'reg_fee_inr': round(reg_fee_inr, 4),
            'issuance_fee_inr': round(issuance_fee_inr, 4),
            'net_revenue': round(net_revenue, 4),
            'success_fee': round(success_fee, 4),
            'final_revenue': round(final_revenue, 4),
            'net_rate': round(net_rate, 4)
        } 