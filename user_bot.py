from vk_api.utils import get_random_id

from keyboard import get_action_buttons, get_sex_keyboard


class UserBot:
    """Управляет диалогом с пользователем через VK API."""

    def __init__(self, vk_api, searcher, db):
        """Инициализирует бота с API, поисковиком и БД."""
        self.vk = vk_api
        self.searcher = searcher
        self.db = db

    def send_message(self, user_id, message, attachment=None, keyboard=None):
        """Отправляет сообщение пользователю."""
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=message,
            attachment=attachment,
            keyboard=keyboard,
        )

    def handle_message(self, user_id, text):
        """Обрабатывает входящее сообщение от пользователя."""
        text = text.strip().lower()

        # Всегда обрабатываем /start
        if text == "/start" or text == "новый поиск":
            # Создаём пользователя и обнуляем состояние
            self.db.get_or_create_user(vk_id=user_id)
            self.db.save_user_state(user_id, {"step": "wait_age"})
            self.send_message(user_id, "Привет! Введи желаемый возраст (например: 25).")
            return

        # Загружаем состояние из БД
        state = self.db.load_user_state(user_id)
        if not state:
            self.send_message(user_id, "Напишите /start, чтобы начать.")
            return

        step = state["step"]

        if step == "wait_age":
            if text.isdigit() and 14 <= int(text) <= 90:
                state["age"] = int(text)
                state["step"] = "wait_sex"
                self.db.save_user_state(user_id, state)
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
                self.db.save_user_state(user_id, state)
                self.send_message(user_id, "Введите город (например: Санкт-Петербург).")
            else:
                self.send_message(
                    user_id,
                    "Выберите пол с помощью кнопок.",
                    keyboard=get_sex_keyboard(),
                )

        elif step == "wait_city":
            city_title = text.strip()

            # Проверяем, что текст не пуст и содержит хотя бы один буквенный символ
            if not city_title or not any(c.isalpha() for c in city_title):
                self.send_message(user_id, "Введите корректное название города (например: Москва).")
                return

            city_id = self.searcher.get_city_id(city_title)
            if not city_id:
                self.send_message(user_id, "Город не найден. Попробуйте ещё раз.")
            else:
                age = state["age"]
                age_from, age_to = max(14, age - 1), age + 1
                sex = state["sex"]

                candidates = self.searcher.search_users(age_from, age_to, sex, city_id)

                if not candidates:
                    self.send_message(user_id, "Кандидаты не найдены.")
                else:
                    # Фильтруем: убираем тех, кто уже в избранном
                    favorites = self.db.get_favorites(user_vk_id=user_id)
                    favorite_ids = {fav['vk_id'] for fav in favorites}
                    filtered = [c for c in candidates if c['id'] not in favorite_ids]

                    if not filtered:
                        self.send_message(user_id, "Нет новых кандидатов.")
                    else:
                        state["step"] = "showing"
                        state["candidates"] = filtered
                        state["index"] = 0
                        self.db.save_user_state(user_id, state)
                        self.send_next_candidate(user_id)

        elif step == "showing":
            if text == "дальше":
                self.send_next_candidate(user_id)
            elif text == "добавить в избранное":
                self.add_to_favorites(user_id)
            elif text == "избранное":
                self.show_favorites(user_id)

    def send_next_candidate(self, user_id):
        """Показывает следующего кандидата из списка."""
        state = self.db.load_user_state(user_id)
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
                "Кандидаты закончились. Начните новый поиск.",
                keyboard=get_action_buttons(),
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
            keyboard=get_action_buttons(),
        )

        # Сохраняем кандидата в БД
        self.db.get_or_create_candidate(
            vk_id=person["id"],
            first_name=person["first_name"],
            last_name=person["last_name"],
            profile_url=link,
            photos=photos
        )

        # Обновляем индекс
        state["index"] += 1
        self.db.save_user_state(user_id, state)

    def add_to_favorites(self, user_id):
        """Добавляет текущего кандидата в избранное."""
        state = self.db.load_user_state(user_id)
        if not state or "candidates" not in state or state["index"] == 0:
            self.send_message(user_id, "Сначала посмотрите кандидата.")
            return

        current_idx = state["index"] - 1
        person = state["candidates"][current_idx]
        photos = self.searcher.get_top_photos(person["id"])

        success = self.db.add_to_favorites(
            user_vk_id=user_id,
            candidate_vk_id=person["id"],
            first_name=person["first_name"],
            last_name=person["last_name"],
            profile_url=f"vk.com/id{person['id']}",
            photos=photos
        )

        if success:
            self.send_message(user_id, "Кандидат добавлен в избранное!")
        else:
            self.send_message(user_id, "Этот кандидат уже в избранном.")

    def show_favorites(self, user_id):
        """Отправляет пользователю всех кандидатов из избранного."""
        favorites = self.db.get_favorites(user_vk_id=user_id)
        if not favorites:
            self.send_message(user_id, "Ваш список избранного пуст.")
            return

        for fav in favorites:
            name = f"{fav['first_name']} {fav['last_name']}"
            link = fav['profile_url']
            message = f"{name}\nСсылка: {link}"
            attachment = ",".join(fav['photos']) if fav['photos'] else None

            self.send_message(user_id, message, attachment=attachment)

        self.send_message(user_id, "Это всё из вашего избранного.", keyboard=get_action_buttons())
