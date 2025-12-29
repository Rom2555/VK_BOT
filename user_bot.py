import logging

from vk_api.utils import get_random_id

from keyboard import get_action_buttons, get_sex_keyboard


class UserBot:
    """Класс, управляющий состоянием и диалогом с пользователем."""

    def __init__(self, vk_api, searcher):
        self.vk = vk_api
        self.searcher = searcher
        self.user_states = {}

    def send_message(self, user_id, message, attachment=None, keyboard=None):
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=message,
            attachment=attachment,
            keyboard=keyboard,
        )

    def handle_message(self, user_id, text):
        text = text.strip().lower()
        logging.info(
            f"Пользователь {user_id}: '{text}' |"
            f" Состояние: {self.user_states.get(user_id)}"
        )

        # Всегда обрабатываем /start
        if text == "/start" or text == "начать заново":
            self.user_states[user_id] = {"step": "wait_age"}
            self.send_message(user_id, "Привет! Введи желаемый возраст (например: 25).")
            return

        if user_id not in self.user_states:
            self.send_message(user_id, "Напишите /start, чтобы начать.")
            return

        state = self.user_states[user_id]
        step = state["step"]

        if step == "wait_age":
            if text.isdigit() and 14 <= int(text) <= 90:
                state["age"] = int(text)
                state["step"] = "wait_sex"
                self.send_message(
                    user_id,
                    "Выбери пол для поиска:\n1 — мужчина\n2 — женщина",
                    keyboard=get_sex_keyboard(),
                )
            else:
                self.send_message(user_id, "Введите возраст числом (от 14 до 90).")

        elif step == "wait_sex":
            if text in ("1", "2"):
                state["sex"] = 2 if text == "1" else 1
                state["step"] = "wait_city"
                self.send_message(user_id, "Введите город (например: Санкт-Петербург).")
            else:
                self.send_message(
                    user_id,
                    "Выберите пол с помощью кнопок.",
                    keyboard=get_sex_keyboard(),
                )

        elif step == "wait_city":
            city_title = text
            city_id = self.searcher.get_city_id(city_title)
            if not city_id:
                self.send_message(user_id, "Город не найден. Попробуйте ещё раз.")
            else:
                age = state["age"]
                age_from, age_to = max(16, age - 5), age + 5
                sex = state["sex"]

                candidates = self.searcher.search_users(age_from, age_to, sex, city_id)

                if not candidates:
                    self.send_message(user_id, "Кандидаты не найдены.")
                    self.user_states.pop(user_id)
                else:
                    state["step"] = "showing"
                    state["candidates"] = candidates
                    state["index"] = 0
                    self.send_next_candidate(user_id)

        elif step == "showing":
            if text == "дальше":
                self.send_next_candidate(user_id)
            elif text == "добавить в избранное":
                self.send_message(user_id, "Пока заглушка для БД.")
            elif text == "избранное":
                self.send_message(user_id, "Пока заглушка для БД.")

    def send_next_candidate(self, user_id):
        state = self.user_states.get(user_id)
        if not state or "candidates" not in state:
            self.send_message(
                user_id, "Ошибка. Начните с /start.", keyboard=get_action_buttons()
            )
            return

        idx = state["index"]
        candidates = state["candidates"]

        if idx >= len(candidates):
            self.send_message(
                user_id,
                "Кандидаты закончились. Что дальше?",
                keyboard=get_action_buttons(),  # теперь кнопки всегда активны
            )
            return

        person = candidates[idx]
        name = f"{person['first_name']} {person['last_name']}"
        link = f"vk.com/id{person['id']}"
        message = f"Имя: {name}\nСсылка: {link}"

        photos = self.searcher.get_top_photos(person["id"])
        attachment = ",".join(photos) if photos else None

        self.send_message(
            user_id,
            message,
            attachment=attachment,
            keyboard=get_action_buttons(),  # ← новая клавиатура
        )

        state["index"] += 1
