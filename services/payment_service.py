from .base_api import BaseAPIClient
from .models import PaymentPayload
from typing import Dict

class PaymentService(BaseAPIClient):
    def calculate_commission(self, payload: Dict) -> Dict:
        return self._request(
            "PUT",
            "/api/charge-calculator/api/v1/charges/trn/multi-calculate",
            json=[payload]
        )
    
    def make_payment(self, payload: PaymentPayload) -> Dict:
        return self._request(
            "POST",
            "/api/payment/api/v5/budget/init/entrepreneur",
            json=payload
        )