import requests
import uuid
import random
from datetime import date
from dateutil.relativedelta import relativedelta
import json
from typing import Dict, Any, Optional, List

class PaymentPayloadGenerator:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.selected_operation_type = "INDIVIDUAL_ENTREPRENEUR"
        self._load_initial_data()

    def _fetch_api_data(self, endpoint: str) -> Dict:
        """Базовый метод для выполнения API-запросов"""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка запроса к {endpoint}: {e}")

    def _load_initial_data(self):
        """Загрузка всех необходимых справочников"""
        # Загрузка счетов
        accounts_data = self._fetch_api_data("/api/account/accounts")
        self.valid_accounts = [
            acc for acc in accounts_data.get("accounts", [])
            if acc.get("accountStatus") == "OPEN" and not acc.get("fullyBlocked", True)
        ]
        
        if not self.valid_accounts:
            raise Exception("Нет доступных счетов для списания")
        
        # Загрузка справочников
        self.ugd_list = self._fetch_api_data("/api/dictionary/dictionary/ugd/all")
        self.kbk_list = self._fetch_api_data(
            f"/api/dictionary/dictionary/kbk/kbk-to-knp-list?taxesPaymentOperationType={self.selected_operation_type}"
        )
        
        if not self.kbk_list:
            raise Exception("Не удалось загрузить список KBK")

    def fetch_period_list(self, kbk_code: str, knp_code: str) -> List[Dict]:
        """Получение списка периодов для KBK/KNP"""
        period_data = self._fetch_api_data(
            f"/api/dictionary/dictionary/payment-period?"
            f"operationType={self.selected_operation_type}"
            f"&kbk={kbk_code}"
            f"&knp={knp_code}"
            f"&id=0"
        )

        if not period_data or period_data.get("periodType") is None:
            return []

        if "periods" in period_data:
            return [
                {
                    "year": p["year"],
                    "quarter": p["quarter"],     
                    "yearHalf": p["yearHalf"]  
                }
                for p in period_data["periods"]
            ]
        return []

    def generate_payload(
        self,
        iban: str,
        kbk_code: str,
        knp_code: str,
        amount: float,
        purpose: str,
        period: str,
        fix_ugd: bool = False,
        ugd_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Генерация payload для платежа"""
        # Находим KBK и KNP в справочниках
        kbk = next((k for k in self.kbk_list if k["code"] == kbk_code), None)
        if not kbk:
            raise ValueError(f"KBK с кодом {kbk_code} не найден")
        
        knp = next((k for k in kbk["knpList"] if k["knpCode"] == knp_code), None)
        if not knp:
            raise ValueError(f"KNP с кодом {knp_code} не найден для KBK {kbk_code}")

        # Формируем базовый payload
        payload = {
            "transactionId": f"APP_INDNTRTAX_{uuid.uuid4()}",
            "ibanDebit": iban,
            "amount": amount,
            "kbk": {
                "name": kbk["name"],
                "code": kbk["code"],
                "employeeLoadingRequired": kbk["employeeLoadingRequired"],
                "ugdLoadingRequired": kbk["ugdLoadingRequired"]
            },
            "knp": knp["knpCode"],
            "purpose": purpose,
            "taxesPaymentOperationType": self.selected_operation_type
        }

        # Обработка периода в зависимости от типа KBK
        if str(kbk_code).startswith('1'):
            periods = self.fetch_period_list(kbk_code, knp_code)
            if periods:
                period_data = random.choice(periods) if not fix_ugd else periods[0]
                payload["quarter"] = period_data["quarter"]
                payload["year"] = period_data["year"]
            else:
                payload["period"] = period
        else:
            payload["period"] = period

        # Добавляем UGD если требуется
        if kbk.get("ugdLoadingRequired"):
            if not ugd_code:
                ugd = random.choice(self.ugd_list)
            else:
                ugd = next((u for u in self.ugd_list if u["code"] == ugd_code), None)
                if not ugd:
                    raise ValueError(f"UGD с кодом {ugd_code} не найден")
            
            payload["bin"] = ugd["bin"]

        return payload

    def generate_random_payload(self, iban: str) -> Dict[str, Any]:
        """Генерация полностью случайного payload"""
        # Выбираем случайный счет, если не указан
        if not iban:
            account = random.choice(self.valid_accounts)
            iban = account["iban"]

        # Выбираем случайные KBK и KNP
        kbk = random.choice(self.kbk_list)
        knp = random.choice(kbk["knpList"])

        # Генерируем случайные значения
        amount = round(random.uniform(100.0, 10000.0), 2)
        purpose = f"{knp['knpName']}_{random.randint(1000, 9999)}"
        
        # Обработка периода
        if str(kbk["code"]).startswith('1'):
            periods = self.fetch_period_list(kbk["code"], knp["knpCode"])
            if periods:
                period_data = random.choice(periods)
                period = period_data["quarter"]
                year = period_data["year"]
            else:
                period = (date.today() - relativedelta(days=random.randint(1, 365))).isoformat()
                year = None
        else:
            period = (date.today() - relativedelta(days=random.randint(1, 365))).isoformat()
            year = None

        # Формируем payload
        payload = {
            "transactionId": f"APP_INDNTRTAX_{uuid.uuid4()}",
            "ibanDebit": iban,
            "amount": amount,
            "kbk": {
                "name": kbk["name"],
                "code": kbk["code"],
                "employeeLoadingRequired": kbk["employeeLoadingRequired"],
                "ugdLoadingRequired": kbk["ugdLoadingRequired"]
            },
            "knp": knp["knpCode"],
            "purpose": purpose,
            "taxesPaymentOperationType": self.selected_operation_type
        }

        if year:
            payload["year"] = year
            payload["quarter"] = period
        else:
            payload["period"] = period

        # Добавляем UGD если требуется
        if kbk.get("ugdLoadingRequired"):
            ugd = random.choice(self.ugd_list)
            payload["bin"] = ugd["bin"]

        return payload

if __name__ == "__main__":
    # Инициализация генератора
    generator = PaymentPayloadGenerator(
        base_url="https://sme-bff.kz.infra",
        token="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6b1RlN1Z5UXFta0JrMktxbXg0QWlaR0lFZGZCcDFjbFZmZXk1TS1Vc1FzIn0.eyJleHAiOjE3NDM1MDg5ODUsImlhdCI6MTc0MzUwNzE4NSwianRpIjoiNDhkYWM0YWEtMGZmOS00NTcwLTk3NTUtOGI4Zjg0Yzc0MDVkIiwiaXNzIjoiaHR0cDovL2hjYi1wbGF0Zm9ybS1rZXljbG9hay5rejAwYzEtc21lLXBsYXRmb3JtL2tleWNsb2FrL3JlYWxtcy9ob21lLWNyZWRpdC1pbnRlcm5ldC1iYW5raW5nLXJlYWxtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImNjNWRlMmNmLTBkNmMtNGFlYi1hOGY4LWU4ZmIzODllMGQwZCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcGxhdGZvcm0iLCJzaWQiOiI4MGMyYWFjZi1mYjZhLTQxZTQtOGQ1YS1kZTAyOTVmNDhjN2MiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIi8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJDT1JFLVJFQURfQUNDT1VOVF9SRVFVSVNJVEVTIiwiQ1VSUkVOQ1lfUEFZTUVOVC1TSUdOX0VEU19PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1dJREdFVCIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fREVUQUlMUyIsIlBBWU1FTlQtQlVER0VUX1BBWU1FTlRTIiwiREVQT1NJVC1PV05FUiIsIlBBWU1FTlQtQ09OVkVSU0lPTiIsIkNPUkUtV1JJVEVfQUNDT1VOVCIsIk1FUkNIQU5ULVZJRVdfU0FMRVNST09NIiwiUEFZTUVOVC1DT05GSVJNX09UUCIsIlRBUklGRi1PV05FUiIsIlBBWU1FTlQtQkVUV0VFTl9ZT1VSX0FDQ09VTlRTIiwiQ0FSRFMtT1dORVJfU0VUX1RSQU5TQUNUSU9OX0xJTUlUUyIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9DT05WRVJTSU9OIiwiUEFZTUVOVC1DT05GSVJNX0VEUyIsIlBBWU1FTlQtUkVRVUlTSVRFU19UUkFOU0ZFUiIsInVtYV9hdXRob3JpemF0aW9uIiwiQ0FSRFMtVklFV19DQVJEX0FDQ09VTlRfREVUQUlMUyIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfRURJVCIsIkNBUkRTLU9XTkVSX1NFVF9QSU4iLCJBQ0NPVU5USU5HLU9XTkVSIiwiQ0FSRFMtT1dORVJfT1BFTl9DQVJEIiwiQ0FSRFMtT1dORVJfUEVSTUFORU5UX0xJTUlUUyIsIlBBWU1FTlQtQ09OVFJBQ1RfT1BFUkFUSU9OUyIsIkNBUkRTLVZJRVdfQ0FSRF9BQ0NPVU5UIiwiTUVSQ0hBTlQtRElTQUJMRV9TQUxFU1JPT00iLCJQQVlNRU5ULUZPUlNJR04iLCJQQVlNRU5ULVJFVklFV19EUkFGVCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfQ0xPU0UiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9WSUVXIiwiTUVSQ0hBTlQtQ1JFQVRFX1VQREFURV9TQUxFU1JPT00iLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1NJR05fT1RQX1VOSyIsIkNVUlJFTkNZX1BBWU1FTlQtU0lHTl9PVFBfSU5fQ1VSUkVOQ1lfVFJBTlNGRVIiLCJNRVJDSEFOVC1SRVFVRVNUX0NPTk5FQ1QiLCJDQVJEUy1WSUVXX0NBUkRfQ1ZWIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT1VOVEVSUEFSVFlfREVMRVRFIiwiUEFZTUVOVC1EUkFGVCIsIkNPUkUtUkVBRF9FRFNfQ0VSVElGSUNBVEUiLCJDT1JFLUNSRUFURV9FRFMiLCJQTEFURk9STS1ST0xFX0RJUkVDVE9SIiwiUExBVEZPUk0tT1JHQU5JWkFUSU9OX0FDQ09VTlRTX1ZJRVdFUiIsIkNVUlJFTkNZX1BBWU1FTlQtU0lHTl9PVFBfT1VUX0NVUlJFTkNZX1RSQU5TRkVSIiwiRUNPTS1PV05FUiIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fRkVFRCIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9FRElUIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9DRVJUSUZJQ0FURSIsIlBBWU1FTlQtQ09ORklSTV9SRVFVSVNJVEVTX1RSQU5TRkVSIiwiUEFZTUVOVC1DVVJSRU5DWV9UUkFOU0ZFUiIsIlBBWU1FTlQtUkVDRUlWSU5HX1BBWU1FTlQiLCJkZWZhdWx0LXJvbGVzLWhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcmVhbG0iLCJNRVJDSEFOVC1WSUVXX0NPTk5FQ1QiLCJDT1JFLVJFQURfQUNDT1VOVCIsIlBBWU1FTlQtU0lHTklORyIsIkNPUkUtUkVBRF9DT01QQU5ZIiwiUEFZTUVOVC1ERUxFVEVfRFJBRlQiLCJvZmZsaW5lX2FjY2VzcyIsIlBBWU1FTlQtTUFTU19UUkFOU0FDVElPTl9EUkFGVCIsIk1FUkNIQU5ULVZJRVdfSElTVE9SWSIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9JTl9DVVJSRU5DWV9UUkFOU0ZFUiIsIkRJUkVDVE9SIiwiTUVSQ0hBTlQtVklFV19TQUxFU1JPT01fREVUQUlMUyIsIkNBUkRTLU9XTkVSX0JMT0NLX1VOQkxPQ0tfQ0FSRCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09VTlRFUlBBUlRZX0NSRUFURSIsIlBBWU1FTlQtQ09ORklSTV9SRUZFUkVOQ0UiLCJQQVlNRU5ULVRSQU5TQUNUSU9OX0RSQUZUIiwiZGVmYXVsdC1wZXJtaXNzaW9uIiwiUEFZTUVOVC1DT05GSVJNX1NUQVRFTUVOVCIsIkNVUlJFTkNZX1BBWU1FTlQtU0lHTl9PVFBfQ09OVkVSU0lPTiIsIlBBWU1FTlQtQ09ORklSTV9CVURHRVRfUEFZTUVOVFMiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlZFUlNJT05fV0lER0VUIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9DUkVBVEUiLCJDVVJSRU5DWV9QQVlNRU5ULUlOX0NVUlJFTkNZX1RSQU5TRkVSX1dJREdFVCIsIlBBWU1FTlQtUkVGRVJFTkNFIiwiQUNDT1VOVElORy1JTlNVUkFOQ0VfT1dORVIiLCJNRVJDSEFOVC1SRVFVRVNUX1JFRlVORCIsIkNBUkRTLVZJRVdfQ0FSRF9OVU1CRVIiLCJQQVlNRU5ULVVQREFURV9EUkFGVCIsIlBBWU1FTlQtT1BFUkFUSU9OUyIsIlBBWU1FTlQtQ09ORklSTV9CRVRXRUVOX1lPVVJfQUNDT1VOVFMiLCJNRVJDSEFOVC1NQU5BR0VfREVMSVZFUlkiLCJDT1JFLVdSSVRFX0VNUExPWUVFIiwiUEFZTUVOVC1DT05GSVJNX01BU1NfVFJBTlNBQ1RJT05fRFJBRlQiLCJQQVlNRU5ULVNUQVRFTUVOVCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfVE9fU0lHTl9VTksiLCJQQVlNRU5ULUNSRUFURV9EUkFGVCIsIkNBUkRTLU9XTkVSX0FDVElWQVRFX0NBUkQiXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6ImRpcmVjdG9yU3ViIHByb2ZpbGUgZW1haWwgaWluIHBob25lIG1haW5BY2NvdW50SWQgY29tcGFueUlkZW50aWZpZXIiLCJwaG9uZU51bWJlciI6Iis3Nzc3OTAwMDAwMCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiY29tcGFueUlkZW50aWZpZXIiOiI5MTA4MTY0NTA3MDIiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJkOThkOTQzOS02YTA1LTRlYzItOGQ0MC00MTNiZWFkNmI4MTUiLCJtYWluQWNjb3VudElkIjoiNzJlOWFmMDUtYzE3My00NTQyLTk3NWYtZTZiOTViNjUxZjNhIiwiaWluIjoiOTEwODE2NDUwNzAyIn0.IZQlcKhdHawQ2ZyJ2i73K2oPMpdfqTvTLYlM--d3geafF-IuA48EX2ftJSBuQUAK09JXJBN17NtLVSvag-iYsDSBbcIDvdBH394AP2WTMwkG5N3QeXKF2c7CvG3M-SIZef14zydvmWvqzEhHPzrLqpzfSJbWe0oI4RekO-tTdVAaPGha-vjLbxQfPfJZMwtHP-TozGt3N3VJxISHs_kth-VktLxRnFCNjRkXAAift02dUxN7QBsGUBG42LuG3t7lX5kIcCgxpGzO059HPA0FnerzTTH8Gi5c0vGP_X9_Eo9l29Y9BwlBVFPQ8LR-reFG3aGSxOs8HXD-8F9IFP6AXA"
    )

    # 2. Генерация полностью случайного payload
    random_payload = generator.generate_random_payload(iban="KZ123456789")


    print(random_payload)