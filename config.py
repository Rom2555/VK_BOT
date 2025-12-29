import os

from dotenv import load_dotenv

load_dotenv()

GROUP_TOKEN = os.getenv("GROUP_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN")

if not GROUP_TOKEN or not USER_TOKEN:
    raise ValueError("Не установлены GROUP_TOKEN или USER_TOKEN в .env файле")
