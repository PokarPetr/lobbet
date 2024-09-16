from aiohttp import web
from asyncio import run, create_task
from admiralbet_parser import update_odds_periodically
from config import HOST, PORT


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
                break
            else:
                print(f"Server received: {msg.data}")
        elif msg.type == web.WSMsgType.ERROR:
            print(f'WebSocket connection closed with exception {ws.exception()}')

    print('WebSocket connection closed')
    return ws


async def main():
    app = web.Application()
    app.add_routes([web.get('/', websocket_handler)])

    server_task = create_task(web._run_app(app, host=HOST, port=PORT))
    odds_update_task = create_task(update_odds_periodically())

    await server_task
    await odds_update_task

"""
   Entry point of the application. It schedules periodic updates for fetching and processing odds data.
"""
if __name__ == "__main__":
    run(main())
