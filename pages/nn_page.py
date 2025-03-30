import streamlit as st
import requests
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import datetime

st.set_page_config(layout="wide")
st.title("💳 Платежи в бюджет — Налоги компании (с расчётом комиссии)")

# ------------------------
# Часть с запросами к API (как у вас в приложении)
# ------------------------

if 'token' not in st.session_state:
    st.error("⚠️ Введите токен на главной странице.")
    st.stop()

base_url = st.text_input("Базовый URL", "https://sme-bff.kz.infra")
headers = {
    "Authorization": f"Bearer {st.session_state['token']}",
    "Content-Type": "application/json"
}

@st.cache_data
def fetch_api_data(endpoint):
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка запроса к {endpoint}: {e}")
        return {}

# Получение счетов
accounts_data = fetch_api_data("/api/account/accounts")
valid_accounts = [
    acc for acc in accounts_data.get("accounts", [])
    if acc.get("accountStatus") == "OPEN" and not acc.get("fullyBlocked", True)
]

if not valid_accounts:
    st.error("⚠️ Нет доступных счетов для списания.")
    st.stop()

iban_options = {
    f"{acc['iban']} — {acc['availableBalance']} {acc['currency']}": acc["iban"]
    for acc in valid_accounts
}
selected_iban_label = st.selectbox("💼 Выберите счёт списания", list(iban_options.keys()))
iban_debit = iban_options[selected_iban_label]

# Справочники
selected_operation_type = "INDIVIDUAL_ENTREPRENEUR"
ugd_list = fetch_api_data("/api/dictionary/dictionary/ugd/all")
kbk_list = fetch_api_data(f"/api/dictionary/dictionary/kbk/kbk-to-knp-list?taxesPaymentOperationType={selected_operation_type}")

if not kbk_list:
    st.stop()

kbk_options = {f"{i['name']} ({i['code']})": i for i in kbk_list}
kbk_selected = st.selectbox("Выберите KBK", list(kbk_options.keys()))
kbk = kbk_options[kbk_selected]

knp_options = {f"{k['knpName']} ({k['knpCode']})": k for k in kbk['knpList']}
knp_selected = st.selectbox("Выберите KNP", list(knp_options.keys()))
knp = knp_options[knp_selected]

# Остальные поля платежа
transaction_id = f"APP_INDNTRTAX_{uuid.uuid4()}"
amount = st.number_input("Сумма платежа", 100.0, 1000000.0, 1000.0)
purpose = st.text_input("Назначение", knp['knpName'])
period = st.date_input("Период", value=date.today().replace(day=1) - relativedelta(months=1))

# BIN, если требуется
bin_code = None
if kbk.get("ugdLoadingRequired"):
    ugd_options = {f"{u['name']} ({u['code']})": u for u in ugd_list}
    ugd_selected = st.selectbox("Выберите УГД", list(ugd_options.keys()))
    bin_code = ugd_options[ugd_selected]["bin"]

if st.button("📊 Рассчитать комиссию и отправить платёж"):
    commission_payload = [{
        "transactionId": transaction_id,
        "transactionAmount": amount,
        "currency": "KZT",
        "urgent": False,
        "futureValueDate": False
    }]
    try:
        commission_url = f"{base_url}/api/charge-calculator/api/v1/charges/trn/multi-calculate"
        resp = requests.put(commission_url, headers=headers, json=commission_payload, verify=False)
        resp.raise_for_status()
        st.success("✅ Комиссия успешно рассчитана")
        st.json(resp.json())
    except Exception as e:
        st.error("❌ Ошибка при расчёте комиссии:")
        st.text(e)
        st.stop()

    # Собираем payload платежа
    payload = {
        "transactionId": transaction_id,
        "ibanDebit": iban_debit,
        "amount": amount,
        "kbk": {
            "name": kbk["name"],
            "code": kbk["code"],
            "employeeLoadingRequired": kbk["employeeLoadingRequired"],
            "ugdLoadingRequired": kbk["ugdLoadingRequired"]
        },
        "knp": knp["knpCode"],
        "purpose": purpose,
        "period": period.isoformat(),
        "taxesPaymentOperationType": selected_operation_type
    }
    if bin_code:
        payload["bin"] = bin_code

    st.subheader("📦 Payload платежа")
    st.json(payload)

    try:
        response = requests.post(f"{base_url}/api/payment/api/v5/budget/init/entrepreneur", headers=headers, json=payload, verify=False)
        response.raise_for_status()
        st.success("✅ Платёж успешно отправлен!")
        st.json(response.json())
    except requests.exceptions.RequestException as e:
        st.error("❌ Ошибка выполнения платежа:")
        if e.response is not None:
            st.text(e.response.text)
        else:
            st.text(e)
    
    # Сохраним payload для анализа нейросетью
    st.session_state.last_payload = payload

# ------------------------
# ML-детектор аномалий: генерация идеальных данных и обучение модели
# ------------------------

st.header("🤖 Детектор аномалий (ML)")

# Определяем автоэнкодер для входного вектора
class Autoencoder(nn.Module):
    def __init__(self, input_dim):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16)
        )
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

