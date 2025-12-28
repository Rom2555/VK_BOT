from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from config import GROUP_TOKEN, USER_TOKEN
from vk_searcher import VkSearcher
from user_bot import UserBot


def main():
    # Инициализация API группы
    group_session = VkApi(token=GROUP_TOKEN)
    vk = group_session.get_api()
    longpoll = VkLongPoll(group_session)

    # Инициализация компонентов
    searcher = VkSearcher(USER_TOKEN)
    bot = UserBot(vk, searcher)

    print("Бот запущен и слушает сообщения...")

    # Основной цикл
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            bot.handle_message(event.user_id, event.text)


if __name__ == '__main__':
    main()