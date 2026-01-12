import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime,
    ForeignKey, Text, UniqueConstraint, func
)
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base

# Базовый класс для всех моделей
Base = declarative_base()

class User(Base):
    """Пользователь бота (тот, кто ищет знакомства)."""

    __tablename__ = 'users'

    # ID записи в нашей базе
    id = Column(Integer, primary_key=True)

    # ID пользователя в ВКонтакте
    vk_id = Column(Integer, unique=True, nullable=False)

    # JSON-строка с состоянием бота (текущий шаг, данные поиска и т.д.)
    state = Column(Text)

    # Дата создания записи
    created = Column(DateTime, default=func.now())

    # Связь с избранными кандидатами (один пользователь - много избранных)
    favorites = relationship('Favorite', back_populates='user')

class Candidate(Base):
    """Кандидат для знакомства (кого нашли)."""

    __tablename__ = 'candidates'

    # ID записи в нашей базе
    id = Column(Integer, primary_key=True)

    # ID кандидата в ВКонтакте
    vk_id = Column(Integer, unique=True, nullable=False)

    # Имя и фамилия кандидата
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)

    # Ссылка на профиль ВК (например:  vk.com/id12345)
    profile_url = Column(String(200), nullable=False)

    # JSON-строка с фотографиями для attachment (список строк "photo123_456")
    photos = Column(Text, nullable=False)

    # Дата создания записи
    created = Column(DateTime, default=func.now())

    # Связь с избранными (один кандидат может быть у многих пользователей)
    favorites = relationship('Favorite', back_populates='candidate')

class Favorite(Base):
    """Связь пользователь-кандидат (многие-ко-многим)."""

    __tablename__ = 'favorites'

    # ID записи в нашей базе
    id = Column(Integer, primary_key=True)

    # Ссылка на пользователя бота (внешний ключ)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Ссылка на кандидата (внешний ключ)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)

    # Дата добавления в избранное
    added = Column(DateTime, default=func.now())

    # Связи с таблицами
    user = relationship('User', back_populates='favorites')
    candidate = relationship('Candidate', back_populates='favorites')

    # Один кандидат может быть в избранном у пользователя только один раз
    __table_args__ = (UniqueConstraint('user_id', 'candidate_id'),)

