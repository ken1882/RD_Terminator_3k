import _G
from _G import log_debug,log_error,log_info,log_warning,handle_exception
import os
import discord
import json
from discord.ext import commands
from discord import option
from datetime import datetime,timedelta
from base64 import b64decode
import requests
from time import sleep
from pprint import pprint
from bs4 import BeautifulSoup as BS
import asyncio

from dashiebot import Bot, verify_permission

FFXIV_TIMER_HEADERS = {
    'Accept-Encoding': 'gzip, deflate',
    'Accept': '*/*',
    'Connection': 'keep-alive',
    'User-Agent': os.getenv('FFXIV_USERAGENT')
}

TIMEZONE_DELTA = 0
TIMER_FILE = '.ffxiv-timers.json'
TimerNewsWebhook = os.getenv('FFXIV_TIMER_WEBHOOK')
LastTimers = {}

try:
    with open(TIMER_FILE, 'r') as fp:
        LastTimers = json.load(fp)
except Exception:
    pass

def get_timers():
    return requests.get(
        'https://www.xenoveritas.org/static/ffxiv/timers.json',
        headers=FFXIV_TIMER_HEADERS
    )

def get_new_timers(olds, news):
    ret_new = []
    ret_end = []
    for i in news:
        found = False
        for j in olds:
            if i['name'] == j['name']:
                found = True
                break
        if not found:
            ret_new.append(i)
    return [ret_new, ret_end]

async def update():
    global LastTimers
    pass
    # res = get_timers()
    # try:
    #     dat  = res.json()
    #     if 'timers' not in LastTimers:
    #         LastTimers['timers'] = []
    #     news, olds = get_new_timers(LastTimers['timers'], dat['timers'])
    #     LastTimers = dat
    #     with open(TIMER_FILE, 'w') as fp:
    #         json.dump(LastTimers, fp)
    #     await send_new_events(news)
    # except Exception as err:
    #     _G.handle_exception(err)

def send_new_events(news):
    global TimerNewsWebhook
    if not TimerNewsWebhook:
        return
    for n in news:
        node = BS(n['name'], 'lxml')
        title = node.text
        href = node.find('a')['href']
        st = datetime.fromtimestamp(n['start']//1000)+timedelta(hours=TIMEZONE_DELTA)
        ed = datetime.fromtimestamp(n['end']//1000)+timedelta(hours=TIMEZONE_DELTA)
        tz = TIMEZONE_DELTA
        msg  = f"{href}\n---\n"
        msg += f"**{title}**\n"
        msg += f"Starts at:\n{st.strftime('%Y/%m/%d %H:%M:%S')} (UTC{'+' if tz >= 0 else ''}{8+tz})\n"
        msg += f"Ends at:\n{ed.strftime('%Y/%m/%d %H:%M:%S')} (UTC{'+' if tz >= 0 else ''}{8+tz})\n"
        _G.log_info(msg)
        requests.post(TimerNewsWebhook, json={'content': msg})

def reload():
    pass

def init():
    pass