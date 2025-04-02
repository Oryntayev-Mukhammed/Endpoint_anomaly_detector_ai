# main.py

import streamlit as st
import requests

st.set_page_config(page_title="API Tester", layout="wide")

st.title("🔧 API-тестер")

st.info("""
👈 Используйте **левое боковое меню** для навигации между разделами.
""")

# Поле для Access-токена
st.subheader("🔑 Введите Bearer-токен (Access)")
access_token_input = st.text_input("Access-токен", type="password", key="access_token_input")

# Поле для Parent Refresh-токена
st.subheader("🔄 Введите Parent Refresh-токен")
parent_refresh_input = st.text_input("Parent Refresh-токен", type="password", key="parent_refresh_input")

# Поле для Child Refresh-токена
st.subheader("🔄 Введите Child Refresh-токен")
child_refresh_input = st.text_input("Child Refresh-токен", type="password", key="child_refresh_token_input")

if access_token_input:
    st.session_state['token'] = access_token_input
    st.success("Access-токен сохранён в session_state!")

if parent_refresh_input:
    # В do_refresh() мы проверяем 'refresh_token' как родительский
    st.session_state['refresh_token'] = parent_refresh_input
    st.info("Parent Refresh-токен сохранён в session_state! (refresh_token)")

if child_refresh_input:
    # В do_refresh() мы сохраняем 'child_refresh'
    st.session_state['child_refresh'] = child_refresh_input
    st.info("Child Refresh-токен сохранён в session_state! (child_refresh)")
