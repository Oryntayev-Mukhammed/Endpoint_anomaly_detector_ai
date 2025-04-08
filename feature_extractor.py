import json
import numpy as np
from datetime import datetime
from typing import Dict, Any
from dataclasses import is_dataclass, asdict

from services.models import PaymentPayload, TransactionDetail

class PaymentFeatureExtractor:
    """Класс для преобразования PaymentPayload и TransactionDetail в feature vectors"""
    
    @staticmethod
    def payload_to_vector(payload: 'PaymentPayload'):
        """Преобразует PaymentPayload в feature vector с метаинформацией"""
        features = {}
        
        # Основные числовые признаки
        features['amount'] = payload.amount / 1_000_000
        features['kbk_code'] = payload.kbk.code / 1_000_000
        
        # Обработка KNP
        knp = payload.knp
        features['knp'] = float(knp) if knp.isdigit() else float(hash(knp) % 10000) / 10000
        
        # Временные параметры
        features['year'] = (payload.year - 2000) / 50 if payload.year else 0.0
        quarter = payload.quarter or ""
        features.update({
            'quarter_1': 1.0 if quarter == "FIRST" else 0.0,
            'quarter_2': 1.0 if quarter == "SECOND" else 0.0,
            'quarter_3': 1.0 if quarter == "THIRD" else 0.0,
            'quarter_4': 1.0 if quarter == "FOURTH" else 0.0,
            'has_period': 1.0 if payload.period else 0.0
        })
        
        # Тип операции
        op_type = payload.taxes_payment_operation_type
        features.update({
            'op_individual': 1.0 if op_type == "INDIVIDUAL_ENTREPRENEUR" else 0.0,
            'op_corporate': 1.0 if op_type == "CORPORATE" else 0.0,
            'op_employee': 1.0 if op_type == "EMPLOYEE" else 0.0
        })
        
        # Флаги KBK
        features.update({
            'kbk_employee_flag': float(payload.kbk.employee_loading_required),
            'kbk_ugd_flag': float(payload.kbk.ugd_loading_required),
            'kbk_name': float(hash(payload.kbk.name or "") % 10000) / 10000
        })
        
        # UGD признаки
        if payload.ugd:
            features.update({
                'has_ugd': 1.0,
                'ugd_code': float(payload.ugd.code or 0) / 10000,
                'ugd_bin': float(payload.ugd.bin or 0)/ 10000,
                'ugd_name': float(hash(payload.ugd.name or "") % 10000) / 10000
            })
        else:
            features.update({
                'has_ugd': 0.0,
                'ugd_code': 0.0,
                'ugd_bin': 0.0,
                'ugd_name': 0.0
            })
        
        # Текстовые признаки
        features.update({
            'purpose_len': len(payload.purpose) / 200,
            'iban_prefix': float(hash(payload.iban_debit or "") % 10000) / 10000
        })
        
        # Создаем вектор
        feature_names = [
            'amount', 'kbk_code', 'knp', 'year',
            'quarter_1', 'quarter_2', 'quarter_3', 'quarter_4', 'has_period',
            'op_individual', 'op_corporate', 'op_employee',
            'kbk_employee_flag', 'kbk_ugd_flag', 'kbk_name',
            'has_ugd', 'ugd_code', 'ugd_bin', 'ugd_name',
            'purpose_len', 'iban_prefix'
        ]
        
        vector = np.array([features[name] for name in feature_names], dtype=np.float32)
        
        return {
            'vector': vector,
            'features': features,
            'feature_names': feature_names,
            'size': len(feature_names)
        }
    
    @staticmethod
    def transaction_to_vector(transaction: 'TransactionDetail'):
        """Улучшенная векторизация TransactionDetail с обработкой всех случаев"""
        features = {}
        
        # 1. Основные числовые признаки
        features.update({
            'amount': transaction.amount / 1_000_000 if transaction.amount else 0.0,
            'another_amount': transaction.another_amount / 1_000_000 if transaction.another_amount else 0.0,
            'commission': transaction.commission / 1000 if transaction.commission else 0.0,
            'kbk_code': float(transaction.kbk_code) / 1_000_000 if transaction.kbk_code else 0.0
        })
        
        # 2. Статус и тип операции (мультикласс)
        status_types = ["COMPLETED", "FAILED", "PENDING", "REVERSED"]
        transaction_types = ["EMPLTAX", "INDNTRTAX", "CORPTAX", "INDTAX"]
        
        features.update({
            f"status_{status.lower()}": 1.0 if transaction.status == status else 0.0
            for status in status_types
        })
        
        features.update({
            f"type_{ttype.lower()}": 1.0 if transaction.transaction_type == ttype else 0.0
            for ttype in transaction_types
        })
        
        features.update({
            'is_debit': float(transaction.debit) if transaction.debit is not None else 0.5,
            'has_error': 1.0 if transaction.error_message else 0.0
        })
        
        # 3. Временные параметры
        created_hour = transaction.created_date.hour if transaction.created_date else 12
        modified_hour = transaction.modified_date.hour if transaction.modified_date else created_hour
        
        features.update({
            'payment_year': (transaction.payment_year - 2000) / 50 if transaction.payment_year else 0.0,
            'payment_quarter': transaction.payment_quarter / 4 if transaction.payment_quarter else 0.0,
            'payment_half_year': transaction.payment_half_year / 2 if transaction.payment_half_year else 0.0,
            'created_hour': created_hour / 24,
            'modified_hour': modified_hour / 24,
            'has_period': 1.0 if transaction.period else 0.0,
            'period_length': len(transaction.period) / 50 if transaction.period else 0.0
        })
        
        # 4. Валюты и направления
        features.update({
            'currency_kzt': 1.0 if transaction.currency == "KZT" else 0.0,
            'another_currency_present': 1.0 if transaction.another_currency else 0.0,
            'exchange_dir_present': 1.0 if transaction.exchange_direction else 0.0,
            'iban_credit_present': 1.0 if transaction.iban_credit else 0.0
        })
        
        # 5. UGD и идентификаторы
        features.update({
            'has_ugd': 1.0 if transaction.ugd_bin else 0.0,
            'ugd_bin_hash': float(hash(transaction.ugd_bin)) % 10000 / 10000 if transaction.ugd_bin else 0.0,
            'credit_id_hash': float(hash(transaction.credit_identifier)) % 10000 / 10000 if transaction.credit_identifier else 0.0,
            'sender_iin_present': 1.0 if transaction.fact_sender_iin else 0.0
        })
        
        # 6. Текстовые и категориальные признаки
        features.update({
            'purpose_len': len(transaction.purpose) / 200 if transaction.purpose else 0.0,
            'counterparty_len': len(transaction.counterparty) / 200 if transaction.counterparty else 0.0,
            'iban_debit_prefix': float(transaction.iban_debit[:6]) / 1_000_000 if transaction.iban_debit and transaction.iban_debit[:6].isdigit() else 0.0,
            'kbk_name_hash': float(hash(transaction.kbk_name)) % 10000 / 10000 if transaction.kbk_name else 0.0,
            'knp_code_present': 1.0 if transaction.knp_code else 0.0,
            'knp_present': 1.0 if transaction.knp else 0.0,
            'sender_name_present': 1.0 if transaction.fact_sender_name else 0.0,
            'employees_count': len(transaction.employees) / 10 if transaction.employees else 0.0
        })
        
        # Создаем вектор
        feature_names = [
            # Числовые
            'amount', 'another_amount', 'commission', 'kbk_code',
            
            # Статусы и типы
            *[f'status_{s.lower()}' for s in status_types],
            *[f'type_{t.lower()}' for t in transaction_types],
            'is_debit', 'has_error',
            
            # Временные
            'payment_year', 'payment_quarter', 'payment_half_year',
            'created_hour', 'modified_hour', 'has_period', 'period_length',
            
            # Валюты
            'currency_kzt', 'another_currency_present', 'exchange_dir_present', 'iban_credit_present',
            
            # UGD
            'has_ugd', 'ugd_bin_hash', 'credit_id_hash', 'sender_iin_present',
            
            # Текстовые
            'purpose_len', 'counterparty_len', 'iban_debit_prefix',
            'kbk_name_hash', 'knp_code_present', 'knp_present',
            'sender_name_present', 'employees_count'
        ]
        
        vector = np.array([features[name] for name in feature_names], dtype=np.float32)
        
        return {
            'vector': vector,
            'features': features,
            'feature_names': feature_names,
            'size': len(feature_names)
        }


