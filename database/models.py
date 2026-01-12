from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime,
    ForeignKey, Text, UniqueConstraint, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """Пользователь бота (тот, кто ищет знакомства)."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    state = Column(Text)  # JSON: {"step": "wait_age", "age": 25}
    created = Column(DateTime, default=func.now())  # ← исправлено
    favorites = relationship('Favorite', back_populates='user')


class Candidate(Base):
    """Кандидат для знакомства (кого нашли)."""
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    profile_url = Column(String(200), nullable=False)
    photos = Column(Text, nullable=False)  # JSON-массив: ["photo1", "photo2", ...]
    created = Column(DateTime, default=func.now())
    favorites = relationship('Favorite', back_populates='candidate')


class Favorite(Base):
    """Избранное. Связь пользователь-кандидат (многие-ко-многим)."""
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    user = relationship('User', backref='favorites')
    candidate = relationship('Candidate', backref='favorites')

    __table_args__ = (UniqueConstraint('user_id', 'candidate_id'),)