from .base_api import BaseAPIClient
from typing import List, Dict

class DictionaryService(BaseAPIClient):
    def get_kbk_list(self, operation_type: str) -> List[Dict]:
        return self._request(
            "GET",
            f"/api/dictionary/dictionary/kbk/kbk-to-knp-list?taxesPaymentOperationType={operation_type}"
        )
    
    def get_ugd_list(self) -> List[Dict]:
        return self._request("GET", "/api/dictionary/dictionary/ugd/all")