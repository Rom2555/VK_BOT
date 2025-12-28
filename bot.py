import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import requests

# === Настройки ===
GROUP_TOKEN = 'vk1.a.7mT7FcZo3tAVhobcX0tKvfrcj9Q6UyqslStJ5ncKMXQSc7MrhZNdZMfMcXSHq6Ghf51Y7jbgZTCGVuJC2Cm_uM069-eo2JAp0rVlLwDepporeNbMlYzWtaCBDZUOGEtkUS-dY3ifycot5QQTFXZQMxXAQwOZx-khOczY35XT_Qhp4Polm3UWN8n8CxvrwJKTFBvESMT4taqbZsg15Rqxdg'
USER_TOKEN = 'vk1.a.mqSeaCYSCq-lXgBXBOxqiGfRhYalT06P-erce9eiYwcuy2jCLbR9C8lMommk4w12dmIDvRBlS6KpZ2UoXhvI5mSysoCW8v0stOjLbwgr_XLhcJod3g6tAson6QDvxm13SKOrQlrCcCIWRDchVGSVlLBLCwyK79N-1vz-1FdQu9l9yVYKIEEpCfwjEQDL7NOShmaVtOe0WpSHCnKS-EIcBA'

# Сессия для бота (группа)
group_session = vk_api.VkApi(token=GROUP_TOKEN)
vk = group_session.get_api()
longpoll = VkLongPoll(group_session)

# Сессия для поиска (пользователь)
search_session = vk_api.VkApi(token=USER_TOKEN)
search_api = search_session.get_api()

# Хранилище состояний
user_states = {}


# === Функция поиска пользователей ===
def search_users(age_from, age_to, sex, city_id, offset=0):
    try:
        response = search_api.users.search(
            age_from=age_from,
            age_to=age_to,
            sex=sex,
            city=city_id,
            has_photo=1,
            count=10,
            offset=offset,
            fields='bdate,city,sex,photo_id',
            v='5.199'
        )
        return response['items']
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return []


# === Получение топ-3 фото по лайкам ===
def get_top_photos(user_id):
    try:
        photos = search_api.photos.get(
            owner_id=user_id,
            album_id='profile',
            extended=1,
            count=30
        )
        photo_likes = []
        for photo in photos['items']:
            # Берём максимальное по размеру изображение
            photo_url = max(photo['sizes'], key=lambda x: x['width'])['url']
            likes = photo['likes']['count']
            photo_id = photo['id']
            photo_likes.append((photo_url, likes, photo_id))

        # Сортируем по лайкам
        top_photos = sorted(photo_likes, key=lambda x: x[1], reverse=True)[:3]
        return top_photos
    except Exception as e:
        print(f"Ошибка фото: {e}")
        return []


# === Получение ID города — с access_token ===
def get_city_id(city_title):
    url = "https://api.vk.com/method/database.getCities"
    params = {
        'country_id': 1,
        'q': city_title,
        'count': 10,
        'v': '5.131',
        'access_token': USER_TOKEN  # ← Добавлен токен
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        if 'response' not in data:
            error_msg = data.get('error', {}).get('error_msg', 'Unknown error')
            print(f"❌ Ошибка API: {error_msg}")
            return None

        items = data['response']['items']
        if not items:
            print(f"⚠️ Город '{city_title}' не найден.")
            return None

        print(f"🔍 Найдены города: {[c['title'] for c in items]}")

        # Точное совпадение
        for city in items:
            if city['title'].lower().strip() == city_title.lower().strip():
                print(f"✅ Точное совпадение: {city['title']} → id={city['id']}")
                return city['id']

        # Частичное совпадение
        for city in items:
            if city_title.lower().strip() in city['title'].lower():
                print(f"✅ Частичное совпадение: '{city_title}' в '{city['title']}' → id={city['id']}")
                return city['id']

        # Возвращаем первый
        city = items[0]
        print(f"🟡 Не найдено, возвращаем первый: {city['title']} → id={city['id']}")
        return city['id']

    except Exception as e:
        print(f"❌ Ошибка при поиске города: {e}")
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
                message = "Выбери пол: 1 - мужчина, 2 - женщина."
            else:
                message = "Введите возраст числом (от 14 до 90)."
            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
            continue

        # Получаем пол
        if user_id in user_states and user_states[user_id]['step'] == 'wait_sex':
            if text in ('1', '2'):
                # Сохраняем, КЕМ ищем (противоположный пол)
                user_sex = int(text)
                search_sex = 1 if user_sex == 2 else 2  # 1=муж, 2=жен → ищем пару
                user_states[user_id]['data']['sex'] = search_sex
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
                age = data['age']
                sex = data['sex']
                data['city_id'] = city_id

                # ✅ Расширяем возраст в диапазон
                age_from = max(16, age - 5)
                age_to = age + 5

                # ✅ Передаём правильные аргументы
                candidates = search_users(age_from, age_to, sex, city_id)

                if not candidates:
                    message = "Кандидаты не найдены. Попробуйте другой возраст или город."
                    vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
                else:
                    for person in candidates[:3]:
                        name = f"{person['first_name']} {person['last_name']}"
                        link = f"vk.com/id{person['id']}"
                        photos = get_top_photos(person['id'])
                        message = f"👤 {name}\n📍 {link}\n"
                        if photos:
                            attachments = ",".join([f"photo{person['id']}_{p[2]}" for p in photos])  # p[2] = photo_id
                            vk.messages.send(
                                user_id=user_id,
                                random_id=get_random_id(),
                                message=message,
                                attachment=attachments
                            )

                        else:
                            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)
                user_states.pop(user_id)
            else:
                message = "Город не найден. Попробуйте ещё раз."
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)