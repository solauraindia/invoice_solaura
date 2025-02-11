# src/database/query.py
from sqlalchemy import text
from .db_connection import get_db

def get_all_sellers_data():
    with next(get_db()) as db:
        query = text("""
            SELECT `group`, seller, success_fee, indicative_price
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
                "indicative_price": row[3]
            }

            if group not in sellers_data:
                sellers_data[group] = []
            sellers_data[group].append(seller_info)

        return sellers_data