import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from database.models import Base, User, Candidate, Favorite


class DatabaseManager:
    """Менеджер базы данных — логика работы с моделями."""

    def __init__(self, db_url: str = 'sqlite:///bot.db'):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        """Создаёт таблицы, если их нет."""
        Base.metadata.create_all(self.engine)

    # --- Работа с пользователями ---

    def get_user(self, vk_id: int) -> Optional[User]:
        """Получает пользователя по ID ВК."""
        with self.Session() as session:
            return session.query(User).filter_by(vk_id=vk_id).first()

    def get_or_create_user(self, vk_id: int) -> User:
        """Получает или создаёт пользователя."""
        user = self.get_user(vk_id)
        if not user:
            with self.Session() as session:
                user = User(vk_id=vk_id)
                session.add(user)
                session.commit()
        return user

    def save_user_state(self, vk_id: int, state: dict):
        """Сохраняет состояние пользователя."""
        with self.Session() as session:
            user = self.get_user(vk_id)
            if user:
                user.state = json.dumps(state, ensure_ascii=False)
                session.commit()

    def load_user_state(self, vk_id: int) -> Optional[dict]:
        """Загружает состояние пользователя."""
        user = self.get_user(vk_id)
        if user and user.state:
            return json.loads(user.state)
        return None

    # --- Работа с кандидатами ---

    def get_candidate(self, vk_id: int) -> Optional[Candidate]:
        """Получает кандидата по ID ВК."""
        with self.Session() as session:
            return session.query(Candidate).filter_by(vk_id=vk_id).first()

    def create_candidate(self, vk_id: int, first_name: str, last_name: str,
                         profile_url: str, photos: List[str]) -> Candidate:
        """Создаёт нового кандидата."""
        with self.Session() as session:
            candidate = Candidate(
                vk_id=vk_id,
                first_name=first_name,
                last_name=last_name,
                profile_url=profile_url,
                photos=json.dumps(photos, ensure_ascii=False)
            )
            session.add(candidate)
            session.commit()
            return candidate

    def get_or_create_candidate(self, vk_id: int, first_name: str, last_name: str,
                                profile_url: str, photos: List[str]) -> Candidate:
        """Получает или создаёт кандидата."""
        candidate = self.get_candidate(vk_id)
        if not candidate:
            candidate = self.create_candidate(
                vk_id, first_name, last_name, profile_url, photos
            )
        return candidate

    # --- Работа с избранным ---

    def add_favorite(self, user_vk_id: int, candidate_vk_id: int,
                     first_name: str, last_name: str, profile_url: str,
                     photos: List[str]) -> bool:
        """Добавляет кандидата в избранное."""
        user = self.get_or_create_user(user_vk_id)
        candidate = self.get_or_create_candidate(
            candidate_vk_id, first_name, last_name, profile_url, photos
        )

        if self.is_favorite(user_vk_id, candidate_vk_id):
            return False

        with self.Session() as session:
            favorite = Favorite(user_id=user.id, candidate_id=candidate.id)
            session.add(favorite)
            session.commit()
            return True

    def remove_favorite(self, user_vk_id: int, candidate_vk_id: int) -> bool:
        """Удаляет из избранного."""
        with self.Session() as session:
            favorite = session.query(Favorite).join(User).join(Candidate).filter(
                User.vk_id == user_vk_id,
                Candidate.vk_id == candidate_vk_id
            ).first()

            if favorite:
                session.delete(favorite)
                session.commit()
                return True
            return False

    def get_favorites(self, user_vk_id: int) -> List[Dict[str, Any]]:
        """Возвращает список избранных кандидатов."""
        with self.Session() as session:
            favorites = session.query(Favorite).join(User).join(Candidate).filter(
                User.vk_id == user_vk_id
            ).order_by(Favorite.added.desc()).all()

            result = []
            for fav in favorites:
                cand = fav.candidate
                result.append({
                    'vk_id': cand.vk_id,
                    'first_name': cand.first_name,
                    'last_name': cand.last_name,
                    'profile_url': cand.profile_url,
                    'photos': json.loads(cand.photos),
                    'added': fav.added
                })
            return result

    def is_favorite(self, user_vk_id: int, candidate_vk_id: int) -> bool:
        """Проверяет, есть ли кандидат в избранном."""
        with self.Session() as session:
            count = session.query(Favorite).join(User).join(Candidate).filter(
                User.vk_id == user_vk_id,
                Candidate.vk_id == candidate_vk_id
            ).count()
            return count > 0


# Глобальный экземпляр (синглтон)
_db_instance = None


def get_database(db_url: str = 'sqlite:///bot.db') -> DatabaseManager:
    """Возвращает единый экземпляр менеджера БД."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_url)
    return _db_instance