from vk_api.utils import get_random_id


class UserBot:
    """Класс, управляющий состоянием и диалогом с пользователем."""

    def __init__(self, vk_api, searcher):
        self.vk = vk_api
        self.searcher = searcher
        self.user_states = {}  # Хранение состояния пользователей

    def send_message(self, user_id, message, attachment=None):
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=message,
            attachment=attachment
        )

    def handle_message(self, user_id, text):
        """Обработка входящего сообщения."""
        text = text.strip().lower()

        if text == '/start':
            self.user_states[user_id] = {'step': 'wait_age'}
            self.send_message(user_id, "Привет! Введи желаемый возраст (например: 25).")
            return

        if user_id not in self.user_states:
            return

        state = self.user_states[user_id]

        match state['step']:
            case 'wait_age':
                if text.isdigit() and 14 <= int(text) <= 90:
                    state['data'] = {'age': int(text)}
                    state['step'] = 'wait_sex'
                    self.send_message(user_id, "Выбери пол для поиска:\n1 — мужчина\n2 — женщина")
                else:
                    self.send_message(user_id, "Введите возраст числом (от 14 до 90).")

            case 'wait_sex':
                if text in ('1', '2'):
                    search_sex = 2 if text == '1' else 1
                    state['data']['sex'] = search_sex
                    state['step'] = 'wait_city'
                    self.send_message(user_id, "Введите город (например: Санкт-Петербург).")
                else:
                    self.send_message(user_id, "Введите 1 или 2.")

            case 'wait_city':
                city_title = text
                city_id = self.searcher.get_city_id(city_title)
                if not city_id:
                    self.send_message(user_id, "Город не найден. Попробуйте ещё раз.")
                else:
                    data = state['data']
                    age = data['age']
                    age_from, age_to = max(16, age - 5), age + 5
                    candidates = self.searcher.search_users(age_from, age_to, data['sex'], city_id)

                    if not candidates:
                        self.send_message(user_id, "К сожалению, кандидаты не найдены.")
                    else:
                        for person in candidates[:3]:
                            name = f"{person['first_name']} {person['last_name']}"
                            link = f"vk.com/id{person['id']}"
                            message = f"Имя: {name}\nСсылка: {link}"
                            photos = self.searcher.get_top_photos(person['id'])
                            attachment = ",".join(photos) if photos else None
                            self.send_message(user_id, message, attachment)

                    # Завершаем диалог
                    self.user_states.pop(user_id)

            case _:
                self.send_message(user_id, "Произошла ошибка. Напишите /start.")
                self.user_states.pop(user_id, None)