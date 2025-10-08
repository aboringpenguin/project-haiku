import json
import aio_pika
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .connection_manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()

async def publish_event(routing_key: str, client_id: int, username: str):
    """Helper function to connect and publish an event to RabbitMQ."""
    try:
        connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "game_events", aio_pika.ExchangeType.TOPIC
            )
            
            message_body = json.dumps({"client_id": client_id, "username": username}).encode()
            
            message = aio_pika.Message(
                body=message_body,
                content_type="application/json"
            )

            await exchange.publish(message, routing_key=routing_key)
            print(f"Published '{routing_key}' event for client #{client_id}")

    except Exception as e:
        print(f"Error publishing to RabbitMQ: {e}")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    print(f"Client #{client_id} has connected.")
    
    # Announce that a player has connected
    await publish_event("player.connected", client_id, f"Player_{client_id}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Announce that a player has disconnected
        await publish_event("player.disconnected", client_id, f"Player_{client_id}")
        print(f"Client #{client_id} has disconnected.")