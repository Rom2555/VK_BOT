from vk_api import VkApi


class VkSearcher:
    """Класс для поиска пользователей, городов и фото через VK API."""

    def __init__(self, token):
        self.session = VkApi(token=token)
        self.api = self.session.get_api()

    def get_city_id(self, city_title):
        try:
            response = self.api.database.getCities(country_id=1, q=city_title, count=10)
            items = response['items']
            if not items:
                return None
            # Точное совпадение
            for city in items:
                if city['title'].lower().strip() == city_title.lower().strip():
                    return city['id']
            # Частичное
            for city in items:
                if city_title.lower().strip() in city['title'].lower():
                    return city['id']
            return items[0]['id']
        except Exception as e:
            print(f"Ошибка поиска города: {e}")
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
                fields='bdate,city,sex,is_closed,can_access_closed',
                v='5.199'
            )
            # Фильтрация: пропускаем пользователей, к которым нет доступа
            users = []
            for person in response['items']:
                if person.get('is_closed', False) and not person.get('can_access_closed', False):
                    continue  # пропустить приватного пользователя
                users.append(person)
            return users
        except Exception as e:
            print(f"Ошибка поиска пользователей: {e}")
            return []

    def get_top_photos(self, user_id):
        try:
            photos = self.api.photos.get(
                owner_id=user_id,
                album_id='profile',
                extended=1,
                count=30
            )
            top = sorted(photos['items'], key=lambda p: p['likes']['count'] + p['comments']['count'], reverse=True)
            return [f"photo{user_id}_{p['id']}" for p in top[:3]]
        except Exception as e:
            print(f"Ошибка получения фото: {e}")
            return []