if __name__ == "__main__":
    # Тестовые данные для демонстрации
    class KBK:
        def __init__(self, name, code, employee_loading_required, ugd_loading_required):
            self.name = name
            self.code = code
            self.employee_loading_required = employee_loading_required
            self.ugd_loading_required = ugd_loading_required

    class UGD:
        def __init__(self, bin, name, code):
            self.bin = bin
            self.name = name
            self.code = code

    print("\n" + "="*50)
    print("Тестирование PaymentPayload векторизации")
    print("="*50)
    
    # Создаем тестовый PaymentPayload
    test_payload = PaymentPayload(
        transaction_id="APP_TEST_123",
        iban_debit="KZ123456789012",
        amount=5000.50,
        kbk=KBK(
            name="Test KBK",
            code=123456,
            employee_loading_required=True,
            ugd_loading_required=False
        ),
        knp="911",
        purpose="Test payment",
        taxes_payment_operation_type="INDIVIDUAL_ENTREPRENEUR",
        quarter="FIRST",
        year=2023,
        ugd=UGD(
            bin="123456789",
            name="Test UGD",
            code=654321
        )
    )
    
    payload_result = PaymentFeatureExtractor.payload_to_vector(test_payload)
    print("\nРезультат для PaymentPayload:")
    print(f"Размер вектора: {payload_result['size']}")
    print("Пример признаков:")
    for name, value in list(payload_result['features'].items())[:5]:  # Первые 5 признаков
        print(f"{name}: {value}")
    
    print("\n" + "="*50)
    print("Тестирование TransactionDetail векторизации")
    print("="*50)
    
    # Создаем тестовый TransactionDetail
    test_transaction = TransactionDetail(
        transaction_type="EMPLTAX",
        id="fd680268-3f42-470a-b3a3-dc5485f81109",
        transaction_id="APP_INDNTRTAX_30aac5e0-abe3-4042-840f-cbf2fe2b99cc",
        created_date=datetime(2025, 4, 3, 19, 41, 7),
        modified_date=datetime(2025, 4, 3, 19, 52, 9),
        status="COMPLETED",
        amount=5986.32,
        another_amount=None,
        currency="KZT",
        another_currency=None,
        commission=150,
        counterparty="ГУ Аппарат акима сельского округа Акжар",
        purpose="Пеня за Пр. виды подакцизной прод.",
        iban_debit="KZ92886A220120705719",
        iban_credit="KZ24070105KSN0000000",
        credit_identifier="000440003800",
        exchange_direction=None,
        fact_sender_name=None,
        fact_sender_iin=None,
        error_message=None,
        knp="912-Пеня по обязательствам в бюджет",
        ugd_bin="000440003800",
        kbk_name="105278-ПрВидыПодАкцизПродВвозВРКИзТС",
        kbk_code="105278",
        knp_code="912",
        payment_half_year=None,
        payment_year=None,
        period="2025-01-26",
        payment_quarter=None,
        employees=[],
        debit=True
    )
    
    transaction_result = PaymentFeatureExtractor.transaction_to_vector(test_transaction)
    print("\nРезультат для TransactionDetail:")
    print(f"Размер вектора: {transaction_result['size']}")
    print("Пример признаков:")
    for name, value in list(transaction_result['features'].items())[:5]:  # Первые 5 признаков
        print(f"{name}: {value}")
    
    print("\nВектор для TransactionDetail:")
    print(json.dumps(transaction_result['features'], indent=2, ensure_ascii=False))