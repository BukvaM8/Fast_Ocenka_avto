# -----------------------------
# АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ ИЗ requirements.txt (без --user)
# -----------------------------
import subprocess
import sys
import os
import streamlit as st  # нужен сразу для session_state/st.error

# --- АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ (жёстко без --user и без user-конфигов pip) ---
import subprocess, sys, os, tempfile
import streamlit as st

def install_requirements_strict(req_path: str):
    # Отключаем влияние пользовательских конфигов/переменных
    env = os.environ.copy()
    # Игнорировать все pip-конфиги пользователя/системы
    # (пустой временный конфиг)
    empty_cfg = os.path.join(tempfile.gettempdir(), "empty_pip.cfg")
    if not os.path.exists(empty_cfg):
        with open(empty_cfg, "w", encoding="utf-8") as f:
            f.write("")  # пусто
    env["PIP_CONFIG_FILE"] = empty_cfg
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env.pop("PIP_USER", None)         # если кто-то выставил PIP_USER=1
    env.pop("PIP_TARGET", None)       # чтобы не уводило инсталл в стороннюю папку
    env.pop("PYTHONUSERBASE", None)   # чтобы не активировалась user-site

    # Команда без --user
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "-r", req_path]
    # Диагностика (если что-то пойдёт не так, увидим точную команду)
    print("Running:", " ".join(cmd))
    print("Using PIP_CONFIG_FILE:", env.get("PIP_CONFIG_FILE"))

    subprocess.check_call(cmd, env=env)

if "reqs_installed" not in st.session_state:
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        try:
            install_requirements_strict(req_path)
            st.session_state["reqs_installed"] = True
        except subprocess.CalledProcessError as e:
            print("Ошибка при установке зависимостей:", e)
            st.error("Не удалось установить зависимости. См. терминал.")
    else:
        st.session_state["reqs_installed"] = True
# --- конец блока автоинсталла ---


# -----------------------------
# ОСНОВНЫЕ ИМПОРТЫ И НАСТРОЙКИ
# -----------------------------
import random
from datetime import date

st.set_page_config(page_title="Оценка авто — MVP", layout="centered")

DEFAULT_CONTRACTOR = "ООО «Агентство «Бизнес-Актив»"

def generate_uuid7() -> str:
    return f"{random.randint(0, 9_999_999):07d}"

@st.dialog("Авторизация")
def login_dialog():
    st.write("Введите ваши данные, чтобы продолжить работу с приложением.")
    name = st.text_input("Имя", key="auth_name")
    login_val = st.text_input("Логин", key="auth_login")

    if login_val and not st.session_state.get("uuid7"):
        st.session_state["uuid7"] = generate_uuid7()
    if not login_val:
        st.session_state.pop("uuid7", None)

    st.text_input(
        "Ваш UUID (7 цифр)",
        value=st.session_state.get("uuid7", ""),
        key="uuid7_display",
        disabled=True,
        help="Генерируется автоматически после ввода логина."
    )

    can_submit = bool(name.strip()) and bool(login_val.strip()) and bool(st.session_state.get("uuid7"))
    if st.button("Войти", type="primary", disabled=not can_submit):
        st.session_state["user_name"] = name.strip()
        st.session_state["user_login"] = login_val.strip()
        st.session_state["auth_ok"] = True
        st.rerun()

# Гейт авторизации
if not st.session_state.get("auth_ok"):
    login_dialog()
    st.stop()

# Сайдбар
with st.sidebar:
    st.markdown("### Профиль")
    st.markdown(f"**Имя:** {st.session_state.get('user_name', '')}")
    st.markdown(f"**Логин:** {st.session_state.get('user_login', '')}")
    st.markdown(f"**UUID:** {st.session_state.get('uuid7', '')}")
    if st.button("Выйти"):
        for k in ("auth_ok","user_name","user_login","auth_name","auth_login","uuid7","uuid7_display"):
            st.session_state.pop(k, None)
        st.rerun()

# Основной интерфейс
st.title("Оценка авто")

if "contractor" not in st.session_state:
    st.session_state["contractor"] = DEFAULT_CONTRACTOR

with st.form("auto_appraisal_form", clear_on_submit=False):
    col1, col2 = st.columns(2)

    with col1:
        contract_no = st.text_input("Номер договора", key="contract_no")
        basis = st.text_input("Основание", key="basis")
        valuation_date = st.date_input("Дата оценки:", value=date.today(), key="valuation_date")
        report_date = st.date_input("Дата составления Отчета об оценке:", value=date.today(), key="report_date")

    with col2:
        customer = st.text_input("Заказчик:", key="customer")
        contractor = st.text_input(
            "Подрядчик:",
            key="contractor",
            help="По умолчанию подставляется ООО «Агентство «Бизнес-Актив», можно изменить."
        )
        price_vat = st.number_input("Стоимость с учетом НДС:", min_value=0.0, step=0.01, format="%.2f", key="price_vat")
        price_no_vat = st.number_input("Стоимость без учета НДС:", min_value=0.0, step=0.01, format="%.2f", key="price_no_vat")

    submitted = st.form_submit_button("Сохранить", type="primary")

    if submitted:
        record = {
            "user_uuid": st.session_state.get("uuid7"),
            "user_name": st.session_state.get("user_name"),
            "user_login": st.session_state.get("user_login"),
            "Номер договора": contract_no,
            "Основание": basis,
            "Дата оценки": str(valuation_date),
            "Дата составления отчета": str(report_date),
            "Заказчик": customer,
            "Подрядчик": contractor,
            "Стоимость с НДС": price_vat,
            "Стоимость без НДС": price_no_vat,
        }
        st.success("Данные сохранены (локально в сессии).")
        st.json(record)

        # --- БД (оставлено закомментированным) ---
        # import mysql.connector
        # try:
        #     conn = mysql.connector.connect(
        #         host="localhost",
        #         user="user",
        #         password="password",
        #         database="auto_appraisal_db",
        #     )
        #     cur = conn.cursor()
        #     cur.execute(
        #         """
        #         INSERT INTO appraisals (
        #             user_uuid, user_name, user_login,
        #             contract_no, basis, valuation_date, report_date,
        #             customer, contractor, price_vat, price_no_vat
        #         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        #         """,
        #         (
        #             record["user_uuid"], record["user_name"], record["user_login"],
        #             record["Номер договора"], record["Основание"], record["Дата оценки"],
        #             record["Дата составления отчета"], record["Заказчик"], record["Подрядчик"],
        #             record["Стоимость с НДС"], record["Стоимость без НДС"]
        #         ),
        #     )
        #     conn.commit()
        #     cur.close()
        #     conn.close()
        #     st.success("Запись сохранена в базу данных MySQL.")
        # except Exception as e:
        #     st.error(f"Ошибка сохранения в MySQL: {e}")
        # ------------------------------------------
