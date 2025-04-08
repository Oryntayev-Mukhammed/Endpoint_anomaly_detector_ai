import json
import uuid
from datetime import datetime
import numpy as np

def generate_ideal_output(input_data: dict, is_payload=False):
    if is_payload:
        payload = input_data
    else:
        payload = input_data["payload"]
    
    # Определяем transactionType на основе taxesPaymentOperationType (если есть)
    transaction_type = "EMPLTAX"  # значение по умолчанию
    if "taxesPaymentOperationType" in payload:
        if payload["taxesPaymentOperationType"] == "INDIVIDUAL_ENTREPRENEUR":
            transaction_type = "INDTAX"
        elif payload["taxesPaymentOperationType"] == "CORPORATE":
            transaction_type = "CORPTAX"
    
    # Обработка дат (если нет quarter и year, но есть period)
    payment_year = payload.get("year", None)
    payment_quarter = get_quarter_number(payload.get("quarter", None)) if "quarter" in payload else None
    period = None
    
    if "period" in payload:
        period = payload["period"]
    elif payment_year and payment_quarter:
        period = f"{payment_year}-{get_quarter_end(payload['quarter'])}"
    
    # Обработка UGD (если нет, то ставим None или дефолтные значения)
    ugd_data = payload.get("ugd")
    if ugd_data:
        ugd_name = ugd_data["name"]
        ugd_bin = ugd_data["bin"]
        ugd_code = ugd_data["code"]
    else:
        ugd_name = None
        ugd_bin = None
        ugd_code = None
    
    # Обработка KBK (если нет, то ставим пустые строки)
    kbk_name = f"{payload['kbk']['name']}" if "kbk" in payload else ""
    kbk_code = str(payload["kbk"]["code"]) if "kbk" in payload else ""
    
    # Формируем KNP (если нет purpose, то только код)
    knp_full = f"{payload['knp']}-{payload['purpose']}" if "purpose" in payload else payload["knp"]
    
    # IBAN кредита (если нет UGD, можно взять из KBK или поставить дефолтный)
    iban_credit = "KZ24070105KSN0000000"  # дефолтный
    
    output = {
        "transactionType": transaction_type,
        "id": str(uuid.uuid4()),
        "transactionId": payload["transactionId"],
        "createdDate": payload["timestamp"][:19],  # Обрезаем миллисекунды
        "modifiedDate": payload["timestamp"],
        "status": "COMPLETED",
        "amount": payload["amount"],
        "anotherAmount": None,
        "currency": "KZT",
        "anotherCurrency": None,
        "commission": 150,  # Фиксированная комиссия или можно вычислять
        "counterparty": ugd_name,
        "purpose": payload.get("purpose", ""),
        "ibanDebit": payload["ibanDebit"],
        "ibanCredit": iban_credit,
        "creditIdentifier": ugd_code,
        "exchangeDirection": None,
        "factSenderName": None,
        "factSenderIin": None,
        "errorMessage": None,
        "knp": knp_full,
        "ugdBin": ugd_bin,
        "kbkName": kbk_name,
        "kbkCode": kbk_code,
        "knpCode": payload["knp"],
        "paymentHalfYear": None,
        "paymentYear": payment_year,
        "period": period,
        "paymentQuarter": payment_quarter,
        "employees": [],
        "debit": True
    }
    return output

def get_quarter_number(quarter_str):
    if not quarter_str:
        return None
    quarters = {
        "FIRST": 1,
        "SECOND": 2,
        "THIRD": 3,
        "FOURTH": 4
    }
    return quarters.get(quarter_str, None)

def get_quarter_end(quarter_str):
    if not quarter_str:
        return None
    if quarter_str == "FIRST":
        return "03-31"
    elif quarter_str == "SECOND":
        return "06-30"
    elif quarter_str == "THIRD":
        return "09-30"
    elif quarter_str == "FOURTH":
        return "12-31"
    return None
    
# Пример использования (без UGD и quarter/year):
input_example = {
    "timestamp": "2025-04-03T19:38:21.798734",
    "payload": {
      "timestamp": "2025-04-03T19:38:21.798734",
      "transactionId": "APP_INDNTRTAX_49bdda3a-0162-415f-b93e-518bacc68c25",
      "ibanDebit": "KZ92886A220120705719",
      "amount": 5740.25,
      "kbk": {
        "name": "Доля РК по разделу прод. по закл. ктр., за иск. поступ. от орг. нефт. сектора",
        "code": 105308,
        "employeeLoadingRequired": False,
        "ugdLoadingRequired": True
      },
      "knp": "911",
      "purpose": "Основное_9498",
      "taxesPaymentOperationType": "INDIVIDUAL_ENTREPRENEUR",
      "quarter": "FIRST",
      "year": 2025,
      "ugd": {
        "bin": "980840003491",
        "name": "ГУ \"Аппарат акима Кировского сельского округа Глубоковского района Восточно-Казахстанской области\"",
        "code": "180308"
      }
    }
  }

if __name__ == "__main__":
    ideal_output = generate_ideal_output(input_example)
    print(len(ideal_output))
    print(json.dumps(ideal_output, indent=2, ensure_ascii=False))