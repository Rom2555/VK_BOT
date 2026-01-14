import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Candidate, Favorite, User


class DatabaseManager:
    """Менеджер для работы с базой данных бота."""

    def __init__(self, db_url):
        """Инициализация подключения к БД."""
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def get_or_create_user(self, vk_id):
        """Получает или создаёт пользователя по VK ID."""
        with self.Session() as session:
            user = session.query(User).filter_by(vk_id=vk_id).first()
            if not user:
                user = User(vk_id=vk_id)
                session.add(user)
                session.commit()
                session.refresh(user)
            return user

    def save_user_state(self, vk_id, state):
        """Сохраняет состояние диалога пользователя."""
        with self.Session() as session:
            user = session.query(User).filter_by(vk_id=vk_id).first()
            if user:
                user.state = json.dumps(state, ensure_ascii=False)
                session.commit()

    def load_user_state(self, vk_id):
        """Загружает состояние диалога пользователя."""
        with self.Session() as session:
            user = session.query(User).filter_by(vk_id=vk_id).first()
            if user and user.state:
                return json.loads(user.state)
            return None

    def get_or_create_candidate(
        self, vk_id, first_name, last_name, profile_url, photos
    ):
        """Получает или создаёт кандидата по VK ID."""
        with self.Session() as session:
            candidate = session.query(Candidate).filter_by(vk_id=vk_id).first()
            if not candidate:
                candidate = Candidate(
                    vk_id=vk_id,
                    first_name=first_name,
                    last_name=last_name,
                    profile_url=profile_url,
                    photos=json.dumps(photos, ensure_ascii=False),
                )
                session.add(candidate)
                session.commit()
                session.refresh(candidate)
            return candidate

    def add_to_favorites(
        self, user_vk_id, candidate_vk_id, first_name, last_name, profile_url, photos
    ):
        """Добавляет кандидата в избранное пользователя."""
        user = self.get_or_create_user(user_vk_id)
        candidate = self.get_or_create_candidate(
            candidate_vk_id, first_name, last_name, profile_url, photos
        )

        with self.Session() as session:
            exists = (
                session.query(Favorite)
                .filter_by(user_id=user.id, candidate_id=candidate.id)
                .first()
            )
            if exists:
                return False

            favorite = Favorite(user_id=user.id, candidate_id=candidate.id)
            session.add(favorite)
            session.commit()
            return True

    def get_favorites(self, user_vk_id):
        """Возвращает список избранных кандидатов пользователя."""
        with self.Session() as session:
            user = session.query(User).filter_by(vk_id=user_vk_id).first()
            if not user:
                return []

            favorites = []
            for fav in user.favorites:
                candidate = fav.candidate
                favorites.append(
                    {
                        "vk_id": candidate.vk_id,
                        "first_name": candidate.first_name,
                        "last_name": candidate.last_name,
                        "profile_url": candidate.profile_url,
                        "photos": json.loads(candidate.photos),
                        "added": fav.added,
                    }
                )
            return favorites
