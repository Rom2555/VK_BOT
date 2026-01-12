import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime,
    ForeignKey, Text, UniqueConstraint, func
)
from sqlalchemy.orm import relationship, declarative_base

# Базовый класс для всех моделей
Base = declarative_base()


class User(Base):
    """Пользователь бота (тот, кто ищет знакомства)."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    state = Column(Text)
    created = Column(DateTime, default=datetime.now())
    favorites = relationship('Favorite', back_populates='user')


class Candidate(Base):
    """Кандидат для знакомства (кого нашли)."""
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    profile_url = Column(String(200), nullable=False)
    photos = Column(Text, nullable=False)
    created = Column(DateTime, default=func.now())
    favorites = relationship('Favorite', back_populates='candidate')


class Favorite(Base):
    """Связь пользователь-кандидат (многие-ко-многим)."""
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    added = Column(DateTime, default=func.now())

    user = relationship('User', back_populates='favorites')
    candidate = relationship('Candidate', back_populates='favorites')

    __table_args__ = (UniqueConstraint('user_id', 'candidate_id'),)