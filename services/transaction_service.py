from .base_api import BaseAPIClient
from .models import Transaction
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
    TEST_IBAN = "KZ92886A220120705719"
    TEST_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6b1RlN1Z5UXFta0JrMktxbXg0QWlaR0lFZGZCcDFjbFZmZXk1TS1Vc1FzIn0.eyJleHAiOjE3NDM2OTMwODAsImlhdCI6MTc0MzY5MTI4MCwianRpIjoiNjllOWQ3NWQtYjhkYS00MDU5LWExMzgtYTc1MGE2Yzk4M2QxIiwiaXNzIjoiaHR0cDovL2hjYi1wbGF0Zm9ybS1rZXljbG9hay5rejAwYzEtc21lLXBsYXRmb3JtL2tleWNsb2FrL3JlYWxtcy9ob21lLWNyZWRpdC1pbnRlcm5ldC1iYW5raW5nLXJlYWxtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6Ijk1NjEzYmE4LTNlZjYtNDhiNy1hOTIzLTI3NTIzODI4ZjgzMCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcGxhdGZvcm0iLCJzaWQiOiJiOGIxMDgxZi01NzhkLTRmY2QtOGI5Ni1iMmUwNDgzNjBkNjkiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIi8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJDT1JFLVJFQURfQUNDT1VOVF9SRVFVSVNJVEVTIiwiQ1VSUkVOQ1lfUEFZTUVOVC1TSUdOX0VEU19PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1dJREdFVCIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fREVUQUlMUyIsIlBBWU1FTlQtQlVER0VUX1BBWU1FTlRTIiwiREVQT1NJVC1PV05FUiIsIlBBWU1FTlQtQ09OVkVSU0lPTiIsIkNPUkUtV1JJVEVfQUNDT1VOVCIsIk1FUkNIQU5ULVZJRVdfU0FMRVNST09NIiwiUEFZTUVOVC1DT05GSVJNX09UUCIsIlRBUklGRi1PV05FUiIsIlBBWU1FTlQtQkVUV0VFTl9ZT1VSX0FDQ09VTlRTIiwiQ0FSRFMtT1dORVJfU0VUX1RSQU5TQUNUSU9OX0xJTUlUUyIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9DT05WRVJTSU9OIiwiUEFZTUVOVC1DT05GSVJNX0VEUyIsIlBBWU1FTlQtUkVRVUlTSVRFU19UUkFOU0ZFUiIsInVtYV9hdXRob3JpemF0aW9uIiwiQ0FSRFMtVklFV19DQVJEX0FDQ09VTlRfREVUQUlMUyIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfRURJVCIsIkNBUkRTLU9XTkVSX1NFVF9QSU4iLCJBQ0NPVU5USU5HLU9XTkVSIiwiQ0FSRFMtT1dORVJfT1BFTl9DQVJEIiwiQ0FSRFMtT1dORVJfUEVSTUFORU5UX0xJTUlUUyIsIlBBWU1FTlQtQ09OVFJBQ1RfT1BFUkFUSU9OUyIsIkNBUkRTLVZJRVdfQ0FSRF9BQ0NPVU5UIiwiTUVSQ0hBTlQtRElTQUJMRV9TQUxFU1JPT00iLCJQQVlNRU5ULUZPUlNJR04iLCJQQVlNRU5ULVJFVklFV19EUkFGVCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfQ0xPU0UiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9WSUVXIiwiTUVSQ0hBTlQtQ1JFQVRFX1VQREFURV9TQUxFU1JPT00iLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1NJR05fT1RQX1VOSyIsIkNVUlJFTkNZX1BBWU1FTlQtU0lHTl9PVFBfSU5fQ1VSUkVOQ1lfVFJBTlNGRVIiLCJNRVJDSEFOVC1SRVFVRVNUX0NPTk5FQ1QiLCJDQVJEUy1WSUVXX0NBUkRfQ1ZWIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT1VOVEVSUEFSVFlfREVMRVRFIiwiUEFZTUVOVC1EUkFGVCIsIkNPUkUtUkVBRF9FRFNfQ0VSVElGSUNBVEUiLCJDT1JFLUNSRUFURV9FRFMiLCJQTEFURk9STS1ST0xFX0RJUkVDVE9SIiwiUExBVEZPUk0tT1JHQU5JWkFUSU9OX0FDQ09VTlRTX1ZJRVdFUiIsIkNVUlJFTkNZX1BBWU1FTlQtU0lHTl9PVFBfT1VUX0NVUlJFTkNZX1RSQU5TRkVSIiwiRUNPTS1PV05FUiIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fRkVFRCIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9FRElUIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9DRVJUSUZJQ0FURSIsIlBBWU1FTlQtQ09ORklSTV9SRVFVSVNJVEVTX1RSQU5TRkVSIiwiUEFZTUVOVC1DVVJSRU5DWV9UUkFOU0ZFUiIsIlBBWU1FTlQtUkVDRUlWSU5HX1BBWU1FTlQiLCJkZWZhdWx0LXJvbGVzLWhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcmVhbG0iLCJNRVJDSEFOVC1WSUVXX0NPTk5FQ1QiLCJDT1JFLVJFQURfQUNDT1VOVCIsIlBBWU1FTlQtU0lHTklORyIsIkNPUkUtUkVBRF9DT01QQU5ZIiwiUEFZTUVOVC1ERUxFVEVfRFJBRlQiLCJvZmZsaW5lX2FjY2VzcyIsIlBBWU1FTlQtTUFTU19UUkFOU0FDVElPTl9EUkFGVCIsIk1FUkNIQU5ULVZJRVdfSElTVE9SWSIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9JTl9DVVJSRU5DWV9UUkFOU0ZFUiIsIkRJUkVDVE9SIiwiTUVSQ0hBTlQtVklFV19TQUxFU1JPT01fREVUQUlMUyIsIkNBUkRTLU9XTkVSX0JMT0NLX1VOQkxPQ0tfQ0FSRCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09VTlRFUlBBUlRZX0NSRUFURSIsIlBBWU1FTlQtQ09ORklSTV9SRUZFUkVOQ0UiLCJQQVlNRU5ULVRSQU5TQUNUSU9OX0RSQUZUIiwiZGVmYXVsdC1wZXJtaXNzaW9uIiwiUEFZTUVOVC1DT05GSVJNX1NUQVRFTUVOVCIsIkNVUlJFTkNZX1BBWU1FTlQtU0lHTl9PVFBfQ09OVkVSU0lPTiIsIlBBWU1FTlQtQ09ORklSTV9CVURHRVRfUEFZTUVOVFMiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlZFUlNJT05fV0lER0VUIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9DUkVBVEUiLCJDVVJSRU5DWV9QQVlNRU5ULUlOX0NVUlJFTkNZX1RSQU5TRkVSX1dJREdFVCIsIlBBWU1FTlQtUkVGRVJFTkNFIiwiQUNDT1VOVElORy1JTlNVUkFOQ0VfT1dORVIiLCJNRVJDSEFOVC1SRVFVRVNUX1JFRlVORCIsIkNBUkRTLVZJRVdfQ0FSRF9OVU1CRVIiLCJQQVlNRU5ULVVQREFURV9EUkFGVCIsIlBBWU1FTlQtT1BFUkFUSU9OUyIsIlBBWU1FTlQtQ09ORklSTV9CRVRXRUVOX1lPVVJfQUNDT1VOVFMiLCJNRVJDSEFOVC1NQU5BR0VfREVMSVZFUlkiLCJDT1JFLVdSSVRFX0VNUExPWUVFIiwiUEFZTUVOVC1DT05GSVJNX01BU1NfVFJBTlNBQ1RJT05fRFJBRlQiLCJQQVlNRU5ULVNUQVRFTUVOVCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfVE9fU0lHTl9VTksiLCJQQVlNRU5ULUNSRUFURV9EUkFGVCIsIkNBUkRTLU9XTkVSX0FDVElWQVRFX0NBUkQiXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6ImRpcmVjdG9yU3ViIHByb2ZpbGUgZW1haWwgaWluIHBob25lIG1haW5BY2NvdW50SWQgY29tcGFueUlkZW50aWZpZXIiLCJwaG9uZU51bWJlciI6Iis3Nzc3NDU1MjIxMyIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiY29tcGFueUlkZW50aWZpZXIiOiI4NDEyMjEzMDI3MjkiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJjZmE0YzIxYy0yMzk1LTRhOTMtYWFiNS01Zjg1ZTRiODQ2YWYiLCJtYWluQWNjb3VudElkIjoiODA0M2EyMTctZmE5Yi00NDk1LWExOTYtZmM3ZGM4M2VlZTcxIiwiaWluIjoiODQxMjIxMzAyNzI5In0.m1lSkGLMcNibxlvM_5E1vmjUhxoL9LO22LVEaeza7Dkd1VUSaF-hOnSxsSFyeM8qzQbrjypfmLekVpwUnyWRVdI2xVK1RRGlH5MUL7Jk9bX75T7OE0rpkTk58cJfslMBFndDiQ_JWS1YONAuXpIGN8Utkuvb02YqsSbcQNCluEvx6-F0c2Ak7wBEsFrsuCdFvChnmQfrJZMYaGH06LEDJRLR-SEn7vgQ-EBkWIUvrU0iKi1jAbko9SYqfw4NmpiFLXhG3BmqdzRixQNzconD-_AXWuMnrjI4XmhG7tPeZUYX3sQNChQN-u8wkqFpVdpjnyl3mB_qSagpuQ_5dLDEzA"
    TEST_BASE_URL = "https://sme-bff.kz.infra"
    
    # Инициализация сервиса
    service = TransactionService(TEST_BASE_URL, TEST_TOKEN)
    
    print("=== Тестирование TransactionService ===")
    
    try:
        # Тест 1: Получение списка транзакций
        print("\n1. Получение последних транзакций...")
        transactions = service.get_transactions(
            ibans=[TEST_IBAN],
            dateFrom=(datetime.now() - timedelta(days=7)).isoformat() + "Z",
            status=["COMPLETED"]
        )
        print(f"Найдено транзакций: {len(transactions.get('transactions', []))}")
        
        # Тест 2: Получение деталей конкретной транзакции
        if transactions.get('transactions'):
            test_tx_id_tx = transactions['transactions'][0]['transactionId']
            print(f"\n2. Получение деталей транзакции по ID: {test_tx_id_tx}")
            
            # Получаем id нужной транзакции. Для теста берем самый первый. id и transactionId не одно и тоже
            tx_details = service.get_by_id_in_transactions(test_tx_id_tx)

            if tx_details:
                print("Детали транзакции:")
                print(tx_details)
                
                # Получаем объект Transaction
                tx = service.get_transaction_details(tx_details.id, tx_details.transaction_type)
                
                print(tx)
            else:
                print("Детали транзакции не найдены")
        
        print("\nТестирование завершено успешно!")
        
    except Exception as e:
        print(f"\nОшибка при тестировании: {str(e)}")
        print("Убедитесь, что:")
        print("- Указан корректный BASE_URL и токен")
        print("- Сервер API доступен")
        print("- У вас есть права на доступ к транзакциям")