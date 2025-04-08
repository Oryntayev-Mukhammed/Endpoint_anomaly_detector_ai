import torch
import torch.nn as nn

from feature_extractor import PaymentFeatureExtractor
from services.models import PaymentPayload
from neural_test import PaymentAutoencoder  # или импортируйте тот же класс откуда нужно


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
    # Пример: грузим модель
    trained_model = load_trained_model("models/payment_autoencoder_0.0801.pth")
    
    # Пример payload (словарь). Можно использовать PaymentPayload.from_dict(...).to_dict()
    # если нужно
    test_payload = {  
        "transactionId": "APP_INDNTRTAX_cd0febf0-144f-11f0-bd44-5f22d257584b",
        "ibanDebit": "KZ81886A220120720370",
        "amount": 1000.0,
        "kbk": {
            "name": "СО в свою пользу",
            "code": 902101,
            "employeeLoadingRequired": False,
            "ugdLoadingRequired": False
        },
        "knp": "012",
        "purpose": "Основное",
        "period": "2025-01-01",
        "timestamp": "2025-04-03T19:38:21.798734"
    }

    # Предикт
    decoded_vec, anomaly_score = predict(test_payload, trained_model)
    print("Decoded vector:", decoded_vec)
    print("Anomaly score:", anomaly_score)