# Функция преобразования payload в числовой вектор.
# В этом примере берем 4 признака: amount, период (timestamp), kbk.code (как число) и длину purpose.
def payload_to_vector(payload, input_dim=10):
    amount = payload.get("amount", 0.0)
    period_str = payload.get("period", None)
    if period_str:
        try:
            period_dt = datetime.datetime.fromisoformat(period_str)
            period_val = period_dt.timestamp()  # преобразуем дату в секунды
        except Exception:
            period_val = 0.0
    else:
        period_val = 0.0
    kbk = payload.get("kbk", {})
    kbk_code = kbk.get("code", "0")
    try:
        kbk_val = float(kbk_code)
    except:
        kbk_val = sum([ord(c) for c in kbk_code]) / 1000.0
    purpose = payload.get("purpose", "")
    purpose_len = len(purpose)
    vec = [amount, period_val, kbk_val, purpose_len]
    # Если размерность меньше input_dim, дополним нулями.
    vec += [0.0] * (input_dim - len(vec))
    return torch.tensor(vec, dtype=torch.float32)

# Функция генерации идеального (нормального) payload на основе вашей формы
def generate_ideal_payload():
    tid = f"APP_INDNTRTAX_{uuid.uuid4()}"
    iban = "KZ" + "".join(np.random.choice(list("0123456789"), size=18))
    amount = np.random.uniform(100.0, 1000000.0)
    # Генерируем kbk с кодом из 6 цифр
    code = str(np.random.randint(100000, 999999))
    kbk = {
         "name": "KBK-" + code,
         "code": code,
         "employeeLoadingRequired": np.random.choice([True, False]),
         "ugdLoadingRequired": np.random.choice([True, False])
    }
    # knp (не используется в векторизации, но добавляем)
    knp = str(np.random.randint(100, 999))
    purpose_options = [
        "Налог на прибыль", 
        "НДС", 
        "Социальный налог", 
        "Акцизный сбор", 
        "Платеж за услуги"
    ]
    purpose = np.random.choice(purpose_options)
    # Период: случайная дата за последние 2 года
    start_date = date.today() - relativedelta(years=2)
    random_days = np.random.randint(0, 365*2)
    period_date = start_date + timedelta(days=int(random_days))
    period_str = period_date.isoformat()
    taxesPaymentOperationType = "INDIVIDUAL_ENTREPRENEUR"
    payload = {
         "transactionId": tid,
         "ibanDebit": iban,
         "amount": amount,
         "kbk": kbk,
         "knp": knp,
         "purpose": purpose,
         "period": period_str,
         "taxesPaymentOperationType": taxesPaymentOperationType
    }
    if kbk["ugdLoadingRequired"]:
         payload["bin"] = str(np.random.randint(100000000, 999999999))
    return payload

# Генерируем набор обучающих примеров из идеальных payload'ов
def generate_training_data_from_payloads(num_samples=1000, input_dim=10):
    vectors = []
    for _ in range(num_samples):
        p = generate_ideal_payload()
        vec = payload_to_vector(p, input_dim=input_dim)
        vectors.append(vec.unsqueeze(0))
    return torch.cat(vectors, dim=0)

# Функция обучения автоэнкодера
def train_autoencoder(model, data, epochs=20, batch_size=32, learning_rate=0.001):
    dataset = TensorDataset(data)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    for epoch in range(epochs):
        running_loss = 0.0
        for batch in dataloader:
            inputs = batch[0]
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, inputs)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)
        epoch_loss = running_loss / len(dataset)
        st.write(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.4f}")
    return model

# Функция для вычисления аномальности: среднеквадратичная ошибка между входным вектором и его восстановлением
def compute_anomaly_score(model, input_vector):
    model.eval()
    with torch.no_grad():
        reconstructed = model(input_vector)
        loss = nn.functional.mse_loss(reconstructed, input_vector, reduction='mean')
    return loss.item()

# Задаем размерность входного вектора (например, 10 признаков)
INPUT_DIM = 10

st.sidebar.header("ML Детектор аномалий")

# Кнопка обучения модели на идеальных (синтетических) данных, сгенерированных по вашей форме
if st.sidebar.button("Обучить модель на идеальных данных"):
    st.sidebar.write("Генерация обучающих данных и обучение автоэнкодера...")
    training_data = generate_training_data_from_payloads(num_samples=1000, input_dim=INPUT_DIM)
    model = Autoencoder(input_dim=INPUT_DIM)
    trained_model = train_autoencoder(model, training_data, epochs=200)
    st.session_state.autoencoder_model = trained_model
    st.sidebar.success("Модель обучена!")

# Если модель уже обучена и имеется последний payload, оцениваем аномальность
if "autoencoder_model" in st.session_state:
    st.sidebar.subheader("Анализ текущего запроса")
    if "last_payload" in st.session_state:
        vec = payload_to_vector(st.session_state.last_payload, input_dim=INPUT_DIM)
        vec = vec.unsqueeze(0)  # добавляем размер батча = 1
        anomaly_score = compute_anomaly_score(st.session_state.autoencoder_model, vec)
        st.sidebar.write(f"Аномалия (MSE): {anomaly_score:.4f}")
        # Задаем порог для аномалии (подберите опытным путем)
        if anomaly_score > 0.5:
            st.sidebar.error("Запрос выглядит аномальным!")
        else:
            st.sidebar.success("Запрос в норме.")
    else:
        st.sidebar.info("Payload для анализа еще не сформирован.")
else:
    st.sidebar.info("Обучите модель для анализа аномалий.")
