import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup as BS
import _G
import utils
from tweety import Twitter
from tweety.types.twDataTypes import TweetThread

PREV_TWEETS_FILE = '.prevtweets.json'

TWITTER_LISTENERS = {
    'mist_staff': (
        os.getenv('MST_TWT_WEBHOOK'),
        os.getenv('MST_GAME_ROLE'),
    ),
    'monmusu_td': (
        os.getenv('MTD_TWT_WEBHOOK'),
        os.getenv('MTD_GAME_ROLE'),
    ),
    'starknights_PR': (
        os.getenv('TSK_TWT_WEBHOOK'),
        os.getenv('TSK_GAME_ROLE'),
    ),
    'EN_BlueArchive': (
        os.getenv('BAH_TWT_WEBHOOK'),
        os.getenv('BAH_GAME_ROLE'),
    ),
    'Blue_ArchiveJP': (
        os.getenv('BAH_TWT_WEBHOOK'),
        os.getenv('BAH_GAME_ROLE'),
    ),
    'azurlane_staff': (
        os.getenv('AZL_TWT_WEBHOOK'),
        os.getenv('AZL_GAME_ROLE'),
    ),
    'ff_xiv_jp': (
        os.getenv('FFXIV_TWT_WEBHOOK'),
        os.getenv('FFXIV_GAME_ROLE'),
    )
}

ACTIVE_HOURS    = []
LAZY_HOURS      = [range(20, 24), range(0, 9)]
NORMAL_INTERVAL = 5
LAZY_INTERVAL   = 30

Agent = None
TickCounter = 0
ErrorCnt = 0

def parse_tweet(tweet):
    ret = {}
    if not tweet.created_on:
        return None
    ret['id'] = int(tweet.id)
    ret['postedAt'] = int(tweet.created_on.timestamp())
    ret['message'] = tweet.text
    ret['account'] = tweet.author.username
    return ret

def get_new_tweets(account):
    global Agent
    ret = []
    try:
        tweets = Agent.get_tweets(account)
        for t in tweets:
            # only interpret first Thread level
            if type(t) == TweetThread:
                for t2 in t:
                    pt = parse_tweet(t2)
                    if pt:
                        ret.append(pt)
            else:
                pt = parse_tweet(t)
                if pt:
                    ret.append(pt)
    except Exception as err:
        utils.handle_exception(err)
        return []
    ret = sorted(ret, key=lambda o: -o['id'])
    return ret

def get_old_tweets(account, PREV_TWEETS_FILE):
    ret = []
    if not os.path.exists(PREV_TWEETS_FILE):
        ret = get_new_tweets(account)
        if not ret:
            return []
        with open(PREV_TWEETS_FILE, 'w') as fp:
            json.dump(ret, fp)
    else:
        with open(PREV_TWEETS_FILE, 'r') as fp:
            ret = json.load(fp)
    ret = sorted(ret, key=lambda o: -o['id'])
    return ret


async def update():
    global TWITTER_LISTENERS, Agent, TickCounter, ErrorCnt
    if not Agent:
        return
    TickCounter += 1
    err_threshold = len(TWITTER_LISTENERS.keys())
    if ErrorCnt > err_threshold:
        Agent = None
        connect_twitter()
    if any(datetime.now().hour in t for t in LAZY_HOURS) and TickCounter % LAZY_INTERVAL != 0:
        _G.log_debug(f"Lazy hour, skip (Tick={TickCounter})")
        return
    elif any(datetime.now().hour in t for t in ACTIVE_HOURS):
        _G.log_debug(f"Active hour (Tick={TickCounter})")
        pass
    elif TickCounter % NORMAL_INTERVAL != 0:
        _G.log_debug(f"Normal hour (Tick={TickCounter})")
        return
    for account, data in TWITTER_LISTENERS.items():
        webhook, dc_role_id = data
        _G.log_debug(f"Getting tweets from {account}")
        PREV_NEWS_FILE = f".{account}_prevtweets.json"
        news = []
        try:
            news = get_new_tweets(account)
            news = sorted(news, key=lambda o: -o['id'])
        except Exception as err:
            utils.handle_exception(err)
            continue
        if not news:
            _G.log_error("Unable to get new tweets")
            ErrorCnt += 1
            continue
        olds = get_old_tweets(account, PREV_NEWS_FILE)
        o_cksum = 0
        if olds:
            o_cksum = olds[0]['postedAt']
        n_cksum = news[0]['postedAt']
        if o_cksum > n_cksum:
            _G.log_warning(f"Old news newer than latest news ({o_cksum} > {n_cksum})")
        elif o_cksum == n_cksum and news[0]['message'] == olds[0]['message']:
            _G.log_debug("No news, skip")
            continue

        _G.log_info(f"Gathering {account} new tweets")
        ar = []
        for n in news:
            if not olds or n['id'] > olds[0]['id'] or (n['id'] == olds[0]['id'] and n['message'] != olds[0]['message']):
                ar.insert(0, n)
            else:
                break
        urls = []
        if webhook:
            urls = webhook.split(',')
        try:
            if ar and dc_role_id:
                roles = dc_role_id.split(',')
                for i,role in enumerate(roles):
                    if not role:
                        continue
                    requests.post(
                        urls[i],
                        json={
                            'content': f"<@&{role}>"
                        }
                    )
            for a in ar:
                for u in urls:
                    send_message(u, a)
        except Exception as err:
            utils.handle_exception(err)
        with open(PREV_NEWS_FILE, 'w') as fp:
            json.dump(news, fp)


def send_message(url, obj):
    return requests.post(
        url,
        json={
            'content': f"https://vxtwitter.com/{obj['account']}/status/{obj['id']}"
        }
    )

def connect_twitter():
    global Agent
    Agent = Twitter('session')
    try:
        Agent.connect()
        _G.log_info("Twitter connected")
    except Exception as err:
        utils.handle_exception(err)
        _G.log_info("Using username/pwd to sign in")
        Agent.sign_in(os.getenv('TWITTER_USERNAME'), os.getenv('TWITTER_PASSWORD'))

def init():
    connect_twitter()

def reload():
    pass
