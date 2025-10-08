from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from .models import Player

class PlayerRepository:
    async def create_player(self, db_session: AsyncSession, username: str) -> Player:
        """Creates a new player in the database."""

        new_player = Player(username=username)
        db_session.add(new_player)
        await db_session.commit()
        await db_session.refresh(new_player)
        return new_player

    async def get_player_by_username(self, db_session: AsyncSession, username: str) -> Optional[Player]:
        """Fetches a single player from the database by their username."""
        
        stmt = select(Player).where(Player.username == username)
        result = await db_session.execute(stmt)
        player = result.scalar_one_or_none()
        return player

    async def get_all_players(self, db_session: AsyncSession) -> List[Player]:
        """Fetches all players from the database."""
        
        stmt = select(Player)
        result = await db_session.execute(stmt)
        players = result.scalars().all()
        return players