class Database:
    """Основной класс для работы с базой данных."""

    def __init__(self, db_url: str = 'sqlite:///bot.db'):
        """
        Инициализация подключения к БД.
        Args: db_url: Строка подключения SQLAlchemy
        """
        # Создаем движок для работы с базой данных
        self.engine = create_engine(db_url)

        # Создаем фабрику сессий для работы с БД
        self.Session = sessionmaker(bind=self.engine)

        # Создаем таблицы при инициализации
        self.create_tables()

    def create_tables(self):
        """Создает таблицы, если они не существуют."""
        Base.metadata.create_all(self.engine)

    # --- Работа с пользователями ---

    def get_user(self, vk_id: int) -> Optional[User]:
        """Получает пользователя по ID ВКонтакте."""
        with self.Session() as session:
            return session.query(User).filter_by(vk_id=vk_id).first()

    def get_or_create_user(self, vk_id: int) -> User:
        """
        Получает существующего пользователя или создает нового.
        Используется, когда нужно гарантированно иметь пользователя в БД.
        """
        # Пытаемся найти пользователя
        user = self.get_user(vk_id)

        # Если не нашли - создаем нового
        if not user:
            with self.Session() as session:
                user = User(vk_id=vk_id)
                session.add(user)
                session.commit()

        return user

    def save_user_state(self, vk_id: int, state: dict):
        """
        Сохраняет состояние сессии пользователя.
        Args:
            vk_id: ID пользователя ВКонтакте
            state: Словарь с состоянием бота (шаги, данные поиска и т.д.)
        """
        with self.Session() as session:
            user = self.get_user(vk_id)
            if user:
                # Сериализуем словарь в JSON и сохраняем
                user.state = json.dumps(state, ensure_ascii=False)
                session.commit()

    def load_user_state(self, vk_id: int) -> Optional[dict]:
        """
        Загружает состояние сессии пользователя.
        Returns:
            Словарь с состоянием или None, если пользователь не найден
        """
        user = self.get_user(vk_id)
        if user and user.state:
            # Десериализуем JSON обратно в словарь
            return json.loads(user.state)
        return None

    # --- Работа с кандидатами ---

    def get_candidate(self, vk_id: int) -> Optional[Candidate]:
        """Получает кандидата по ID ВКонтакте."""
        with self.Session() as session:
            return session.query(Candidate).filter_by(vk_id=vk_id).first()

    def create_candidate(self, vk_id: int, first_name: str, last_name: str,
                         profile_url: str, photos: List[str]) -> Candidate:
        """
        Создает нового кандидата.
        Args:
            vk_id: ID кандидата в ВКонтакте
            first_name: Имя кандидата
            last_name: Фамилия кандидата
            profile_url: Ссылка на профиль
            photos: Список фотографий для attachment
        """
        with self.Session() as session:
            candidate = Candidate(
                vk_id=vk_id,
                first_name=first_name,
                last_name=last_name,
                profile_url=profile_url,
                # Сериализуем список фото в JSON
                photos=json.dumps(photos, ensure_ascii=False)
            )
            session.add(candidate)
            session.commit()
            return candidate

    def get_or_create_candidate(self, vk_id: int, first_name: str, last_name: str,
                                profile_url: str, photos: List[str]) -> Candidate:
        """
        Получает существующего кандидата или создает нового.
        Используется при добавлении в избранное, чтобы избежать дублирования.
        """
        # Пытаемся найти кандидата
        candidate = self.get_candidate(vk_id)

        # Если не нашли - создаем нового
        if not candidate:
            candidate = self.create_candidate(
                vk_id, first_name, last_name, profile_url, photos
            )

        return candidate

    # --- Работа с избранным ---

    def add_favorite(self, user_vk_id: int, candidate_vk_id: int,
                     first_name: str, last_name: str, profile_url: str,
                     photos: List[str]) -> bool:
        """
        Добавляет кандидата в избранное пользователя.
        Args:
            user_vk_id: ID пользователя бота в ВК
            candidate_vk_id: ID кандидата в ВК
            first_name: Имя кандидата
            last_name: Фамилия кандидата
            profile_url: Ссылка на профиль кандидата
            photos: Список фотографий кандидата
        Returns:
            True если кандидат добавлен, False если уже был в избранном
        """
        # Получаем или создаем пользователя
        user = self.get_or_create_user(user_vk_id)

        # Получаем или создаем кандидата
        candidate = self.get_or_create_candidate(
            candidate_vk_id, first_name, last_name, profile_url, photos
        )
        # Проверяем, не добавлен ли кандидат уже в избранное
        if self.is_favorite(user_vk_id, candidate_vk_id):
            return False

        # Добавляем связь в таблицу избранных
        with self.Session() as session:
            favorite = Favorite(user_id=user.id, candidate_id=candidate.id)
            session.add(favorite)
            session.commit()
            return True

    def remove_favorite(self, user_vk_id: int, candidate_vk_id: int) -> bool:
        """
        Удаляет кандидата из избранного пользователя.
        Returns: True если удалено, False если не было в избранном
        """
        with self.Session() as session:
            # Ищем связь пользователь-кандидат
            favorite = session.query(Favorite).join(User).join(Candidate).filter(
                User.vk_id == user_vk_id,
                Candidate.vk_id == candidate_vk_id
            ).first()

            # Если нашли - удаляем
            if favorite:
                session.delete(favorite)
                session.commit()
                return True

            return False

    def get_favorites(self, user_vk_id: int) -> List[Dict[str, Any]]:
        """
        Возвращает список избранных кандидатов пользователя.
        Returns: Список словарей с информацией о кандидатах
        """
        with self.Session() as session:
            # Получаем все записи избранного для пользователя
            favorites = session.query(Favorite).join(User).join(Candidate).filter(
                User.vk_id == user_vk_id
            ).order_by(Favorite.added.desc()).all()

            # Формируем удобный для использования список
            result = []
            for fav in favorites:
                cand = fav.candidate
                result.append({
                    'vk_id': cand.vk_id,
                    'first_name': cand.first_name,
                    'last_name': cand.last_name,
                    'profile_url': cand.profile_url,
                    'photos': json.loads(cand.photos),  # Десериализуем фото
                    'added': fav.added
                })

            return result

    def is_favorite(self, user_vk_id: int, candidate_vk_id: int) -> bool:
        """
        Проверяет, есть ли кандидат в избранном у пользователя.
        Returns: True если кандидат в избранном, иначе False
        """
        with self.Session() as session:
            # Считаем количество записей с такой связью
            count = session.query(Favorite).join(User).join(Candidate).filter(
                User.vk_id == user_vk_id,
                Candidate.vk_id == candidate_vk_id
            ).count()

            # Если count > 0, значит связь существует
            return count > 0

# Глобальная переменная для хранения экземпляра базы данных
_db_instance = None

def get_database(db_url: str = 'sqlite:///bot.db') -> Database:
    """
    Возвращает экземпляр базы данных.
    Паттерн синглтон: создает базу только при первом вызове,
    последующие вызовы возвращают тот же экземпляр.
    Args:
        db_url: Строка подключения к БД
    Returns:
        Экземпляр класса Database
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = Database(db_url)

    return _db_instance