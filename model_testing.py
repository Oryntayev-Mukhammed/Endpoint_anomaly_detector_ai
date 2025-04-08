import numpy as np
import torch
import torch.nn as nn

from feature_extractor import PaymentFeatureExtractor
from services.models import PaymentPayload, TransactionDetail
from neural_test import PaymentAutoencoder
from services.transaction_service import TransactionService  # или импортируйте тот же класс откуда нужно


def load_trained_model(model_path: str) -> PaymentAutoencoder:
    """
    Загружает обученную модель из model_path в PaymentAutoencoder.
    """
    # 1. Создаём экземпляр модели с теми же гиперпараметрами, что при обучении
    model = PaymentAutoencoder(input_size=21, hidden_size=64, output_size=37)
    
    # 2. Загружаем веса из pth-файла
    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
    model.load_state_dict(state_dict)
    
    # 3. Переключаем модель в режим "eval", чтобы отключить dropout/batchnorm (если есть)
    model.eval()
    
    return model

def predict(payload_data: dict, model: PaymentAutoencoder):
    """
    Принимает словарь payload_data (или PaymentPayload.to_dict()),
    подготавливает вход, прогоняет через модель и возвращает:
      - decoded (реконструированный вектор)
      - anomaly_score (риск аномалии)
    """
    # 1. Преобразуем payload в вектор
    input_vector = PaymentFeatureExtractor.payload_to_vector(PaymentPayload.from_dict(payload_data))['vector']  # длина 21
    # 2. Превращаем в тензор (в виде батча из 1 примера)
    input_tensor = torch.FloatTensor(input_vector).unsqueeze(0)  # [1, 21]
    
    # 3. Прогоняем через модель
    with torch.no_grad():  # в режиме предсказания не нужны градиенты
        decoded, anomaly_score = model(input_tensor)
    
    # decoded: shape [1, 37]   anomaly_score: shape [1, 1]
    # Извлекаем из батча
    decoded = decoded.squeeze(0).numpy()        # -> shape [37]
    anomaly_score = anomaly_score.squeeze(0).item()  # -> число типа float
    
    return decoded, anomaly_score

