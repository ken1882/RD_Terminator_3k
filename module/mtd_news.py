import requests
import json
import os
import _G
from datetime import datetime
import utils

PREV_NEWS_FILE = '.mtd_prevnews.json'

NEWS_URL    = os.getenv('MTD_NEWS_URL')
WEBHOOK_URL = os.getenv('MTD_WEBHOOK_URL')

MTD_NEWS_TAG = {
  1: 'MAINTENANCE',
  2: 'UPDATE',
  3: 'GACHA',
  4: 'EVENT',
  5: 'CAMPAIGN',
  6: 'BUG',
  7: 'MISC',
}

MTD_NEWS_ICON = {
  1: 'https://cdn-icons-png.flaticon.com/512/777/777081.png',
  2: 'https://cdn.icon-icons.com/icons2/1508/PNG/512/updatemanager_104426.png',
  3: 'https://cdn-icons-png.flaticon.com/512/4230/4230567.png',
  4: 'https://cdn-icons-png.flaticon.com/512/4285/4285436.png',
  5: 'https://cdn-icons-png.flaticon.com/512/3867/3867424.png',
  6: 'https://www.iconsdb.com/icons/preview/red/error-7-xxl.png',
  7: 'https://cdn-icons-png.flaticon.com/512/1827/1827301.png'
}

MTD_NEWS_COLOR = {
  1: 0xfc3aef,
  2: 0x5299f7,
  3: 0xfad73c,
  4: 0x50faf4,
  5: 0xff5cb0,
  6: 0xdb043e,
  7: 0xcccccc,
}

MTD_VOCAB_JP = {
  'NEWS_TAG': {
    1: 'メンテナンス',
    2: 'アップデート',
    3: 'ガチャ',
    4: 'イベント',
    5: 'キャンペーン',
    6: '不具合',
    7: 'その他',
  }
}

def get_webhook_url():
    global WEBHOOK_URL
    return WEBHOOK_URL

def get_news_data():
    return requests.get(NEWS_URL).json()['newsList']

def get_old_news():
    ret = {}
    if not os.path.exists(PREV_NEWS_FILE):
        ret = get_news_data()
        ret = sorted(ret, key=lambda o: -o['id'])
        with open(PREV_NEWS_FILE, 'w') as fp:
            json.dump(ret, fp)
    else:
        with open(PREV_NEWS_FILE, 'r') as fp:
            ret = json.load(fp)
    return ret


async def update():
    news = {}
    try:
        news = get_news_data()
        news = sorted(news, key=lambda o: -o['id'])
    except Exception as err:
        utils.handle_exception(err)
        return
    olds = get_old_news()
    o_cksum = int(datetime.fromisoformat(olds[0]['postedAt']).timestamp())
    n_cksum = int(datetime.fromisoformat(news[0]['postedAt']).timestamp())
    if o_cksum > n_cksum:
        _G.log_warning(f"Old news newer than latest news ({o_cksum} > {n_cksum})")
    elif o_cksum == n_cksum:
        # _G.log_info("No news, skip")
        return

    _G.log_info("Gathering news")
    ar = []
    for n in news:
        if n['id'] > olds[0]['id']:
            ar.append(n)
        else:
            break
    for a in ar:
        try:
            send_message(a)
        except Exception as err:
            utils.handle_exception(err)
    with open(PREV_NEWS_FILE, 'w') as fp:
        json.dump(news, fp)


def send_message(obj):
    payload = {}
    payload['embeds'] = [{
        'author': {
            'name': MTD_VOCAB_JP['NEWS_TAG'][obj['tag']],
            'icon_url': MTD_NEWS_ICON[obj['tag']],
        },
        'title': f"**{obj['title']}**",
        'description': f"<t:{int(datetime.fromisoformat(obj['postedAt']).timestamp())}>",
        'color': MTD_NEWS_COLOR[obj['tag']],
        'fields': []
    }]
    # this will fail if total length is over 6000
    for msg in utils.chunk(obj['message'], 1000):
        payload['embeds'][0]['fields'].append({
            'name': " \u200b", # zero-width space
            'value': msg
        })
    return requests.post(get_webhook_url(), json=payload)

def init():
    pass