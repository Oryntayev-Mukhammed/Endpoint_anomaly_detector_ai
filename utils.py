# utils.py

import requests
import streamlit as st
import uuid
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_headers():
    """Возвращает заголовки с авторизацией из session_state, плюс JSON."""
    if 'token' not in st.session_state:
        st.error("Нет Access-токена! Сначала вернитесь на главную страницу и введите токены.")
        st.stop()
    return {
        "Authorization": f"Bearer {st.session_state['token']}",
        "Content-Type": "application/json"
    }

def do_refresh(base_url):
    """
    Отправляет запрос /api/v3/token/refresh/parent_child
    в формате application/x-www-form-urlencoded (по скриншоту).
    Обновляет session_state['token'] при успехе.
    """
    if 'refresh_token' not in st.session_state:
        st.warning("Нет refresh-токена, не можем рефрешить!")
        return False

    url = f"{base_url}/api/v3/token/refresh/parent_child"
    
    # Обычно refresh-эндпоинт требует form-data или x-www-form-urlencoded
    payload = {
        "parentRefreshToken": st.session_state['refresh_token'],
        "childRefreshToken": st.session_state['child_refresh'],
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        resp = requests.post(url, data=payload, headers=headers, verify=False)
        resp.raise_for_status()
        
        data = resp.json()
        # Внутри data обычно хранится accessToken, refreshToken и т.д.
        # Исходя из примера, видим
        # {
        #   "parentAuthResponse": { ... "accessToken": "...", "refreshToken":"..." },
        #   "childAuthResponse": { ... }
        # }
        
        if 'parentAuthResponse' in data and 'accessToken' in data['parentAuthResponse']:
            new_access = data['parentAuthResponse']['accessToken']
            new_refresh = data['parentAuthResponse']['refreshToken']
            st.session_state['token'] = new_access
            st.session_state['refresh_token'] = new_refresh
            st.info("✅ Токен успешно обновлён (родительский)!")
            
            # Аналогично, если нужен child:
            if 'childAuthResponse' in data and 'accessToken' in data['childAuthResponse']:
                new_child_access = data['childAuthResponse']['accessToken']
                new_child_refresh = data['childAuthResponse']['refreshToken']
                # Сохраняем при необходимости
                st.session_state['child_token'] = new_child_access
                st.session_state['child_refresh'] = new_child_refresh
                st.info("✅ Токен успешно обновлён (дочерний)!")
            return True
        else:
            st.error("Не нашли accessToken в ответе refresh!")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при рефреше токена: {e}")
        return False

def fetch_api_data(base_url, endpoint, method="GET", payload=None):
    """
    Универсальная функция для запросов: GET, POST, PUT.
    Если получаем 401 => пытаемся рефрешить, потом повторяем запрос.
    """
    def make_request():
        url = f"{base_url}{endpoint}"
        headers = get_headers()
        
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, verify=False)
        elif method.upper() == "POST":
            resp = requests.post(url, headers=headers, json=payload, verify=False)
        elif method.upper() == "PUT":
            resp = requests.put(url, headers=headers, json=payload, verify=False)
        else:
            st.error(f"Метод {method} не поддерживается.")
            return None
        
        return resp
    
    resp = make_request()
    if resp is None:
        return None
    
    # Проверяем статус
    if resp.status_code == 401:
        st.warning("Получили 401. Пробуем рефрешить токен...")
        ok = do_refresh(base_url)
        if ok:
            st.info("Попытка повторить запрос с обновлённым токеном...")
            resp = make_request()  # повторяем запрос
        else:
            st.error("Не удалось рефрешить токен! Останавливаем.")
            return resp.json

    if resp.ok:
        return resp.json()
    else:
        st.error(f"Ошибка запроса [{method}] {endpoint}: {resp.status_code}")
        st.text(resp.text)
        return resp.json

def generate_transaction_id(prefix="APP_INDNTRTAX"):
    """Генерируем уникальный transactionId."""
    return f"{prefix}_{uuid.uuid4()}"
