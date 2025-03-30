import streamlit as st
import requests

st.set_page_config(page_title="API Tester", layout="wide")

st.title("🔧 API-тестер")

st.info("""
👈 Используйте **левое боковое меню** для навигации между разделами.
""")

# Ввод и сохранение токена
st.subheader("🔑 Введите Bearer-токен")
token = st.text_input("Токен авторизации", type="password")

if token:
    st.session_state['token'] = token
    st.success("Токен успешно сохранён и доступен на других страницах!")
