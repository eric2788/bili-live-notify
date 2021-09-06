import requests
import asyncio
# noinspection PyPackageRequirements
import telegram

from blivedm import BLiveClient
import json


class Spider(BLiveClient):

    def __init__(self, room_id: int, userId: int, name: str = None): # name can make custom
        super().__init__(room_id)
        self.title = None
        self.bilibili_uid = 0
        self.user_cover = None
        self.name = name
        self.r1 = None
        self.userId = userId

    def get_live_info(self):
        r = requests.get('https://api.live.bilibili.com/room/v1/Room/get_info?room_id=%s' % self.room_id,
                         headers={
                             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                           'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'})

        if r.status_code == 200:
            data = r.json()['data']
            self.title = data['title']
            self.bilibili_uid = data['uid']
            self.user_cover = data['user_cover']
            return data

    def get_user_info(self):
        r = requests.get('https://api.bilibili.com/x/space/acc/info?mid=%s&jsonp=jsonp' % self.bilibili_uid,
                           headers={
                             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                           'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'})
        if r.status_code == 200:
            data = r.json()['data']
            self.name = data['name']


    _COMMAND_HANDLERS = BLiveClient._COMMAND_HANDLERS.copy()

    async def _on_live(self, command):
        print(command)
        if self.live_status:
            return
        self.get_live_info()
        if not self.name:
            self.get_user_info()
        self.live_status = True
        caption = '<a href="https://space.bilibili.com/' + str(self.bilibili_uid) + '">' + self.name + '</a> 正在直播\n'
        caption += '标题： ' + self.title + '\n'
        reply_markup = telegram.InlineKeyboardMarkup(
            [[telegram.InlineKeyboardButton('直播间', url='https://live.bilibili.com/' + str(self.room_id))]])
        if len(self.user_cover) > 0:
            self.r1 = bot.sendPhoto(self.userId, self.user_cover, caption=caption, parse_mode='html',
                                    reply_markup=reply_markup)
            bot.pinChatMessage(self.userId, self.r1.message_id)
        else:
            self.r1 = bot.send_message(self.userId, caption, parse_mode='html', reply_markup=reply_markup)
            bot.pinChatMessage(self.userId, self.r1.message_id, True)

    async def _on_prepare(self, command):
        _ = command
        self.live_status = False
        print('%d 准备中' % self.room_id)
        if self.r1:
            bot.unpin_chat_message(self.userId, api_kwargs=dict(message_id=self.r1.message_id))

    # noinspection PyTypeChecker
    _COMMAND_HANDLERS['LIVE'] = _on_live
    # noinspection PyTypeChecker
    _COMMAND_HANDLERS['PREPARING'] = _on_prepare


async def start(rooms: list, data):
    for room in rooms:
        print('add room' + str(room))
        task = Spider(room, int(data['toUser']))
        await task.init_room()
        task.start()
    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    f = open('./settings/config.json')
    data = json.load(f)
    listen_room = data['rooms']
    token = data['token']
    bot = telegram.Bot(token=token)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(listen_room, data))
