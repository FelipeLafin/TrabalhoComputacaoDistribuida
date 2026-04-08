import asyncio
import websockets
import json

rooms = {}
admins = set()

async def handler(websocket):
    current_room = None
    user_name = "Anônimo"

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "login":
                    user_name = data.get("user", "Anônimo")
                    current_room = data.get("room", "geral")

                    if current_room not in rooms:
                        rooms[current_room] = set()

                    rooms[current_room].add(websocket)

                    if data.get("isAdmin"):
                        admins.add(websocket)

                    print(f"{user_name} entrou na sala {current_room}")

                elif msg_type == "message":
                    if current_room and current_room in rooms:
                        payload = json.dumps({
                            "user": user_name,
                            "text": data.get("text"),
                            "style": "normal"
                        })

                        for client in rooms[current_room]:
                            await client.send(payload)

                elif msg_type == "admin_broadcast":
                    if websocket in admins:
                        payload = json.dumps({
                            "user": user_name,
                            "text": data.get("text"),
                            "style": "admin"
                        })

                        for room_clients in rooms.values():
                            for client in room_clients:
                                await client.send(payload)
                    else:
                        await websocket.send(json.dumps({
                            "text": "Você não é admin!",
                            "style": "error"
                        }))

            except json.JSONDecodeError:
                print(f"❌ Erro: {user_name} enviou dados inválidos.")
                continue

    except websockets.exceptions.ConnectionClosed:
        pass


    finally:

        if current_room and current_room in rooms:

            rooms[current_room].discard(websocket)

            payload = json.dumps({
                "user": "Sistema",
                "text": f"{user_name} saiu da sala",
                "room": current_room,
                "style": "system"

            })
            for client in rooms[current_room]:
                await client.send(payload)
            if len(rooms[current_room]) == 0:
                del rooms[current_room]

        admins.discard(websocket)

        print(f"🔌 {user_name} desconectou.")


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("✅ Servidor Atitus rodando em ws://localhost:8080")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado.")