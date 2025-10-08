import asyncio
import json
import aio_pika
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from . import schemas
from .database import async_session
from .repository import PlayerRepository

# --- RabbitMQ Consumer and Lifespan Management ---

async def consume_player_events(repo: PlayerRepository, r: redis.Redis):
    """Listens for player events from RabbitMQ and processes them."""
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "game_events", aio_pika.ExchangeType.TOPIC
        )
        queue = await channel.declare_queue("player_service_queue", durable=True)
        
        # Bind to both connected and disconnected events
        await queue.bind(exchange, routing_key="player.connected")
        await queue.bind(exchange, routing_key="player.disconnected")

        print("Player service is listening for events...")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = json.loads(message.body.decode())
                    username = body["username"]
                    print(f"Received event '{message.routing_key}': {body}")
                    
                    async with async_session() as session:
                        # Get the player from the database
                        player = await repo.get_player_by_username(session, username)
                        if not player and message.routing_key == "player.connected":
                            # Create player if they don't exist and the event is 'connected'
                            player = await repo.create_player(session, username)
                            print(f"Player '{username}' created with ID {player.id}.")
                        
                        if player:
                            # Set Redis status based on the event type
                            if message.routing_key == "player.connected":
                                await r.set(f"player:{player.id}:status", "online")
                                print(f"Set player {player.id} status to 'online'")
                            elif message.routing_key == "player.disconnected":
                                await r.set(f"player:{player.id}:status", "offline")
                                print(f"Set player {player.id} status to 'offline'")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the FastAPI app."""
    repo = PlayerRepository()
    r = redis.Redis.from_pool(redis_pool)
    task = asyncio.create_task(consume_player_events(repo, r))
    print("Player event consumer started.")
    yield
    print("Player event consumer stopped.")

# Pass the lifespan manager to the FastAPI app
app = FastAPI(lifespan=lifespan)

# --- Redis Connection Pool ---
redis_pool = redis.ConnectionPool.from_url("redis://localhost:6379/0", decode_responses=True)


# --- Dependency Injection & API Endpoints (No changes below this line) ---
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

@app.post("/players", response_model=schemas.PlayerResponse, status_code=201)
async def create_new_player(player_data: schemas.PlayerCreate, repo: PlayerRepository = Depends(), db: AsyncSession = Depends(get_db_session)):
    return await repo.create_player(db_session=db, username=player_data.username)

@app.get("/players/{username}", response_model=schemas.PlayerResponse)
async def get_player(username: str, repo: PlayerRepository = Depends(), db: AsyncSession = Depends(get_db_session)):
    player = await repo.get_player_by_username(db_session=db, username=username)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.get("/players/{username}/status")
async def get_player_status(username: str, db: AsyncSession = Depends(get_db_session)):
    r = redis.Redis.from_pool(redis_pool)
    repo = PlayerRepository()
    player = await repo.get_player_by_username(db, username)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found in primary database")
    status = await r.get(f"player:{player.id}:status")
    if status is None:
        return {"username": username, "status": "offline"}
    return {"username": username, "status": status}