from base_api import BaseAPIClient
from models import Transaction
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class TransactionService(BaseAPIClient):
    def get_transactions(self, ibans: List[str], **kwargs) -> Dict:
        """Получение транзакций с фильтрами"""
        payload = {
            "search": {
                "iban": ibans,
                **kwargs
            },
            "pageable": {
                "page": 0,
                "size": 20,
                "sort": {
                    "property": "createdDate",
                    "direction": "DESC"
                }
            }
        }
        return self._request(
            "POST",
            "/api/payment-history/api/v1/history/transactions",
            json=payload
        )
    
    def get_transaction_details(self, id: str, type: str) -> Optional[Dict]:
        """Получение деталей транзакции по ID"""
        payload = {
            "id": id,
            "type": type  # или другой тип, в зависимости от транзакции
        }
        response = self._request(
            "POST",
            "/api/payment-history/api/v1/history/transaction",
            json=payload
        )
        return response.get('transaction')

    def get_by_id_in_transactions(self, transaction_id: str) -> Optional[Transaction]:
        """Получение транзакции по ID"""
        result = self.get_transactions(ibans=[])
        for tx in result.get('transactions', []):
            if tx.get('transactionId') == transaction_id:
                return self._parse_transaction(tx)
        return None
    
    def get_transaction_details_by_transaction_id(self, iban: str):
        # Тест 1: Получение списка транзакций
        transactions = service.get_transactions(
            ibans=[iban],
            dateFrom=(datetime.now() - timedelta(days=7)).isoformat() + "Z",
            status=["COMPLETED"]
        )
        
        if transactions.get('transactions'):
            test_tx_id_tx = transactions['transactions'][0]['transactionId']

            # Получаем id нужной транзакции. Для теста берем самый первый. id и transactionId не одно и тоже
            tx_details = service.get_by_id_in_transactions(test_tx_id_tx)

            if tx_details:
                # Получаем объект Transaction
                return service.get_transaction_details(tx_details.id, tx_details.transaction_type)
            else:
                raise "Транзакция не найдена!!"
    
    def _parse_transaction(self, data: Dict) -> Transaction:
        """Парсинг сырых данных в объект Transaction"""
        return Transaction(
            id=data['id'],
            transaction_id=data['transactionId'],
            created_date=datetime.fromisoformat(data['createdDate']),
            amount=data['amount'],
            currency=data['currency'],
            iban_credit=data.get('ibanCredit'),
            iban_debit=data.get('ibanDebit'),
            counterparty=data['counterparty'],
            purpose=data['purpose'],
            status=data['status'],
            transaction_type=data['transactionType'],
            credit_identifier=data['creditIdentifier'],
            commission=data.get('commission', 0),
            debit=data.get('debit', False)
        )

if __name__ == "__main__":
    # Тестовые данные для демонстрации
    TEST_IBAN = "KZ81886A220120720370"
    TEST_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6b1RlN1Z5UXFta0JrMktxbXg0QWlaR0lFZGZCcDFjbFZmZXk1TS1Vc1FzIn0.eyJleHAiOjE3NDQxMDc5NDcsImlhdCI6MTc0NDEwNjE0NywianRpIjoiOTE1MWNkNzItYmViMC00MzMzLWJhOTAtZDMxM2YzNzYxMDY2IiwiaXNzIjoiaHR0cDovL2hjYi1wbGF0Zm9ybS1rZXljbG9hay5rejAwYzEtc21lLXBsYXRmb3JtL2tleWNsb2FrL3JlYWxtcy9ob21lLWNyZWRpdC1pbnRlcm5ldC1iYW5raW5nLXJlYWxtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjE5MTVhODUwLTg2ODItNDllOC04NWFkLTlkYTM5MzkzMTkwNCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcGxhdGZvcm0iLCJzaWQiOiI0ZTkyMmE2MS0xODUzLTQ1ZGYtYmYyMC04ZGQxMzBmODdmNmUiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIi8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJQTEFURk9STS1DSElMRF9BQ0NPVU5UU19PV05FUiIsIm9mZmxpbmVfYWNjZXNzIiwiUExBVEZPUk0tQ0hJTERfQUNDT1VOVFNfVklFV0VSIiwidW1hX2F1dGhvcml6YXRpb24iLCJkZWZhdWx0LXJvbGVzLWhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcmVhbG0iLCJNQUlOX0FDQ09VTlQiXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBkaXJlY3RvclN1YiBwcm9maWxlIGVtYWlsIGlpbiBwaG9uZSBtYWluQWNjb3VudElkIGNvbXBhbnlJZGVudGlmaWVyIiwicGhvbmVOdW1iZXIiOiIrNzcwMTQ0MDAzMzEiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInByZWZlcnJlZF91c2VybmFtZSI6ImIwNzE4YWYwLWFkMzktNGFhMy05NTYxLTkzZmE5NGYwZTM2MSIsImlpbiI6Ijk4MDEwNDQwMDMzMSJ9.eM4DPDNAVlrSyPCPJ67shXHY0GakVj8hVgstRcZL0QOESXJxCT7UqWV_m-YW7QBazYP-45TqjXW2hADQgif86Bb5-0BFfAp_75sTvYQDrVmtsT9cdv_0nF62Bkt61LbUMfdjR6zwNrPLu7mUMegCckw-S8nIZ8ficrFscciHPc1QAXquaAQozY9E2FnRvuJs5JY1pJH-7h1M6s_swPMQ5cM_0ZM8KEomIWbdpHiDIS2JuolgyZj1mGJKz7MmyiuDahzpQ8BTlbUvoEb1fjt-pSbWhkhWcunKCSVWITbTTWot7Dwde8Ptm-Ku3IURL3tmpx0uSM-gy_frxWbLvXYG7g"
    TEST_BASE_URL = "https://sme-bff.kz.infra"
    
    # Инициализация сервиса
    service = TransactionService(TEST_BASE_URL, TEST_TOKEN)
    
    print("=== Тестирование TransactionService ===")
    
    try:
        print(service.get_transaction_details_by_transaction_id(TEST_IBAN))
        
        print("\nТестирование завершено успешно!")
        
    except Exception as e:
        print(f"\nОшибка при тестировании: {str(e)}")
        print("Убедитесь, что:")
        print("- Указан корректный BASE_URL и токен")
        print("- Сервер API доступен")
        print("- У вас есть права на доступ к транзакциям")