if __name__ == "__main__":
    # 1) Грузим модель
    trained_model = load_trained_model("models/payment_autoencoder_0.0801.pth")

    # 2) Инициализируем сервис
    TEST_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6b1RlN1Z5UXFta0JrMktxbXg0QWlaR0lFZGZCcDFjbFZmZXk1TS1Vc1FzIn0.eyJleHAiOjE3NDQxMTU5NjIsImlhdCI6MTc0NDExNDE2MiwianRpIjoiNDNiOThmZTMtZjg1Mi00ZDFiLTkyNmYtMzY4MzA4MWJjZjA3IiwiaXNzIjoiaHR0cDovL2hjYi1wbGF0Zm9ybS1rZXljbG9hay5rejAwYzEtc21lLXBsYXRmb3JtL2tleWNsb2FrL3JlYWxtcy9ob21lLWNyZWRpdC1pbnRlcm5ldC1iYW5raW5nLXJlYWxtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjkyOThiYzc0LTUwNWEtNDYyNy05YmU1LWZkMDRiZDQ4NWU2YSIsInR5cCI6IkJlYXJlciIsImF6cCI6ImhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcGxhdGZvcm0iLCJzaWQiOiIwZmZjYjFlYi03OTYxLTQwNWEtODI4Yi04M2U2NWZhZDkyZTQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIi8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJDT1JFLVJFQURfQUNDT1VOVF9SRVFVSVNJVEVTIiwiQ1VSUkVOQ1lfUEFZTUVOVC1TSUdOX0VEU19PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1dJREdFVCIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fREVUQUlMUyIsIlBBWU1FTlQtQlVER0VUX1BBWU1FTlRTIiwiREVQT1NJVC1PV05FUiIsIlBBWU1FTlQtQ09OVkVSU0lPTiIsIkNPUkUtV1JJVEVfQUNDT1VOVCIsIk1FUkNIQU5ULVZJRVdfU0FMRVNST09NIiwiUEFZTUVOVC1DT05GSVJNX09UUCIsIlRBUklGRi1PV05FUiIsIlBBWU1FTlQtQkVUV0VFTl9ZT1VSX0FDQ09VTlRTIiwiQ0FSRFMtT1dORVJfU0VUX1RSQU5TQUNUSU9OX0xJTUlUUyIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9DT05WRVJTSU9OIiwiTUFOQUdFUiIsIlBBWU1FTlQtQ09ORklSTV9FRFMiLCJQQVlNRU5ULVJFUVVJU0lURVNfVFJBTlNGRVIiLCJ1bWFfYXV0aG9yaXphdGlvbiIsIkNBUkRTLVZJRVdfQ0FSRF9BQ0NPVU5UX0RFVEFJTFMiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX0VESVQiLCJDQVJEUy1PV05FUl9TRVRfUElOIiwiQUNDT1VOVElORy1PV05FUiIsIkNBUkRTLU9XTkVSX09QRU5fQ0FSRCIsIkNBUkRTLU9XTkVSX1BFUk1BTkVOVF9MSU1JVFMiLCJQQVlNRU5ULUNPTlRSQUNUX09QRVJBVElPTlMiLCJBQ0NPVU5USU5HLUlOU1VSQU5DRV9BTEwiLCJDQVJEUy1WSUVXX0NBUkRfQUNDT1VOVCIsIlBBWU1FTlQtRk9SU0lHTiIsIlBBWU1FTlQtUkVWSUVXX0RSQUZUIiwiRUNPTS1XUklURVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX0NMT1NFIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT1VOVEVSUEFSVFlfVklFVyIsIk1FUkNIQU5ULUNSRUFURV9VUERBVEVfU0FMRVNST09NIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9TSUdOX09UUF9VTksiLCJDVVJSRU5DWV9QQVlNRU5ULVNJR05fT1RQX0lOX0NVUlJFTkNZX1RSQU5TRkVSIiwiQ0FSRFMtVklFV19DQVJEX0NWViIsIkNVUlJFTkNZX1BBWU1FTlQtQ09VTlRFUlBBUlRZX0RFTEVURSIsIlBBWU1FTlQtRFJBRlQiLCJDVVJSRU5DWV9QQVlNRU5ULVNJR05fT1RQX09VVF9DVVJSRU5DWV9UUkFOU0ZFUiIsIlBBWU1FTlQtVFJBTlNBQ1RJT05fRkVFRCIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9PVVRfQ1VSUkVOQ1lfVFJBTlNGRVIiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9FRElUIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05UUkFDVF9DRVJUSUZJQ0FURSIsIlBBWU1FTlQtQ09ORklSTV9SRVFVSVNJVEVTX1RSQU5TRkVSIiwiUEFZTUVOVC1DVVJSRU5DWV9UUkFOU0ZFUiIsIlBBWU1FTlQtUkVDRUlWSU5HX1BBWU1FTlQiLCJkZWZhdWx0LXJvbGVzLWhvbWUtY3JlZGl0LWludGVybmV0LWJhbmtpbmctcmVhbG0iLCJNRVJDSEFOVC1WSUVXX0NPTk5FQ1QiLCJDT1JFLVJFQURfQUNDT1VOVCIsIlBBWU1FTlQtU0lHTklORyIsIkNPUkUtUkVBRF9DT01QQU5ZIiwiUEFZTUVOVC1ERUxFVEVfRFJBRlQiLCJvZmZsaW5lX2FjY2VzcyIsIlBBWU1FTlQtTUFTU19UUkFOU0FDVElPTl9EUkFGVCIsIk1FUkNIQU5ULVZJRVdfSElTVE9SWSIsIkNVUlJFTkNZX1BBWU1FTlQtSU5JVF9JTl9DVVJSRU5DWV9UUkFOU0ZFUiIsIk1FUkNIQU5ULVZJRVdfU0FMRVNST09NX0RFVEFJTFMiLCJDQVJEUy1PV05FUl9CTE9DS19VTkJMT0NLX0NBUkQiLCJDVVJSRU5DWV9QQVlNRU5ULUNPVU5URVJQQVJUWV9DUkVBVEUiLCJQQVlNRU5ULUNPTkZJUk1fUkVGRVJFTkNFIiwiUEFZTUVOVC1UUkFOU0FDVElPTl9EUkFGVCIsImRlZmF1bHQtcGVybWlzc2lvbiIsIlBBWU1FTlQtQ09ORklSTV9TVEFURU1FTlQiLCJDVVJSRU5DWV9QQVlNRU5ULVNJR05fT1RQX0NPTlZFUlNJT04iLCJQQVlNRU5ULUNPTkZJUk1fQlVER0VUX1BBWU1FTlRTIiwiQ1VSUkVOQ1lfUEFZTUVOVC1DT05WRVJTSU9OX1dJREdFVCIsIkNVUlJFTkNZX1BBWU1FTlQtQ09OVFJBQ1RfQ1JFQVRFIiwiQ1VSUkVOQ1lfUEFZTUVOVC1JTl9DVVJSRU5DWV9UUkFOU0ZFUl9XSURHRVQiLCJQQVlNRU5ULVJFRkVSRU5DRSIsIk1FUkNIQU5ULVJFUVVFU1RfUkVGVU5EIiwiQ0FSRFMtVklFV19DQVJEX05VTUJFUiIsIlBBWU1FTlQtVVBEQVRFX0RSQUZUIiwiUEFZTUVOVC1PUEVSQVRJT05TIiwiUEFZTUVOVC1DT05GSVJNX0JFVFdFRU5fWU9VUl9BQ0NPVU5UUyIsIk1FUkNIQU5ULU1BTkFHRV9ERUxJVkVSWSIsIlBBWU1FTlQtQ09ORklSTV9NQVNTX1RSQU5TQUNUSU9OX0RSQUZUIiwiUEFZTUVOVC1TVEFURU1FTlQiLCJDVVJSRU5DWV9QQVlNRU5ULUNPTlRSQUNUX1RPX1NJR05fVU5LIiwiUEFZTUVOVC1DUkVBVEVfRFJBRlQiLCJDQVJEUy1PV05FUl9BQ1RJVkFURV9DQVJEIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJkaXJlY3RvclN1YiBwcm9maWxlIGVtYWlsIGlpbiBwaG9uZSBtYWluQWNjb3VudElkIGNvbXBhbnlJZGVudGlmaWVyIiwicGhvbmVOdW1iZXIiOiIrNzcwMTQ0MDAzMzEiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNvbXBhbnlJZGVudGlmaWVyIjoiODUwODI0NDAwNzk2IiwiZGlyZWN0b3JTdWIiOiIyM2E5NjdmMS03ZmM3LTQzMWQtYTQ1MC0xMjg2ZDQ0Y2E5ODIiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIyZmVjN2I4NC0xZDg5LTQyYjgtYjI1NS01MDEwZmNjMjNhOTYiLCJtYWluQWNjb3VudElkIjoiMTkxNWE4NTAtODY4Mi00OWU4LTg1YWQtOWRhMzkzOTMxOTA0IiwiaWluIjoiOTgwMTA0NDAwMzMxIn0.nMQ6Peba1SHW7JMpHVszvqI7aohioMilIvGyGKzgNNETzbWH8VF5k5ce6nWNA1_SVsbz5kL7FZ8PaB5bJZzZ8c_Bxr24R_Y-f1WHQeKsk8lqxIMXjfUxCuDOWSBDZJcYjtpuX8BHKLmG4S214nzdOptS6EWbgMUY9U956kxCFb-usBPiR586BQXITNNyQJ4DXOVOrIb7l5bHJ8qlaVnIGMAYeNVtzdQd2gUVe1B7ncSJu5k3y6kCLzyW51PehJIGR9XBw7DcaFEHMakgA41DV6MxbyUzkPvDJNz79O34Va3NxqWdmWbN4gdi5OEqPV4c1UAWgXrjxwD8_I7wxG-_6w"
    TEST_BASE_URL = "https://sme-bff.kz.infra"
    service = TransactionService(TEST_BASE_URL, TEST_TOKEN)

    # 3) ПРИМЕР ПОЛУЧЕНИЯ "РЕАЛЬНОЙ" ТРАНЗАКЦИИ по её transactionId
    tx_id = "APP_INDNTRTAX_e88e2dd0-1470-11f0-bd44-5f22d257584b"
    real_tx_data = service.get_transaction_details_by_transaction_id(tx_id)
    # Здесь real_tx_data — это dict. Если у вас есть метод, который сразу даёт объект TransactionDetail, можно взять его.
    # Или, если вы уже делаете TransactionDetail.from_dict(...), тогда:
    # transaction_detail_obj = TransactionDetail.from_dict(real_tx_data)

    if not real_tx_data:
        print(f"Транзакция {tx_id} не найдена на сервере!")
        exit(0)

    # 4) Превратим реальную транзакцию (dict) в объект TransactionDetail (если нужно)
    #    и/или вектор
    transaction_detail = TransactionDetail.from_dict(real_tx_data)
    paymerFeatureExt = PaymentFeatureExtractor()
    actual_vec = paymerFeatureExt.transaction_to_vector(transaction_detail)['vector']  # длина 37

    # 5) Предскажем «идеальный» вектор через модель, используя payload (имитация входа)
    #    Предположим, что payload_data совпадает или примерно совпадает с тем, что могло вызвать эту транзакцию
    test_payload = {
        "transactionId": "APP_INDNTRTAX_e88e2dd0-1470-11f0-bd44-5f22d257584b",
        "ibanDebit": "KZ81886A220120720370",
        "amount": 1000.0,
        "kbk": {
            "name": "Бонусы от организаций нефтяного сектора",
            "code": 105325,
            "employeeLoadingRequired": False,
            "ugdLoadingRequired": True
        },
        "ugd": {
            "name": "РГУ \"УГД по Айтекебийскому району ДГД по Актюбинской области КГД МФ РК\"",
            "bin": "980540000971",
            "code": "121312"
        },
        "knp": "911",
        "purpose": "Основное",
        "year": 2024,
        "quarter": "SECOND",
        "timestamp": "2025-04-03T19:38:21.798734"
    }

    decoded_vec, anomaly_score = predict(test_payload, trained_model)

    print(decoded_vec)
    print(actual_vec)
    # 6) Считаем, насколько предсказанный вектор (decoded_vec) отличается от реального (actual_vec)
    reconstruction_error = np.mean((decoded_vec - actual_vec) ** 2)  # MSE пример

    print("----- Результаты -----")
    print("1) anomaly_score (из модели):", anomaly_score)
    print("2) Ошибка реконструкции (MSE) :", reconstruction_error)

    # 7) Логика принятия решения об аномалии
    #    Можно условно задать пороги
    anomaly_threshold_score = 0.5   # выше -> аномалия
    anomaly_threshold_mse   = 0.01  # зависит от масштаба фичей

    is_anomaly = (anomaly_score > anomaly_threshold_score) or (reconstruction_error > anomaly_threshold_mse)

    print(f"\nЯвляется ли транзакция {tx_id} аномальной? -> {is_anomaly}\n")