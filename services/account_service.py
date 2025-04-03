from .base_api import BaseAPIClient
from typing import List, Dict

class AccountService(BaseAPIClient):
    def get_accounts(self) -> List[Dict]:
        return self._request("GET", "/api/account/accounts").get('accounts', [])
    
    def get_open_accounts(self) -> List[Dict]:
        return [
            acc for acc in self.get_accounts()
            if acc.get('accountStatus') == 'OPEN' 
            and not acc.get('fullyBlocked')
        ]