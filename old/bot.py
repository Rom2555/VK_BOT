# import os
# import requests
# from vk_api import VkApi
# from vk_api.longpoll import VkLongPoll, VkEventType
# from vk_api.utils import get_random_id
# from dotenv import load_dotenv
#
# load_dotenv()
#
#
# class VkSearcher:
#     """Класс для поиска пользователей, городов и фото через VK API."""
#
#     def __init__(self, token):
#         self.session = VkApi(token=token)
#         self.api = self.session.get_api()
#
#     def get_city_id(self, city_title):
#         try:
#             response = self.api.database.getCities(country_id=1, q=city_title, count=10)
#             items = response['items']
#             if not items:
#                 return None
#             # Точное совпадение
#             for city in items:
#                 if city['title'].lower().strip() == city_title.lower().strip():
#                     return city['id']
#             # Частичное
#             for city in items:
#                 if city_title.lower().strip() in city['title'].lower():
#                     return city['id']
#             return items[0]['id']
#         except Exception as e:
#             print(f"Ошибка поиска города: {e}")
#             return None
#
#     def search_users(self, age_from, age_to, sex, city_id, offset=0):
#         try:
#             response = self.api.users.search(
#                 age_from=age_from,
#                 age_to=age_to,
#                 sex=sex,
#                 city_id=city_id,
#                 has_photo=1,
#                 count=10,
#                 offset=offset,
#                 fields='bdate,city,sex',
#                 v='5.199'
#             )
#             return response['items']
#         except Exception as e:
#             print(f"Ошибка поиска пользователей: {e}")
#             return []
#
#     def get_top_photos(self, user_id):
#         try:
#             photos = self.api.photos.get(
#                 owner_id=user_id,
#                 album_id='profile',
#                 extended=1,
#                 count=30
#             )
#             top = sorted(photos['items'], key=lambda p: p['likes']['count'], reverse=True)
#             return [f"photo{user_id}_{p['id']}" for p in top[:3]]
#         except Exception as e:
#             print(f"Ошибка получения фото: {e}")
#             return []
#
#
# class UserBot:
#     """Класс, управляющий состоянием и диалогом с пользователем."""
#
#     def __init__(self, vk_api, searcher):
#         self.vk = vk_api
#         self.searcher = searcher
# #####################################################################################################################
#         # Словарь для хранения состояния пользователя
#
#         self.user_states = {}
# ####################################################################################################################
#
#     def send_message(self, user_id, message, attachment=None):
#         self.vk.messages.send(
#             user_id=user_id,
#             random_id=get_random_id(),
#             message=message,
#             attachment=attachment
#         )
#
#     def handle_message(self, user_id, text):
#         """Обработка входящего сообщения."""
#
#         text = text.strip().lower()
#
#         if text in ('/start'):
#             self.user_states[user_id] = {'step': 'wait_age'}
#             self.send_message(user_id, "Привет! Введи желаемый возраст (например: 25).")
#             return
#
#         if user_id not in self.user_states:
#             return
#
#         state = self.user_states[user_id]     ########################################################################
#         print(self.user_states)
#
#         match state['step']:
#             case 'wait_age':
#                 if text.isdigit() and 14 <= int(text) <= 90:
#                     state['data'] = {'age': int(text)}
#                     state['step'] = 'wait_sex'
#                     self.send_message(user_id, "Выбери пол для поиска:\n1 — мужчина\n2 — женщина")
#                 else:
#                     self.send_message(user_id, "Введите возраст числом (от 14 до 90).")
#
#             case 'wait_sex':
#                 if text in ('1', '2'):
#                     search_sex = 2 if text == '1' else 1
#                     state['data']['sex'] = search_sex
#                     state['step'] = 'wait_city'
#                     self.send_message(user_id, "Введите город (например: Санкт-Петербург).")
#                 else:
#                     self.send_message(user_id, "Введите 1 или 2.")
#
#             case 'wait_city':
#                 city_id = self.searcher.get_city_id(text)
#                 if not city_id:
#                     self.send_message(user_id, "Город не найден. Попробуйте ещё раз.")
#                 else:
#                     data = state['data']
#                     age = data['age']
#                     age_from, age_to = max(16, age - 5), age + 5  # защита от слишком маленького возраста (12)
#                     candidates = self.searcher.search_users(age_from, age_to, data['sex'], city_id)
#
#                     if not candidates:
#                         self.send_message(user_id, "К сожалению, кандидаты не найдены.")
#                     else:
#                         for person in candidates[:3]:
#                             name = f"{person['first_name']} {person['last_name']}"
#                             link = f"vk.com/id{person['id']}"
#                             message = f"Имя: {name}\nСсылка: {link}"
#                             photos = self.searcher.get_top_photos(person['id'])
#                             attachment = ",".join(photos) if photos else None
#                             self.send_message(user_id, message, attachment)
#
# ################################### Наверное здесь должна быть запись результатов в БД ###########################
#
#                     # Завершаем сессию, очищая словарь состояния
#                     self.user_states.pop(user_id)
#
#             case _:
#                 self.send_message(user_id, "Произошла ошибка. Напишите /start.")
#                 self.user_states.pop(user_id, None)
#
#
# # === Запуск бота ===
# if __name__ == '__main__':
#     GROUP_TOKEN = os.getenv('GROUP_TOKEN')
#     USER_TOKEN = os.getenv('USER_TOKEN')
#
#     if not GROUP_TOKEN or not USER_TOKEN:
#         raise ValueError("Требуются GROUP_TOKEN и USER_TOKEN в .env")
#
#     # Инициализация
#     group_session = VkApi(token=GROUP_TOKEN)
#     vk = group_session.get_api()
#     longpoll = VkLongPoll(group_session)
#
#     # Инициализация поиска и бота
#     searcher = VkSearcher(USER_TOKEN)
#     bot = UserBot(vk, searcher)
#
#     print("Бот запущен и слушает сообщения...")
#
#     # Основной цикл
#     for event in longpoll.listen():
#         if event.type == VkEventType.MESSAGE_NEW and event.to_me:
#             bot.handle_message(event.user_id, event.text)