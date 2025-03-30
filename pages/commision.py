# pages/commission.py
import streamlit as st
from utils import fetch_api_data, generate_transaction_id

st.title("🧮 Расчёт комиссии (ручной)")

if 'token' not in st.session_state:
    st.error("⚠️ Сначала введите токен на главной странице.")
    st.stop()

base_url = st.text_input("Базовый URL", "https://sme-bff.kz.infra")

transaction_id = generate_transaction_id()
amount = st.number_input("Сумма платежа", min_value=100.0, max_value=1000000.0, value=1000.0)

if st.button("🔍 Рассчитать комиссию"):
    payload = [{
        "transactionId": transaction_id,
        "transactionAmount": amount,
        "currency": "KZT",
        "urgent": False,
        "futureValueDate": False
    }]
    resp = fetch_api_data(base_url, "/api/charge-calculator/api/v1/charges/trn/multi-calculate",
                          method="PUT", payload=payload)
    if resp:
        st.json(resp)
        st.success("Комиссия рассчитана.")
    else:
        st.error("Не удалось рассчитать комиссию!")
