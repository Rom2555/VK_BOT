import os
from dotenv import load_dotenv

load_dotenv()

GROUP_TOKEN = os.getenv("GROUP_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if not GROUP_TOKEN:
    raise ValueError("Не установлен GROUP_TOKEN в .env")
if not USER_TOKEN:
    raise ValueError("Не установлен USER_TOKEN в .env")
if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS]):
    raise ValueError(
        "Не установлены все необходимые параметры БД в .env: "
        "DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS"
    )