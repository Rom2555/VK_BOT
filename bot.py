import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import requests

# === Настройки ===
TOKEN = 'ваш_токен_сообщества'  # ← Замените

# Авторизация бота
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# Хранилище состояний пользователей (в реальном проекте — БД)
user_states = {}  # {user_id: {'step': 'wait_age', 'data': {}}}


# === Функция поиска пользователей ===
def search_users(age, sex, city_id, offset=0):
    try:
        response = vk.users.search(
            age_from=age,
            age_to=age,
            sex=sex,           # 1 — женщина, 2 — мужчина
            city=city_id,
            has_photo=1,
            count=10,
            offset=offset,
            fields='photo_id, about, bdate'
        )
        return response['items']
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return []


# === Получение топ-3 фото по лайкам ===
def get_top_photos(user_id):
    try:
        photos = vk.photos.get(
            owner_id=user_id,
            album_id='profile',
            extended=1,
            count=30
        )
        photo_likes = []
        for photo in photos['items']:
            photo_url = max(photo['sizes'], key=lambda x: x['width'])['url']
            likes = photo['likes']['count']
            photo_likes.append((photo_url, likes))

        # Сортируем по лайкам, берём топ-3
        top_photos = sorted(photo_likes, key=lambda x: x[1], reverse=True)[:3]
        return top_photos  # [(url, likes), ...]
    except Exception as e:
        print(f"Ошибка фото: {e}")
        return []


# === Получение ID города ===
def get_city_id(city_title):
    try:
        response = vk.database.getCities(country_id=1, q=city_title, count=1)
        if response['items']:
            return response['items'][0]['id']
        else:
            return None
    except:
        return None


# === Обработка сообщений ===
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.strip().lower()
        message = ""

        # Начало диалога
        if text in ('/start', 'начать', 'найти пару'):
            user_states[user_id] = {'step': 'wait_age'}
            message = "Привет! Введи желаемый возраст (например: 25)."
            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
            continue

        # Получаем возраст
        if user_id in user_states and user_states[user_id]['step'] == 'wait_age':
            if text.isdigit() and 14 <= int(text) <= 90:
                user_states[user_id]['data'] = {'age': int(text)}
                user_states[user_id]['step'] = 'wait_sex'
                message = "Выбери пол: 1 — женщина, 2 — мужчина."
            else:
                message = "Введите возраст числом (от 14 до 90)."
            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
            continue

        # Получаем пол
        if user_id in user_states and user_states[user_id]['step'] == 'wait_sex':
            if text in ('1', '2'):
                user_states[user_id]['data']['sex'] = int(text)
                user_states[user_id]['step'] = 'wait_city'
                message = "Введи город (например: Москва)."
            else:
                message = "Введите 1 или 2."
            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
            continue

        # Получаем город
        if user_id in user_states and user_states[user_id]['step'] == 'wait_city':
            city_id = get_city_id(text)
            if city_id:
                data = user_states[user_id]['data']
                data['city_id'] = city_id

                # Поиск
                candidates = search_users(data['age'], data['sex'], data['city_id'])
                if not candidates:
                    message = "Кандидаты не найдены."
                    vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
                else:
                    for person in candidates[:3]:  # Покажем первых 3
                        name = f"{person['first_name']} {person['last_name']}"
                        link = f"vk.com/id{person['id']}"
                        photos = get_top_photos(person['id'])
                        message = f"👤 {name}\n📍 {link}\n"
                        if photos:
                            message += "ТОП-3 фото по лайкам:\n"
                            for i, (url, likes) in enumerate(photos, 1):
                                message += f"{i}. Лайков: {likes}\n"
                            # Отправляем фото
                            vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                message=message,
                                attachment=",".join([f"photo{person['id']}_{photo['id']}" for photo in photos])
                            )
                        else:
                            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
                # Завершаем
                user_states.pop(user_id)
            else:
                message = "Город не найден. Попробуйте ещё раз."
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)