import requests
from typing import Dict, Any

class BaseAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                verify=False,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Request to {url} failed: {str(e)}"
            if e.response:
                error_msg += f"\nResponse: {e.response.text}"
            raise Exception(error_msg)

class APIError(Exception):
    """Базовое исключение для ошибок API"""
    pass