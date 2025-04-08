from .base_api import BaseAPIClient
from .models import Transaction, TransactionDetail
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class TransactionService(BaseAPIClient):
    def get_transactions(self, **kwargs) -> Dict:
        """Получение транзакций с фильтрами"""
        payload = {
            "search": {
                "iban": None,
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
        result = self.get_transactions()
        for tx in result.get('transactions', []):
            if tx.get('transactionId') == transaction_id:
                return self._parse_transaction(tx)
        return None
    
    def get_transaction_details_by_transaction_id(self, tr_id: str):
        # Тест 1: Получение списка транзакций
        transactions = self.get_transactions(
            dateFrom=(datetime.now() - timedelta(days=7)).isoformat() + "Z",
            status=["COMPLETED"]
        )
        
        if transactions.get('transactions'):
            
            # Получаем id нужной транзакции. Для теста берем самый первый. id и transactionId не одно и тоже
            tx_details = self.get_by_id_in_transactions(tr_id)

            if tx_details:
                # Получаем объект Transaction
                return self.get_transaction_details(tx_details.id, tx_details.transaction_type)
            else:
                raise Exception("Транзакция не найдена!!")
    
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
    TEST_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6b1RlN1Z5UXFta0JrMktxbXg0QWlaR0lFZGZCcDFjbFZmZXk1TS1Vc1FzIn0.eyJleHAiOjE3NDQxMDk4ODcsImlhdCI6MTc0NDEwODA4NywianRpIjoiNDllZmY0OGUtY2U3NC00N2QyLTkxY2MtMDllOTMwNjA3ZTBiIiwiaXNzIjoiaHR0cDovL2hjYi1wbGF0Zm9ybS1rZXljbG9hay5rejAwYzEtc21lLXBsYXRmb3JtL2tleWNsb2FrL3JlYWxtcy9ob21lLWNyZWRpdC1pbnRlcm5ldC1iYW5raW5nLXJlYWxtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjkyOThiYzc0LTUwNWEtNDYyNy05YmU1LWZkMDRiZDQ4NWU2YSIsInR5cCI6IkJlYXJlciIsImF6cCI6ImhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcGxhdGZvcm0iLCJzaWQiOiIwZmZjYjFlYi03OTYxLTQwNWEtODI4Yi04M2U2NWZhZDkyZTQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIi8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJDT1JFLVJFQURfQUNDT1VOVF9SRVFVSVNJVEVTIiwiQ1VSUkVOQ1lfUEFZTUVOVC1TSUdOX0VEU19PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1dJREdFVCIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fREVUQUlMUyIsIlBBWU1FTlQtQlVER0VUX1BBWU1FTlRTIiwiREVQT1NJVC1PV05FUiIsIlBBWU1FTlQtQ09OVkVSU0lPTiIsIkNPUkUtV1JJVEVfQUNDT1VOVCIsIk1FUkNIQU5ULVZJRVdfU0FMRVNST09NIiwiUEFZTUVOVC1DT05GSVJNX09UUCIsIlRBUklGRi1PV05FUiIsIlBBWU1FTlQtQkVUV0VFTl9ZT1VSX0FDQ09VTlRTIiwiQ0FSRFMtT1dORVJfU0VUX1RSQU5TQUNUSU9OX0xJTUlUUyIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9DT05WRVJTSU9OIiwiTUFOQUdFUiIsIlBBWU1FTlQtQ09ORklSTV9FRFMiLCJQQVlNRU5ULVJFUVVJU0lURVNfVFJBTlNGRVIiLCJ1bWFfYXV0aG9yaXphdGlvbiIsIkNBUkRTLVZJRVdfQ0FSRF9BQ0NPVU5UX0RFVEFJTFMiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX0VESVQiLCJDQVJEUy1PV05FUl9TRVRfUElOIiwiQUNDT1VOVElORy1PV05FUiIsIkNBUkRTLU9XTkVSX09QRU5fQ0FSRCIsIkNBUkRTLU9XTkVSX1BFUk1BTkVOVF9MSU1JVFMiLCJQQVlNRU5ULUNPTlRSQUNUX09QRVJBVElPTlMiLCJBQ0NPVU5USU5HLUlOU1VSQU5DRV9BTEwiLCJDQVJEUy1WSUVXX0NBUkRfQUNDT1VOVCIsIlBBWU1FTlQtRk9SU0lHTiIsIlBBWU1FTlQtUkVWSUVXX0RSQUZUIiwiRUNPTS1XUklURVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX0NMT1NFIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT1VOVEVSUEFSVFlfVklFVyIsIk1FUkNIQU5ULUNSRUFURV9VUERBVEVfU0FMRVNST09NIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9TSUdOX09UUF9VTksiLCJDVVJSRU5DWV9QQVlNRU5ULVNJR05fT1RQX0lOX0NVUlJFTkNZX1RSQU5TRkVSIiwiQ0FSRFMtVklFV19DQVJEX0NWViIsIkNVUlJFTkNZX1BBWU1FTlQtQ09VTlRFUlBBUlRZX0RFTEVURSIsIlBBWU1FTlQtRFJBRlQiLCJDVVJSRU5DWV9QQVlNRU5ULVNJR05fT1RQX09VVF9DVVJSRU5DWV9UUkFOU0ZFUiIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fRkVFRCIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9FRElUIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9DRVJUSUZJQ0FURSIsIlBBWU1FTlQtQ09ORklSTV9SRVFVSVNJVEVTX1RSQU5TRkVSIiwiUEFZTUVOVC1DVVJSRU5DWV9UUkFOU0ZFUiIsIlBBWU1FTlQtUkVDRUlWSU5HX1BBWU1FTlQiLCJkZWZhdWx0LXJvbGVzLWhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcmVhbG0iLCJNRVJDSEFOVC1WSUVXX0NPTk5FQ1QiLCJDT1JFLVJFQURfQUNDT1VOVCIsIlBBWU1FTlQtU0lHTklORyIsIkNPUkUtUkVBRF9DT01QQU5ZIiwiUEFZTUVOVC1ERUxFVEVfRFJBRlQiLCJvZmZsaW5lX2FjY2VzcyIsIlBBWU1FTlQtTUFTU19UUkFOU0FDVElPTl9EUkFGVCIsIk1FUkNIQU5ULVZJRVdfSElTVE9SWSIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9JTl9DVVJSRU5DWV9UUkFOU0ZFUiIsIk1FUkNIQU5ULVZJRVdfU0FMRVNST09NX0RFVEFJTFMiLCJDQVJEUy1PV05FUl9CTE9DS19VTkJMT0NLX0NBUkQiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9DUkVBVEUiLCJQQVlNRU5ULUNPTkZJUk1fUkVGRVJFTkNFIiwiUEFZTUVOVC1UUkFOU0FDVElPTl9EUkFGVCIsImRlZmF1bHQtcGVybWlzc2lvbiIsIlBBWU1FTlQtQ09ORklSTV9TVEFURU1FTlQiLCJDVVJSRU5DWV9QQVlNRU5ULVNJR05fT1RQX0NPTlZFUlNJT04iLCJQQVlNRU5ULUNPTkZJUk1fQlVER0VUX1BBWU1FTlRTIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05WRVJTSU9OX1dJREdFVCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfQ1JFQVRFIiwiQ1VSUkVOQ1lfUEFZTUVOVC1JTl9DVVJSRU5DWV9UUkFOU0ZFUl9XSURHRVQiLCJQQVlNRU5ULVJFRkVSRU5DRSIsIk1FUkNIQU5ULVJFUVVFU1RfUkVGVU5EIiwiQ0FSRFMtVklFV19DQVJEX05VTUJFUiIsIlBBWU1FTlQtVVBEQVRFX0RSQUZUIiwiUEFZTUVOVC1PUEVSQVRJT05TIiwiUEFZTUVOVC1DT05GSVJNX0JFVFdFRU5fWU9VUl9BQ0NPVU5UUyIsIk1FUkNIQU5ULU1BTkFHRV9ERUxJVkVSWSIsIlBBWU1FTlQtQ09ORklSTV9NQVNTX1RSQU5TQUNUSU9OX0RSQUZUIiwiUEFZTUVOVC1TVEFURU1FTlQiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1RPX1NJR05fVU5LIiwiUEFZTUVOVC1DUkVBVEVfRFJBRlQiLCJDQVJEUy1PV05FUl9BQ1RJVkFURV9DQVJEIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJkaXJlY3RvclN1YiBwcm9maWxlIGVtYWlsIGlpbiBwaG9uZSBtYWluQWNjb3VudElkIGNvbXBhbnlJZGVudGlmaWVyIiwicGhvbmVOdW1iZXIiOiIrNzcwMTQ0MDAzMzEiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNvbXBhbnlJZGVudGlmaWVyIjoiODUwODI0NDAwNzk2IiwiZGlyZWN0b3JTdWIiOiIyM2E5NjdmMS03ZmM3LTQzMWQtYTQ1MC0xMjg2ZDQ0Y2E5ODIiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIyZmVjN2I4NC0xZDg5LTQyYjgtYjI1NS01MDEwZmNjMjNhOTYiLCJtYWluQWNjb3VudElkIjoiMTkxNWE4NTAtODY4Mi00OWU4LTg1YWQtOWRhMzkzOTMxOTA0IiwiaWluIjoiOTgwMTA0NDAwMzMxIn0.sAV5z2RbFtqBAOgKh6IZDTXnWo-C1YoPaRMwcVq4i4fVm-oF72r1lnFsVFbcfkxaJpE5_63pJjdsXDf-FFPyAYDUReDzLT8jM5nQJtp1Z7Mts48tyISsXXBOcorNAbSgxlJHGBUgLcGNedEoMKJvH-WcKuCQHEOn-32jBioJ5Jp9f8_E-_gXdg3cOnPx1L27A-mTQ6w2sinANsLrW387Xuz8tNknl25YBt1UilM9IaOp0piQ22-4Ro6TjyOCsBc8elfOSrSSCToXzIOj3j-DcyBeYzP_nqsDVsblPAj5Mb5JQfkE5VFgbRKCRHpdDEo66l04hmxmfQAdMQbELCJHrw"
    TEST_BASE_URL = "https://sme-bff.kz.infra"
    
    # Инициализация сервиса
    service = TransactionService(TEST_BASE_URL, TEST_TOKEN)
    
    print("=== Тестирование TransactionService ===")
    
    try:
        transaction_detail = TransactionDetail.from_dict(service.get_transaction_details_by_transaction_id("APP_REQTRANS_ad981c30-1458-11f0-b202-6b87b91423ca"))
        print(transaction_detail.to_dict())
        
        print("\nТестирование завершено успешно!")
        
    except Exception as e:
        print(f"\nОшибка при тестировании: {str(e)}")
        print("Убедитесь, что:")
        print("- Указан корректный BASE_URL и токен")
        print("- Сервер API доступен")
        print("- У вас есть права на доступ к транзакциям")