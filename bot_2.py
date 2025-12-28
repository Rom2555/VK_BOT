import os
import requests
import psycopg2
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from dotenv import load_dotenv
import logging

# === Настройки логирования ===
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# === Загрузка переменных окружения ===
load_dotenv()

# === Токены VK ===
GROUP_TOKEN = os.getenv('GROUP_TOKEN')
USER_TOKEN = os.getenv('USER_TOKEN')

# === Настройки PostgreSQL ===
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'vk_bot_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')

# === Подключение к БД ===
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# === Инициализация БД и таблиц ===
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            step VARCHAR(50),
            age INTEGER,
            sex INTEGER,
            city_id INTEGER,
            city_name VARCHAR(100)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            candidate_id BIGINT,
            name VARCHAR(200),
            link VARCHAR(100),
            city VARCHAR(100),
            photo_urls TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    log.info("✅ База данных инициализирована.")

# === Класс для поиска через VK API ===
class VkSearcher:
    def __init__(self, token):
        self.session = VkApi(token=token)
        self.api = self.session.get_api()

    def get_city_id(self, city_title):
        try:
            response = self.api.database.getCities(country_id=1, q=city_title, count=10)
            items = response['items']
            if not items:
                return None
            for city in items:
                if city['title'].lower().strip() == city_title.lower().strip():
                    return city['id']
            for city in items:
                if city_title.lower().strip() in city['title'].lower():
                    return city['id']
            return items[0]['id']
        except Exception as e:
            log.error(f"Ошибка поиска города: {e}")
            return None

    def search_users(self, age_from, age_to, sex, city_id, offset=0):
        try:
            response = self.api.users.search(
                age_from=age_from,
                age_to=age_to,
                sex=sex,
                city_id=city_id,
                has_photo=1,
                count=10,
                offset=offset,
                fields='bdate,city,sex',
                v='5.199'
            )
            return response['items']
        except Exception as e:
            log.error(f"Ошибка поиска пользователей: {e}")
            return []

    def get_top_photos(self, user_id):
        try:
            photos = self.api.photos.get(
                owner_id=user_id,
                album_id='profile',
                extended=1,
                count=30
            )
            top = sorted(photos['items'], key=lambda p: p['likes']['count'], reverse=True)
            return [f"photo{user_id}_{p['id']}" for p in top[:3]]
        except Exception as e:
            if '30' not in str(e) and 'private' not in str(e).lower():
                log.error(f"Ошибка получения фото: {e}")
            return []


# === Основной класс бота с PostgreSQL ===
class UserBotWithDB:
    def __init__(self, vk_api, searcher):
        self.vk = vk_api
        self.searcher = searcher

    def send_message(self, user_id, message, attachment=None):
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=message,
            attachment=attachment
        )

    # === Работа с состоянием пользователя в БД ===
    def get_user_state(self, user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT step, age, sex, city_id, city_name FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {
                'step': row[0],
                'data': {'age': row[1], 'sex': row[2], 'city_id': row[3], 'city_name': row[4]}
            }
        return None

    def save_user_state(self, user_id, step, data):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (user_id, step, age, sex, city_id, city_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                step = EXCLUDED.step,
                age = EXCLUDED.age,
                sex = EXCLUDED.sex,
                city_id = EXCLUDED.city_id,
                city_name = EXCLUDED.city_name
        ''', (user_id, step, data.get('age'), data.get('sex'), data.get('city_id'), data.get('city_name')))
        conn.commit()
        cur.close()
        conn.close()

    def clear_user_state(self, user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()

    # === Проверка, показывали ли уже этого кандидата ===
    def is_candidate_shown(self, user_id, candidate_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM candidates WHERE user_id = %s AND candidate_id = %s", (user_id, candidate_id))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists

    def save_candidate(self, user_id, person, photo_urls):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO candidates (user_id, candidate_id, name, link, city, photo_urls)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            person['id'],
            f"{person['first_name']} {person['last_name']}",
            f"vk.com/id{person['id']}",
            person.get('city', {}).get('title', 'Не указан'),
            ','.join(photo_urls) if photo_urls else None
        ))
        conn.commit()
        cur.close()
        conn.close()

    # === Обработка сообщения ===
    def handle_message(self, user_id, text):
        text = text.strip().lower()

        if text in ('/start', 'начать', 'найти пару'):
            self.save_user_state(user_id, 'wait_age', {'age': None, 'sex': None, 'city_id': None})
            self.send_message(user_id, "Привет! Введи желаемый возраст (например: 25).")
            return

        state = self.get_user_state(user_id)
        if not state:
            return

        step = state['step']
        data = state.get('data', {})

        match step:
            case 'wait_age':
                if text.isdigit() and 14 <= int(text) <= 90:
                    data['age'] = int(text)
                    self.save_user_state(user_id, 'wait_sex', data)
                    self.send_message(user_id, "Выбери пол для поиска:\n1 — мужчина\n2 — женщина")
                else:
                    self.send_message(user_id, "Введите возраст числом (от 14 до 90).")

            case 'wait_sex':
                if text in ('1', '2'):
                    data['sex'] = 2 if text == '1' else 1
                    self.save_user_state(user_id, 'wait_city', data)
                    self.send_message(user_id, "Введите город (например: Москва).")
                else:
                    self.send_message(user_id, "Введите 1 или 2.")

            case 'wait_city':
                city_title = text.title()
                city_id = self.searcher.get_city_id(city_title)
                if not city_id:
                    self.send_message(user_id, "Город не найден. Попробуйте ещё раз.")
                else:
                    data['city_id'] = city_id
                    data['city_name'] = city_title
                    self.save_user_state(user_id, 'searching', data)

                    age = data['age']
                    age_from, age_to = max(16, age - 5), age + 5
                    candidates = self.searcher.search_users(age_from, age_to, data['sex'], city_id)

                    sent = 0
                    for person in candidates:
                        if sent >= 3:
                            break
                        if self.is_candidate_shown(user_id, person['id']):
                            continue

                        name = f"{person['first_name']} {person['last_name']}"
                        link = f"vk.com/id{person['id']}"
                        message = f"👤 {name}\n📍 {link}"
                        photos = self.searcher.get_top_photos(person['id'])
                        attachment = ",".join(photos) if photos else None
                        self.send_message(user_id, message, attachment)
                        self.save_candidate(user_id, person, photos)
                        sent += 1

                    if sent == 0:
                        self.send_message(user_id, "Кандидаты не найдены или все уже показаны.")
                    else:
                        self.send_message(user_id, "✅ Три новых кандидата показаны.")

                    self.clear_user_state(user_id)

            case _:
                self.send_message(user_id, "Произошла ошибка. Напишите /start.")
                self.clear_user_state(user_id)


# === Запуск бота ===
if __name__ == '__main__':
    if not GROUP_TOKEN or not USER_TOKEN:
        raise ValueError("Требуются GROUP_TOKEN и USER_TOKEN в .env")

    init_db()

    group_session = VkApi(token=GROUP_TOKEN)
    vk = group_session.get_api()
    longpoll = VkLongPoll(group_session)

    searcher = VkSearcher(USER_TOKEN)
    bot = UserBotWithDB(vk, searcher)

    log.info("✅ Бот запущен и слушает сообщения...")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            bot.handle_message(event.user_id, event.text)