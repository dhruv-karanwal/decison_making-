import re

def extract_entities(text: str) -> dict:
    entities = {}

    # 1. Invoice / Job Card ID
    entities["Invoice/JobCard ID"] = re.findall(
        r"(?:Invoice\s*No[:\-]?\s*|Job\s*Card\s*ID[:\-]?\s*)([A-Za-z0-9\-\/]+)",
        text, flags=re.IGNORECASE
    )

    # 2. Dates
    date_patterns = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}",
    ]
    entities["Date"] = []
    for pat in date_patterns:
        entities["Date"].extend(re.findall(pat, text))

    # 3. Amounts
    entities["Amount"] = re.findall(r"(?:₹|Rs\.?|INR)\s?[\d,]+\.?\d*", text)

    # 4. Email
    entities["Email"] = re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", text
    )

    # 5. Phone numbers
    entities["Phone"] = re.findall(r"(?:\+91[\-\s]?)?\d{10}", text)

    # 6. GST numbers
    entities["GST/Tax"] = re.findall(
        r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b", text
    )

    # 7. Fitness certificate status
    entities["Fitness Certificate Status"] = re.findall(
        r"\b(Valid|Expired|Pending)\b", text, flags=re.IGNORECASE
    )

    # 8. Job card status
    entities["Job Card Status"] = re.findall(
        r"\b(Completed|Pending|In Progress)\b", text, flags=re.IGNORECASE
    )

    # 9. Vendor/Contractor
    entities["Vendor"] = re.findall(
        r"(?:vendor|contractor|company|provider)[:,]?\s*([A-Z][\w\s&.,-]+)",
        text, flags=re.IGNORECASE
    )

    # 10. Train / Coach
    entities["Train/Coach Number"] = re.findall(
        r"(?:Train|Coach)[:\-]?\s*([A-Za-z0-9\-]+)", text
    )

    # 11. Expiry dates
    entities["Expiry Dates"] = re.findall(
        r"(?:Expiry|Valid Till|Expires)[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})",
        text, flags=re.IGNORECASE
    )

    return entities
