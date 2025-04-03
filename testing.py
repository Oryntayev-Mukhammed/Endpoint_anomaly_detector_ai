import json
import uuid
from datetime import datetime
import numpy as np

def generate_ideal_output(input_data):
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
    ugd_name = payload["ugd"]["name"] if "ugd" in payload else None
    ugd_bin = payload["ugd"]["bin"] if "ugd" in payload else None
    ugd_code = payload["ugd"]["code"] if "ugd" in payload else None
    
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
        "createdDate": input_data["timestamp"][:19],  # Обрезаем миллисекунды
        "modifiedDate": input_data["timestamp"],
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


def input_to_feature_vector(input_data):
    """
    Преобразует входные данные платежа в одномерный числовой вектор фичей.
    Обрабатывает отсутствующие поля, категориальные данные и нормализует значения.
    """
    payload = input_data["payload"]
    features = []

    # 1. Числовые признаки
    features.append(float(payload.get("amount", 0)))  # 0
    
    # 2. KBK код (если есть)
    kbk_code = float(payload["kbk"]["code"]) if "kbk" in payload and "code" in payload["kbk"] else 0.0
    features.append(kbk_code)  # 1

    # 3. KNP (преобразуем строку в число если возможно)
    knp = payload.get("knp", "0")
    features.append(float(knp) if knp.isdigit() else hash(knp) % 10000)  # 2

    # 4. Год (нормализованный)
    year = float(payload.get("year", 2025))
    features.append((year - 2000) / 50)  # 3 (нормализация 2000-2050 -> 0.0-1.0)

    # 5. Квартал (one-hot encoding)
    quarter_map = {"FIRST": 0, "SECOND": 1, "THIRD": 2, "FOURTH": 3}
    quarter = quarter_map.get(payload.get("quarter", ""), -1)
    quarter_features = [0.0] * 4
    if quarter >= 0:
        quarter_features[quarter] = 1.0
    features.extend(quarter_features)  # 4-7

    # 6. Тип операции (one-hot)
    operation_types = ["INDIVIDUAL_ENTREPRENEUR", "CORPORATE", "EMPLOYEE"]
    op_type = payload.get("taxesPaymentOperationType", "")
    op_features = [1.0 if op_type == t else 0.0 for t in operation_types]
    features.extend(op_features)  # 8-10

    # 7. Флаги из KBK
    kbk_flags = [
        float(payload["kbk"].get("employeeLoadingRequired", False)) if "kbk" in payload else 0.0,
        float(payload["kbk"].get("ugdLoadingRequired", False)) if "kbk" in payload else 0.0
    ]
    features.extend(kbk_flags)  # 11-12

    # 8. Наличие UGD (бинарный признак)
    features.append(1.0 if "ugd" in payload else 0.0)  # 13

    # 9. Хэш IBAN (первые 6 цифр)
    iban = payload.get("ibanDebit", "")
    iban_hash = float(iban[:6]) if iban[:6].isdigit() else hash(iban) % 10000
    features.append(iban_hash / 10000)  # 14 (нормализовано)

    # 10. Длина purpose (нормализованная)
    purpose_len = len(payload.get("purpose", "")) / 100  # предполагаем макс 100 символов
    features.append(purpose_len)  # 15

    # Преобразуем в numpy array и нормализуем
    feature_vector = np.array(features, dtype=np.float32)
    
    return feature_vector

# Пример использования (без UGD и quarter/year):
input_example = {
    "timestamp": "2025-04-03T19:38:21.798734",
    "payload": {
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

ideal_output = generate_ideal_output(input_example)
print(len(input_to_feature_vector(input_example)), len(input_example['payload']))
print(json.dumps(ideal_output, indent=2, ensure_ascii=False))