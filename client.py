import asyncio
import websockets

async def connect_to_gateway():
    uri = "ws://localhost:8080/ws/1"
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        # Keep the connection alive, similar to how a game client would stay running.
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(connect_to_gateway())