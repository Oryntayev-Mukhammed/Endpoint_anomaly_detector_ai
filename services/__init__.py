from .transaction_service import TransactionService
from .account_service import AccountService
from .dictionary_service import DictionaryService
from .payment_service import PaymentService

class PaymentSystemAPI:
    def __init__(self, base_url: str, token: str):
        self.transactions = TransactionService(base_url, token)
        self.accounts = AccountService(base_url, token)
        self.dictionary = DictionaryService(base_url, token)
        self.payments = PaymentService(base_url, token)