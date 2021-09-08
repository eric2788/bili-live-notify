from json.decoder import JSONDecodeError
from typing import Any, List
import requests
import asyncio
# noinspection PyPackageRequirements
import telegram
import json
import redis
import time


async def _on_live(data):
    print(data)
    user_cover = data['cover']
    bilibili_uid = data['uid']
    title = data['title']
    room_id = data['room']
    name = data['name']

    print(f'正在發送 {name} 的開播通知: {room_id}, 標題: {title}')

    caption = '<a href="https://space.bilibili.com/' + \
        str(bilibili_uid) + '">' + name + '</a> 正在直播\n'
    caption += '标题： ' + title + '\n'
    reply_markup = telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton('直播间', url='https://live.bilibili.com/' + str(room_id))]])
    if len(user_cover) > 0:
        bot.sendPhoto(userId, user_cover, caption=caption, parse_mode='html',
                                reply_markup=reply_markup)
    else:
        bot.send_message(
            userId, caption, parse_mode='html', reply_markup=reply_markup)


def handle_ws(message):
    try:
        info = message['data'].decode('utf-8')
        data = json.loads(info)
        if data['command'] == "LIVE":
            _on_live(data['data'])
    except redis.exceptions.ConnectionError as e:
        print(f'解析 redis 時出現錯誤: {e}')
    except JSONDecodeError as e:
        print(f'解析 json 時出現錯誤: {e}')

def initRedis(host: str = "127.0.0.1", port: int = 6379, database: int = 0):
    return redis.Redis(host, port, database)


def startRooms(rooms: List[int], redis_info: Any):
    try:
        rc = initRedis(redis_info['host'], redis_info['port'], redis_info['database'])
        pubsub = rc.pubsub()
        room_subscribed = {}
        for room in rooms:
            print('add room' + str(room))
            room_subscribed[f'blive:{room}'] = handle_ws
        pubsub.subscribe(**room_subscribed)
        t = pubsub.run_in_thread(sleep_time=0.1)
    except redis.exceptions.ConnectionError as e:
        print(f'初始化 redis 時出現錯誤, 等待五秒重啟: {e}')
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print(f'等待被手動中止')


if __name__ == '__main__':
    f = open('./settings/config.json')
    data = json.load(f)
    listen_room = data['rooms']
    token = data['token']
    global bot, userId
    userId = int(data['toUser'])
    bot = telegram.Bot(token=token)
    redis_info = data['redis']
    startRooms(listen_room, redis_info)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(listen_room))
