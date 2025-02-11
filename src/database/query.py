# src/database/query.py
from sqlalchemy import text
from .db_connection import get_db

def get_all_sellers_data():
    with next(get_db()) as db:
        query = text("""
            SELECT `group`, seller, success_fee, indicative_price, gst, pan, address
            FROM sellers
            ORDER BY `group`, seller
        """)
        result = db.execute(query)

        sellers_data = {}
        for row in result:
            group = row[0]
            seller_info = {
                "seller": row[1],
                "success_fee": row[2],
                "indicative_price": row[3],
                "gst": row[4],
                "pan": row[5],
                "address": row[6]
            }

            if group not in sellers_data:
                sellers_data[group] = []
            sellers_data[group].append(seller_info)

        return sellers_data

def get_devices_by_pan(pan):
    """Get distinct device IDs from inventory2 table for a given PAN number"""
    with next(get_db()) as db:
        query = text("""
            SELECT DISTINCT `Device ID`
            FROM inventory2
            WHERE PAN = :pan
            ORDER BY `Device ID`
        """)
        result = db.execute(query, {"pan": pan})
        return [row[0] for row in result]

def get_months_between(from_month, to_month):
    """Get list of months between two months inclusive"""
    months = ["january", "february", "march", "april", "may", "june",
             "july", "august", "september", "october", "november", "december"]
    # Convert input months to lowercase for comparison
    from_month = from_month.lower()
    to_month = to_month.lower()
    start_idx = months.index(from_month)
    end_idx = months.index(to_month)
    return months[start_idx:end_idx + 1]

def get_invoice_data(device_ids, year, period_from, period_to):
    """Get invoice data for selected devices and period"""
    months = get_months_between(period_from, period_to)

    print("device_ids", device_ids)
    print("year", year)
    print("period_from", period_from)
    print("period_to", period_to)
    
    # Generate dynamic SQL for each month's issued sum
    month_sums = []
    for month in months:
        month_sums.append(f"SUM(CASE WHEN LOWER(Month) = '{month}' THEN Issued ELSE 0 END) AS `{month}Issued`")
    month_sums_sql = ", ".join(month_sums)
    
    # Convert months to tuple for IN clause
    months_tuple = tuple(months)
    
    with next(get_db()) as db:
        query = text(f"""
            SELECT 
                `Device ID`,
                `Project`,
                MIN(`Capacity (MW)`) AS Capacity,
                SUM(Issued) AS TotalIssued,
                {month_sums_sql}
            FROM inventory2
            WHERE 
                `Device ID` IN :device_ids AND 
                Year = :year AND 
                LOWER(Month) IN :months AND
                Issued = Actual_used AND
                invoice_status = 'False'
            GROUP BY `Device ID`, `Project`
        """)
        
        # Prepare parameters
        params = {
            "device_ids": tuple(device_ids),
            "year": year,
            "months": months_tuple
        }
            
        result = db.execute(query, params)
        
        # Convert result to list of dictionaries
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]

def get_registered_devices(device_ids):
    """Get list of registered device IDs from invoicereg table"""
    with next(get_db()) as db:
        # Convert comma-separated string to list if needed
        if isinstance(device_ids, str):
            device_ids = device_ids.split(',')
            
        query = text("""
            SELECT `Device ID`
            FROM invoicereg
            WHERE `Device ID` IN :device_ids
        """)
        
        result = db.execute(query, {"device_ids": tuple(device_ids)})
        return ','.join(row[0] for row in result)