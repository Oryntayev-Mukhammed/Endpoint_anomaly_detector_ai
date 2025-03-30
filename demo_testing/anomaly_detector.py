# anomaly_detector.py
import requests
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random

from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score

import time

SERVER_URL = "http://127.0.0.1:5000"

# --- Автоэнкодер ---
class AutoEncoder(nn.Module):
    def __init__(self, input_dim=1, hidden_dim=8, bottleneck=2):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )
    
    def forward(self, x):
        z = self.encoder(x)
        out = self.decoder(z)
        return out

def train_autoencoder(model, data, epochs=100, lr=1e-3):
    model.train()
    X = torch.tensor(data, dtype=torch.float32).unsqueeze(1)  # [N,1]
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for _ in range(epochs):
        optimizer.zero_grad()
        recon = model(X)
        loss = criterion(recon, X)
        loss.backward()
        optimizer.step()

def eval_autoencoder(model, data):
    model.eval()
    X = torch.tensor(data, dtype=torch.float32).unsqueeze(1)  # [N,1]
    with torch.no_grad():
        recon = model(X)
    # MSE
    mse = (recon - X).pow(2).mean(dim=1).numpy()
    return mse

def main():
    # Шаг 1: Сбор данных
    all_data = []
    all_labels = []
    N = 30  # кол-во запросов
    batch_size = 20  # сколько точек за раз
    anomaly_rate = 0.08  # немного повысим шанс аномалий

    for i in range(N):
        # делаем GET-запрос
        url = f"{SERVER_URL}/data?n={batch_size}&anomaly_rate={anomaly_rate}"
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"[{i}] Ошибка {resp.status_code}: {resp.text}")
            continue
        out = resp.json()  # словарь {data: [...], labels: [...]}
        data_batch = out["data"]
        labels_batch = out["labels"]
        all_data.extend(data_batch)
        all_labels.extend(labels_batch)
        time.sleep(0.3)  # маленькая пауза
    
    all_data = np.array(all_data, dtype=np.float32)
    all_labels = np.array(all_labels, dtype=int)
    print(f"\nВсего собрано {len(all_data)} точек (из {N} запросов).")

    # Шаг 2: Автоэнкодер
    model = AutoEncoder(input_dim=1, hidden_dim=16, bottleneck=4)
    # Тренируем только на нормальных точках (label=0)
    normal_mask = (all_labels==0)
    normal_data = all_data[normal_mask]
    if len(normal_data) < 10:
        print("Слишком мало нормальных данных! Останов.")
        return

    train_autoencoder(model, normal_data, epochs=150, lr=1e-3)

    # Считаем MSE на всех точках
    mse_all = eval_autoencoder(model, all_data)
    # Ищем порог (например, 95-й перцентиль MSE нормальных точек)
    mse_normal = mse_all[normal_mask]
    threshold = np.percentile(mse_normal, 95)

    # Предсказание (0=normal,1=outlier)
    ypred_ae = (mse_all > threshold).astype(int)

    # Шаг 3: Isolation Forest
    X_2d = all_data.reshape(-1,1)
    iso = IsolationForest(n_estimators=100, contamination='auto', random_state=42)
    iso.fit(X_2d[normal_mask])  # обучаемся только на нормальных
    # Прогнозируем на всем датасете
    ypred_if = iso.predict(X_2d)
    # В sklearn: +1 = inlier, -1 = outlier
    ypred_if = np.where(ypred_if==-1, 1, 0)  # Переводим в (0,1) как наши labels

    # Шаг 4: Метрики
    # Для AE
    precision_ae = precision_score(all_labels, ypred_ae)
    recall_ae = recall_score(all_labels, ypred_ae)
    f1_ae = f1_score(all_labels, ypred_ae)

    # Для IF
    precision_if = precision_score(all_labels, ypred_if)
    recall_if = recall_score(all_labels, ypred_if)
    f1_if = f1_score(all_labels, ypred_if)

    # Шаг 5: Вывод результатов
    print("\n----- РЕЗУЛЬТАТЫ АНОМАЛИИ -----")
    print(f"В реальности: {sum(all_labels)} / {len(all_labels)} (≈ {100*sum(all_labels)/len(all_labels):.2f}%) аномалий.")
    print("AutoEncoder threshold =", threshold)
    print(f"AE => Precision={precision_ae:.3f}, Recall={recall_ae:.3f}, F1={f1_ae:.3f}")
    print(f"IF => Precision={precision_if:.3f}, Recall={recall_if:.3f}, F1={f1_if:.3f}")

    # Пример просмотра некоторых (точка, label, mse)
    # Сортируем по mse
    idx_sorted = np.argsort(mse_all)[::-1]  # по убыванию MSE
    top5_idx = idx_sorted[:5]
    print("\nТоп-5 MSE (AE):")
    for i, idx in enumerate(top5_idx):
        val = all_data[idx]
        lab = all_labels[idx]
        print(f"{i+1}) point={val:.2f}, label={lab}, MSE={mse_all[idx]:.3f}")

if __name__ == "__main__":
    main()
