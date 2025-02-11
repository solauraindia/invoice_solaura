def convert_to_words(amount):
    crore = 10000000
    lakh = 100000
    thousand = 1000
    hundred = 100

    units = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN", 
             "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]

    def convert_number_to_words(num):
        if num < 20:
            return units[num]
        if num < 100:
            return tens[num // 10] + (" " + units[num % 10] if num % 10 != 0 else "")
        if num < thousand:
            return units[num // hundred] + " HUNDRED" + (" AND " + convert_number_to_words(num % hundred) if num % hundred != 0 else "")
        if num < lakh:
            return convert_number_to_words(num // thousand) + " THOUSAND" + (" " + convert_number_to_words(num % thousand) if num % thousand != 0 else "")
        if num < crore:
            return convert_number_to_words(num // lakh) + " LAKH" + (" " + convert_number_to_words(num % lakh) if num % lakh != 0 else "")
        return convert_number_to_words(num // crore) + " CRORE" + (" " + convert_number_to_words(num % crore) if num % crore != 0 else "")

    # Format the amount to ensure 2 decimal places
    amount_str = "{:.2f}".format(float(amount))
    rupees, paise = amount_str.split('.')
    
    result = convert_number_to_words(int(rupees))
    result += " RUPEES"

    paise_val = int(paise)
    if paise_val > 0:
        result += " AND " + convert_number_to_words(paise_val) + " PAISE"

    return result + " ONLY" 