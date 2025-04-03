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