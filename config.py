import os
from dotenv import load_dotenv

load_dotenv()

GROUP_TOKEN = os.getenv("GROUP_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not GROUP_TOKEN:
    raise ValueError("Не установлен GROUP_TOKEN в .env")
if not USER_TOKEN:
    raise ValueError("Не установлен USER_TOKEN в .env")
if not DATABASE_URL:
    raise ValueError("Не установлен DATABASE_URL в .env")
