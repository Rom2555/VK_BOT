import logging
import time

from vk_api import VkApi, VkApiError
from vk_api.longpoll import VkEventType, VkLongPoll

from config import GROUP_TOKEN, USER_TOKEN
from user_bot import UserBot
from vk_searcher import VkSearcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    while True:
        try:
            group_session = VkApi(token=GROUP_TOKEN)
            group_session.get_api().users.get(user_ids=1)  # Проверка токена
            vk = group_session.get_api()
            longpoll = VkLongPoll(group_session)

            searcher = VkSearcher(USER_TOKEN)
            bot = UserBot(vk, searcher)

            logging.info("Бот запущен и слушает сообщения...")

            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    bot.handle_message(event.user_id, event.text.strip())

        except VkApiError as e:
            logging.error(f"Ошибка API ВКонтакте: {e}")
        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
        finally:
            time.sleep(5)  # Пауза перед перезапуском


if __name__ == "__main__":
    main()
