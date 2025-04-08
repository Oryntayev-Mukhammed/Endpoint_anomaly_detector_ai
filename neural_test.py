import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

from feature_extractor import PaymentFeatureExtractor
from generate_ideal_transactionDetail import generate_ideal_output
from services.models import PaymentPayload, TransactionDetail

def load_json_file(file_path):
    """Загрузка JSON файла с обработкой кодировки"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='cp1251') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Не удалось загрузить файл {file_path}. Ошибка: {str(e)}")

class PaymentDataset(Dataset):
    def __init__(self, payloads, transactions):
        self.payloads = payloads
        self.transactions = transactions
        
    def __len__(self):
        return len(self.payloads)
    
    def __getitem__(self, idx):
        payload_vec = PaymentFeatureExtractor.payload_to_vector(self.payloads[idx])['vector']
        transaction_vec = PaymentFeatureExtractor.transaction_to_vector(self.transactions[idx])['vector']
        return torch.FloatTensor(payload_vec), torch.FloatTensor(transaction_vec)

class PaymentAutoencoder(nn.Module):
    def __init__(self, input_size=21, hidden_size=64, output_size=37):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size//2),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(hidden_size//2, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )
        self.anomaly_scorer = nn.Sequential(
            nn.Linear(hidden_size//2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        anomaly_score = self.anomaly_scorer(encoded)
        return decoded, anomaly_score

def train_model():
    # 1. Загрузка и подготовка данных
    try:
        data = load_json_file('successful_payloads.json')
        payloads = [PaymentPayload.from_dict(item) for item in data]
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return None
    
    # Генерация идеальных транзакций
    transactions = [TransactionDetail.from_dict(generate_ideal_output(payload.to_dict(), is_payload=True)) for payload in payloads]
    
    # 2. Разделение данных
    X = [PaymentFeatureExtractor.payload_to_vector(p)['vector'] for p in payloads]
    y = [PaymentFeatureExtractor.transaction_to_vector(t)['vector'] for t in transactions]
    
    # 2. Создаём список индексов
    indices = list(range(len(X)))

    # 3. Разделяем именно индексы, а не данные
    train_indices, val_indices = train_test_split(indices, test_size=0.2, random_state=42)

    # 4. Формируем X_train, X_val, y_train, y_val (если нужно)
    X_train = [X[i] for i in train_indices]
    y_train = [y[i] for i in train_indices]
    X_val   = [X[i] for i in val_indices]
    y_val   = [y[i] for i in val_indices]

    # 5. Создаём датасеты
    train_dataset = PaymentDataset(
        [payloads[i] for i in train_indices],
        [transactions[i] for i in train_indices]
    )
    val_dataset = PaymentDataset(
        [payloads[i] for i in val_indices],
        [transactions[i] for i in val_indices]
    )
    
    # 3. Создание модели и обучение
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PaymentAutoencoder().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    reconstruction_loss = nn.MSELoss()
    anomaly_loss = nn.BCELoss()
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    
    min_train_loss = 10000.0
    best_model = None

    for epoch in range(500):
        model.train()
        train_loss = 0
        for payload, target in train_loader:
            payload, target = payload.to(device), target.to(device)
            
            optimizer.zero_grad()
            decoded, anomaly_score = model(payload)
            
            rec_loss = reconstruction_loss(decoded, target)
            anom_loss = anomaly_loss(anomaly_score, torch.zeros_like(anomaly_score))
            loss = rec_loss + anom_loss
            
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # Валидация
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for payload, target in val_loader:
                payload, target = payload.to(device), target.to(device)
                decoded, anomaly_score = model(payload)
                val_loss += reconstruction_loss(decoded, target).item()
        if train_loss < min_train_loss:
            min_train_loss = train_loss
            best_model = model
            if epoch % 100 == 0: 
                torch.save(best_model.state_dict(), f'models/payment_autoencoder_{train_loss/len(train_loader):.4f}.pth')
        print(f'Epoch {epoch+1}: Train Loss: {train_loss/len(train_loader):.4f}, Val Loss: {val_loss/len(val_loader):.4f}')
    
    return model

if __name__ == "__main__":
    # Проверяем доступность файла
    try:
        with open('successful_payloads.json', 'r', encoding='utf-8') as f:
            pass
        print("Файл successful_payloads.json доступен для чтения")
    except Exception as e:
        print(f"Ошибка доступа к файлу: {e}")
        exit(1)
    
    # Запускаем обучение
    trained_model = train_model()
    if trained_model:
        print("Модель успешно обучена")