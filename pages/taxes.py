import streamlit as st
import requests
import json
from datetime import date
from dateutil.relativedelta import relativedelta
import uuid

st.set_page_config(layout="wide")
st.title("💳 Платежи в бюджет — Налоги компании (с расчётом комиссии)")

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
        return []

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
selected_iban_label = st.selectbox("💼 Выберите счёт списания", iban_options.keys())
iban_debit = iban_options[selected_iban_label]

# Справочники
selected_operation_type = "INDIVIDUAL_ENTREPRENEUR"
ugd_list = fetch_api_data("/api/dictionary/dictionary/ugd/all")
kbk_list = fetch_api_data(f"/api/dictionary/dictionary/kbk/kbk-to-knp-list?taxesPaymentOperationType={selected_operation_type}")

if not kbk_list:
    st.stop()

kbk_options = {f"{i['name']} ({i['code']})": i for i in kbk_list}
kbk_selected = st.selectbox("Выберите KBK", kbk_options.keys())
kbk = kbk_options[kbk_selected]

knp_options = {f"{k['knpName']} ({k['knpCode']})": k for k in kbk['knpList']}
knp_selected = st.selectbox("Выберите KNP", knp_options.keys())
knp = knp_options[knp_selected]

# Остальные поля
transaction_id = f"APP_INDNTRTAX_{uuid.uuid4()}"
amount = st.number_input("Сумма платежа", 100.0, 1000000.0, 1000.0)
purpose = st.text_input("Назначение", knp['knpName'])
period = st.date_input("Период", value=date.today().replace(day=1) - relativedelta(months=1))

# BIN если нужно
bin_code = None
if kbk.get("ugdLoadingRequired"):
    ugd_options = {f"{u['name']} ({u['code']})": u for u in ugd_list}
    ugd_selected = st.selectbox("Выберите УГД", ugd_options.keys())
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

    # Собираем payload и делаем платёж
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
