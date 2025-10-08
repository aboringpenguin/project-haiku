from sqlalchemy import Column, Integer, String, DateTime, func
from .database import Base

class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Player(id={self.id}, username='{self.username}')>"