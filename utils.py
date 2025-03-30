# utils.py
import requests
import streamlit as st
import uuid

def get_headers():
    """Возвращает заголовки с авторизацией из session_state, плюс JSON."""
    if 'token' not in st.session_state:
        st.error("Токен не найден в session_state! Сначала зайдите на главную страницу и введите токен.")
        st.stop()
    return {
        "Authorization": f"Bearer {st.session_state['token']}",
        "Content-Type": "application/json"
    }

def fetch_api_data(base_url, endpoint, method="GET", payload=None):
    """Универсальная функция для запросов: GET, POST, PUT. Возвращает JSON или None."""
    url = f"{base_url}{endpoint}"
    headers = get_headers()
    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, verify=False)
        elif method.upper() == "POST":
            resp = requests.post(url, headers=headers, json=payload, verify=False)
        elif method.upper() == "PUT":
            resp = requests.put(url, headers=headers, json=payload, verify=False)
        else:
            st.error(f"Метод {method} не поддерживается.")
            return None
        
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка запроса [{method}] {url}: {e}")
        # Можно дополнительно st.text(resp.text) вывести, если нужно
        return None

def generate_transaction_id(prefix="APP_INDNTRTAX"):
    """Генерируем уникальный transactionId."""
    return f"{prefix}_{uuid.uuid4()}"
