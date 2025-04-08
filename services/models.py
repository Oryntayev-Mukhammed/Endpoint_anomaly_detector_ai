from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union

@dataclass
class Transaction:
    id: str
    transaction_id: str
    created_date: datetime
    amount: float
    currency: str
    iban_credit: Optional[str]
    iban_debit: Optional[str]
    counterparty: str
    purpose: str
    status: str
    transaction_type: str
    credit_identifier: Optional[str]
    commission: float
    debit: bool
    another_currency: Optional[str] = None
    another_amount: Optional[float] = None
    exchange_direction: Optional[str] = None

@dataclass
class TransactionDetail:
    transaction_type: str
    id: str
    transaction_id: str
    created_date: datetime
    modified_date: datetime
    status: str
    amount: float
    another_amount: Optional[float]
    currency: str
    another_currency: Optional[str]
    commission: float
    counterparty: str
    purpose: str
    iban_debit: Optional[str]
    iban_credit: Optional[str]
    credit_identifier: Optional[str]
    exchange_direction: Optional[str]
    fact_sender_name: Optional[str]
    fact_sender_iin: Optional[str]
    error_message: Optional[str]
    knp: str
    ugd_bin: Optional[str]
    kbk_name: str
    kbk_code: str
    knp_code: str
    payment_half_year: Optional[int]
    payment_year: Optional[int]
    period: Optional[str]
    payment_quarter: Optional[int]
    employees: List[dict] = field(default_factory=list)
    debit: bool = True

    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт TransactionDetail из словаря c полями в стиле snakeCase -> camelCase."""
        created_date_str = data.get("createdDate")
        created_date = datetime.fromisoformat(created_date_str) if created_date_str else None

        modified_date_str = data.get("modifiedDate")
        modified_date = datetime.fromisoformat(modified_date_str) if modified_date_str else None

        return cls(
            transaction_type=data.get("transactionType", ""),
            id=data.get("id", ""),
            transaction_id=data.get("transactionId", ""),
            created_date=created_date,
            modified_date=modified_date,
            status=data.get("status", ""),
            amount=data.get("amount", 0.0),
            another_amount=data.get("anotherAmount"),
            currency=data.get("currency", "KZT"),
            another_currency=data.get("anotherCurrency"),
            commission=data.get("commission", 0.0),
            counterparty=data.get("counterparty", ""),
            purpose=data.get("purpose", ""),
            iban_debit=data.get("ibanDebit"),
            iban_credit=data.get("ibanCredit"),
            credit_identifier=data.get("creditIdentifier"),
            exchange_direction=data.get("exchangeDirection"),
            fact_sender_name=data.get("factSenderName"),
            fact_sender_iin=data.get("factSenderIin"),
            error_message=data.get("errorMessage"),
            knp=data.get("knp", ""),
            ugd_bin=data.get("ugdBin"),
            kbk_name=data.get("kbkName", ""),
            kbk_code=data.get("kbkCode", ""),
            knp_code=data.get("knpCode", ""),
            payment_half_year=data.get("paymentHalfYear"),
            payment_year=data.get("paymentYear"),
            period=data.get("period"),
            payment_quarter=data.get("paymentQuarter"),
            employees=data.get("employees", []),
            debit=data.get("debit", True)
        )

    def to_dict(self) -> dict:
        """Конвертирует текущий объект TransactionDetail обратно в dict с camelCase ключами."""
        return {
            "transactionType": self.transaction_type,
            "id": self.id,
            "transactionId": self.transaction_id,
            "createdDate": self.created_date.isoformat() if self.created_date else None,
            "modifiedDate": self.modified_date.isoformat() if self.modified_date else None,
            "status": self.status,
            "amount": self.amount,
            "anotherAmount": self.another_amount,
            "currency": self.currency,
            "anotherCurrency": self.another_currency,
            "commission": self.commission,
            "counterparty": self.counterparty,
            "purpose": self.purpose,
            "ibanDebit": self.iban_debit,
            "ibanCredit": self.iban_credit,
            "creditIdentifier": self.credit_identifier,
            "exchangeDirection": self.exchange_direction,
            "factSenderName": self.fact_sender_name,
            "factSenderIin": self.fact_sender_iin,
            "errorMessage": self.error_message,
            "knp": self.knp,
            "ugdBin": self.ugd_bin,
            "kbkName": self.kbk_name,
            "kbkCode": self.kbk_code,
            "knpCode": self.knp_code,
            "paymentHalfYear": self.payment_half_year,
            "paymentYear": self.payment_year,
            "period": self.period,
            "paymentQuarter": self.payment_quarter,
            "employees": self.employees,
            "debit": self.debit
        }


@dataclass
class UGD:
    bin: Optional[str]
    name: Optional[str]
    code: Optional[int]

@dataclass
class KBK:
    name: str
    code: int
    employee_loading_required: bool
    ugd_loading_required: bool

@dataclass
class PaymentPayload:
    timestamp: str
    transaction_id: str
    iban_debit: str
    amount: float
    kbk: KBK
    knp: str
    purpose: str
    taxes_payment_operation_type: str
    period: Optional[str] = None
    quarter: Optional[str] = None
    year: Optional[int] = None
    ugd: Optional[UGD] = None

    @classmethod
    def from_dict(cls, data: dict):
        payload_data = data.get('payload', data) 
        return cls(
            timestamp = data['timestamp'],
            transaction_id=payload_data['transactionId'],
            iban_debit=payload_data['ibanDebit'],
            amount=payload_data['amount'],
            kbk=KBK(
                name=payload_data['kbk']['name'],
                code=payload_data['kbk']['code'],
                employee_loading_required=payload_data['kbk']['employeeLoadingRequired'],
                ugd_loading_required=payload_data['kbk']['ugdLoadingRequired']
            ),
            knp=payload_data['knp'],
            purpose=payload_data['purpose'],
            taxes_payment_operation_type=payload_data['taxesPaymentOperationType'] if 'taxesPaymentOperationType' in payload_data else None,
            period=payload_data.get('period'),
            quarter=payload_data.get('quarter'),
            year=payload_data.get('year'),
            ugd=UGD(
                bin=payload_data['ugd']['bin'] if 'ugd' in payload_data and payload_data['ugd'] else None,
                name=payload_data['ugd']['name'] if 'ugd' in payload_data and payload_data['ugd'] else None,
                code=payload_data['ugd']['code'] if 'ugd' in payload_data and payload_data['ugd'] else None
            ) if 'ugd' in payload_data else None,
        )
    
    def to_dict(self) -> dict:
        """
        Возвращает словарь со структурой, аналогичной тому,
        что ожидает from_dict() (т. е. "распаковка" в виде transactionId, kbk и т.д.).
        """
        return {
            "timestamp": self.timestamp,
            "transactionId": self.transaction_id,
            "ibanDebit": self.iban_debit,
            "amount": self.amount,
            "kbk": {
                "name": self.kbk.name,
                "code": self.kbk.code,
                "employeeLoadingRequired": self.kbk.employee_loading_required,
                "ugdLoadingRequired": self.kbk.ugd_loading_required
            } if self.kbk else None,
            "knp": self.knp,
            "purpose": self.purpose,
            "taxesPaymentOperationType": self.taxes_payment_operation_type,
            "period": self.period,
            "quarter": self.quarter,
            "year": self.year,
            "ugd": {
                "bin": self.ugd.bin,
                "name": self.ugd.name,
                "code": self.ugd.code
            } if self.ugd else None
        }