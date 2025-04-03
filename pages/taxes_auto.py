import streamlit as st
import requests
import json
import uuid
import random
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from utils import fetch_api_data
import time

st.set_page_config(layout="wide")
st.title("💳 Платежи в бюджет — Налоги компании (с расчётом комиссии)")


import json
from datetime import datetime

def save_successful_payload(payload, filename="successful_payloads.json"):
    """
    Загружает существующие данные из файла (ожидается список записей).
    Если данные не являются списком, оборачивает их в список.
    Затем добавляет новую запись с временной меткой и сохраняет обновлённый список обратно.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Если данные не являются списком, оборачиваем их в список
        if not isinstance(data, list):
            data = [data]
    except Exception:
        data = []
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "payload": payload
    }
    data.append(record)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# @st.cache_data
# def fetch_api_data(endpoint):
#     try:
#         response = requests.get(f"{base_url}{endpoint}", headers=headers, verify=False)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         st.error(f"Ошибка запроса к {endpoint}: {e}")
#         return {}

# Проверка токена
if 'token' not in st.session_state:
    st.error("⚠️ Введите токен на главной странице.")
    st.stop()

base_url = st.text_input("Базовый URL", "https://sme-bff.kz.infra")

headers = {
    "Authorization": f"Bearer {st.session_state['token']}",
    "Content-Type": "application/json"
}

# Получение счетов
accounts_data = fetch_api_data(base_url=base_url, endpoint="/api/account/accounts")
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

max_attempts = st.number_input("Количество попыток отправки, если не прошло", value=5, step=1, key="max_attempts")

# Справочники
selected_operation_type = "INDIVIDUAL_ENTREPRENEUR"
ugd_list = fetch_api_data(base_url=base_url, endpoint="/api/dictionary/dictionary/ugd/all")
kbk_list = fetch_api_data(base_url=base_url, endpoint=f"/api/dictionary/dictionary/kbk/kbk-to-knp-list?taxesPaymentOperationType={selected_operation_type}")
quarters_list = None

if not kbk_list:
    st.stop()

kbk_options = {f"{i['name']} ({i['code']})": i for i in kbk_list}
ugd_options = {f"{u['name']} ({u['code']})": u for u in ugd_list}
# kbk_selected = st.selectbox("Выберите KBK", list(kbk_options.keys()))
# kbk = kbk_options[kbk_selected]

def fetch_period_list(kbkCode, knpCode):
    period_data = fetch_api_data(base_url=base_url, endpoint=
        f"/api/dictionary/dictionary/payment-period?"
        f"operationType=INDIVIDUAL_ENTREPRENEUR"
        f"&kbk={kbkCode}"
        f"&knp={knpCode}"
        f"&id=0"
    )

    # Если нет ответа или periodType не указан – вернем пустой список
    if not period_data:
        return []

    if period_data.get("periodType") is None:
        return []

    # Если есть поле "periods" – вернем его в удобном формате
    if "periods" in period_data:
        return [
            {
                "year": p["year"],
                "quarter": p["quarter"],     
                "yearHalf": p["yearHalf"]  
            }
            for p in period_data["periods"]
        ]
    else:
        return ["Нет кварталов"]


st.markdown("---")
st.header("Настройки платежа")

# Размещаем поля и чекбоксы для фиксации в одной строке

col0, col0_1 = st.columns([2,1])
with col0:
    base_kbk_selected = st.selectbox("Выберите KBK", list(kbk_options.keys()))
    base_kbk = kbk_options[base_kbk_selected]
with col0_1:
    fix_kbk = st.checkbox("Фиксировать kbk", value=True)

knp_options = {f"{k['knpName']} ({k['knpCode']})": k for k in base_kbk['knpList']}

col1, col2 = st.columns([2,1])
with col1:
    base_knp_selected = st.selectbox("Выберите KNP", list(knp_options.keys()))
    base_knp = knp_options[base_knp_selected]
with col2:
    fix_knp = st.checkbox("Фиксировать knp", value=True)
    
col2, col3 = st.columns([2,1])
with col2:
    base_amount = st.number_input("Сумма платежа", 100.0, 1000000.0, 1000.0)
with col3:
    fix_amount = st.checkbox("Фиксировать сумму", value=True)

col4, col5 = st.columns([2,1])
with col4:
    base_purpose = st.text_input("Назначение", base_knp['knpName'])
with col5:
    fix_purpose = st.checkbox("Фиксировать назначение", value=True)

col6, col7 = st.columns([2,1])
with col6:
    kbk_code_str = (str(base_kbk["code"]) if fix_kbk else '0')

    if kbk_code_str.startswith('1'):
        base_period_list = fetch_period_list(base_kbk["code"], base_knp["knpCode"])
        if base_period_list == []:
            base_period = st.date_input("Период", value=date.today().replace(day=1) - relativedelta(months=1))
        else:
            period_selected = st.selectbox("Выберите квартал", [i['quarter'] for i in base_period_list])
            base_period = period_selected
    else:
        base_period = st.date_input("Период", value=date.today().replace(day=1) - relativedelta(months=1))

with col7:
    fix_period = st.checkbox("Фиксировать период", value=True)


if base_kbk.get("ugdLoadingRequired"):
    col8, col9 = st.columns([2, 1])
    with col8:
        ugd_selected = st.selectbox("Выберите УГД", list(ugd_options.keys()))
        base_ugd = ugd_options[ugd_selected]
    with col9:
        fix_ugd = st.checkbox("Фиксировать ugd", value=True)
else:
    fix_ugd = False
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
        
        #################
        random_kbk_key = random.choice(list(kbk_options.keys()))
        kbk_dict = kbk_options[random_kbk_key]
        iter_kbk = base_kbk if fix_kbk else kbk_dict

        # Используем фиксированные или случайные значения
        knp_options = {f"{k['knpName']} ({k['knpCode']})": k for k in iter_kbk['knpList']}
        random_knp_key = random.choice(list(knp_options.keys()))
        knp_dict = knp_options[random_knp_key]
        iter_knp = base_knp if fix_knp else knp_dict

        iter_amount = base_amount if fix_amount else round(random.uniform(100.0, 10000.0), 2)
        iter_purpose = base_purpose if fix_purpose else f"{base_purpose}_{random.randint(1000, 9999)}"

        kbk_code_str = str(iter_kbk["code"])
        if kbk_code_str.startswith('1'):
            iter_period_list = fetch_period_list(iter_kbk["code"], iter_knp["knpCode"])
            if iter_period_list == []:
                iter_period = base_period.isoformat() if fix_period else (base_period + relativedelta(days=random.randint(-100, 10))).isoformat()
            else:
                random_period = random.choice(iter_period_list)
                iter_year = random_period["year"]
                iter_quarter = random_period["quarter"]
                iter_period = base_period if fix_period else iter_quarter
        else:
            iter_period = base_period.isoformat() if fix_period else (base_period + relativedelta(days=random.randint(-100, 10))).isoformat()
        
        if iter_kbk.get("ugdLoadingRequired"):
            random_choice = random.choice(list(ugd_options.keys()))
            iter_ugd = base_ugd if fix_ugd else ugd_options[random_choice]
        
        #################

        # Формируем payload
        iter_payload = {
            "transactionId": iter_transaction_id,
            "ibanDebit": iban_debit,
            "amount": iter_amount,
            "kbk": {
                "name": iter_kbk["name"],
                "code": iter_kbk["code"],
                "employeeLoadingRequired": iter_kbk["employeeLoadingRequired"],
                "ugdLoadingRequired": iter_kbk["ugdLoadingRequired"]
            },
            "knp": iter_knp["knpCode"],
            "purpose": iter_purpose,
            "taxesPaymentOperationType": selected_operation_type
        }

        if kbk_code_str.startswith('1') and iter_period_list != []:
            iter_payload["quarter"] = iter_period
            iter_payload['year'] = iter_year
        elif kbk_code_str.startswith('1') and iter_period_list == ["Нет кварталов"]:
            iter_payload['year'] = iter_year
        else:
            iter_payload["period"] = iter_period

        if iter_kbk.get("ugdLoadingRequired"):
            iter_payload["ugd"] = iter_ugd

        
        # Формируем commission_payload вне цикла (так как amount и transactionId фиксированы для данной итерации)
        commission_payload = [{
            "transactionId": iter_transaction_id,
            "transactionAmount": iter_amount,
            "currency": "KZT",
            "urgent": False,
            "futureValueDate": False
        }]

        attempt = 0
        payment_status = None
        payment_text = ""
        while attempt < max_attempts:
            iter_transaction_id = f"APP_INDNTRTAX_{uuid.uuid4()}"
            commission_payload[0]["transactionId"] = iter_transaction_id
            iter_payload["transactionId"] = iter_transaction_id
            # Пересчитываем комиссию
            try:
                commission_url = f"{base_url}/api/charge-calculator/api/v1/charges/trn/multi-calculate"
                commission_resp = requests.put(commission_url, headers=headers, json=commission_payload, verify=False)
                commission_resp.raise_for_status()
                commission_status = commission_resp.status_code
                commission_text = commission_resp.text
            except Exception as e:
                commission_status = None
                commission_text = str(e)
            
            # Попытка отправки платежа
            try:
                payment_url = f"{base_url}/api/payment/api/v5/budget/init/entrepreneur"
                payment_resp = requests.post(payment_url, headers=headers, json=iter_payload, verify=False)
                payment_resp.raise_for_status()
                payment_status = payment_resp.status_code
                payment_text = payment_resp.text
                save_successful_payload(iter_payload, filename="successful_payloads.json")
                # Если запрос прошёл успешно, выходим из цикла
                break
            except requests.exceptions.RequestException as e:
                attempt += 1
                if attempt < max_attempts:
                    progress_text.text(f"Попытка {attempt}/{max_attempts} не удалась, пересчитываем комиссию и повторяем...")
                    time.sleep(0.5)  # небольшая задержка перед повторной попыткой
                else:
                    payment_status = None
                    if hasattr(e, 'response') and e.response is not None:
                        payment_text = f"Попытка {attempt}/{max_attempts} — Exception: {e}\nServer Response:\n{e.response.text}"
                    else:
                        payment_text = f"Попытка {attempt}/{max_attempts} — Exception: {e}"
                    break

        results.append({
            # "TransactionID": iter_transaction_id,
            "Kbk": iter_kbk['code'],
            "Knp": iter_knp['knpCode'],
            "Amount": iter_amount,
            "Purpose": iter_purpose,
            "Period": iter_period,
            "Attempts": attempt,
            "Commission Status": commission_status,
            "Payment Status": payment_status,
            "Commission Response": commission_text,
            "Payment Response": payment_text,
            "Payload": iter_payload,
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

        styled_df = df_results.style.map(color_status, subset=['Commission Status', 'Payment Status'])
        table_placeholder.dataframe(styled_df, height=500)
        # # Добавим небольшую задержку для наглядности обновления (не обязательно)
        # time.sleep(0.001)
    
    progress_text.text("Итерационные тесты завершены.")
