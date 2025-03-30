import streamlit as st
import requests
import json
import uuid
import random
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import time

st.set_page_config(layout="wide")
st.title("💳 Платежи в бюджет — Налоги компании (с расчётом комиссии)")

# Проверка токена
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

st.markdown("---")
st.header("Настройки платежа")

# Размещаем поля и чекбоксы для фиксации в одной строке
col1, col2 = st.columns([2,1])
with col1:
    base_amount = st.number_input("Сумма платежа", 100.0, 1000000.0, 1000.0)
with col2:
    fix_amount = st.checkbox("Фиксировать сумму", value=True)

col3, col4 = st.columns([2,1])
with col3:
    base_purpose = st.text_input("Назначение", knp['knpName'])
with col4:
    fix_purpose = st.checkbox("Фиксировать назначение", value=True)

col5, col6 = st.columns([2,1])
with col5:
    base_period = st.date_input("Период", value=date.today().replace(day=1) - relativedelta(months=1))
with col6:
    fix_period = st.checkbox("Фиксировать период", value=True)

# BIN если требуется
bin_code = None
if kbk.get("ugdLoadingRequired"):
    ugd_options = {f"{u['name']} ({u['code']})": u for u in ugd_list}
    ugd_selected = st.selectbox("Выберите УГД", list(ugd_options.keys()))
    bin_code = ugd_options[ugd_selected]["bin"]

st.markdown("---")
st.header("🔄 Итерационное тестирование")

# Настройки итераций
iterations = st.number_input("Количество итераций", value=100, step=1, key="iterations")

# Контейнер для динамической таблицы и текстового прогресса
progress_text = st.empty()
progress_bar = st.progress(0)
table_placeholder = st.empty()

if st.button("Запустить итерационные тесты"):
    results = []
    for i in range(iterations):
        # Обновляем текст прогресса
        progress_text.text(f"Итерация {i+1} из {iterations}")
        
        # Генерируем уникальный transactionId для итерации
        iter_transaction_id = f"APP_INDNTRTAX_{uuid.uuid4()}"
        
        # Используем фиксированные или случайные значения
        iter_amount = base_amount if fix_amount else round(random.uniform(100.0, 1000000.0), 2)
        iter_purpose = base_purpose if fix_purpose else f"{base_purpose}_{random.randint(1000, 9999)}"
        iter_period = base_period.isoformat() if fix_period else (base_period + relativedelta(days=random.randint(-10, 10))).isoformat()
        
        # Формируем payload
        iter_payload = {
            "transactionId": iter_transaction_id,
            "ibanDebit": iban_debit,
            "amount": iter_amount,
            "kbk": {
                "name": kbk["name"],
                "code": kbk["code"],
                "employeeLoadingRequired": kbk["employeeLoadingRequired"],
                "ugdLoadingRequired": kbk["ugdLoadingRequired"]
            },
            "knp": knp["knpCode"],
            "purpose": iter_purpose,
            "period": iter_period,
            "taxesPaymentOperationType": selected_operation_type
        }
        if bin_code:
            iter_payload["bin"] = bin_code

        # Расчёт комиссии
        commission_payload = [{
            "transactionId": iter_transaction_id,
            "transactionAmount": iter_amount,
            "currency": "KZT",
            "urgent": False,
            "futureValueDate": False
        }]
        try:
            commission_url = f"{base_url}/api/charge-calculator/api/v1/charges/trn/multi-calculate"
            commission_resp = requests.put(commission_url, headers=headers, json=commission_payload, verify=False)
            commission_resp.raise_for_status()
            commission_status = commission_resp.status_code
            commission_text = commission_resp.text
        except Exception as e:
            commission_status = None
            commission_text = str(e)
        
        # Отправка платежа
        try:
            payment_url = f"{base_url}/api/payment/api/v5/budget/init/entrepreneur"
            payment_resp = requests.post(payment_url, headers=headers, json=iter_payload, verify=False)
            payment_resp.raise_for_status()
            payment_status = payment_resp.status_code
            payment_text = payment_resp.text
        except Exception as e:
            payment_status = None
            payment_text = str(e)
        
        results.append({
            "Итерация": i+1,
            "TransactionID": iter_transaction_id,
            "Amount": iter_amount,
            "Purpose": iter_purpose,
            "Period": iter_period,
            "Commission Status": commission_status,
            "Payment Status": payment_status,
            "Commission Response": commission_text,
            "Payment Response": payment_text
        })
        progress_bar.progress((i+1) / iterations)
        # Обновляем динамическую таблицу после каждой итерации
        df_results = pd.DataFrame(results)
        
        # Функция для окрашивания ячеек по статусу
        def color_status(val):
            try:
                if 200 <= int(val) < 300:
                    color = 'green'
                else:
                    color = 'red'
            except:
                color = 'orange'
            return f'color: {color}'

        styled_df = df_results.style.applymap(color_status, subset=['Commission Status', 'Payment Status'])
        table_placeholder.dataframe(styled_df, height=500)
        # Добавим небольшую задержку для наглядности обновления (не обязательно)
        time.sleep(0.1)
    
    progress_text.text("Итерационные тесты завершены.")
