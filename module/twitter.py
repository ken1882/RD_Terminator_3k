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
    'mist_staff': os.getenv('MST_TWT_WEBHOOK'),
    'starknights_PR': os.getenv('MTD_TWT_WEBHOOK'),
    'monmusu_td': os.getenv('TSK_TWT_WEBHOOK')
}

Agent = None

def parse_tweet(tweet):
    ret = {}
    ret['id'] = tweet.id
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
                    ret.append(parse_tweet(t2))
            else:
                ret.append(parse_tweet(t))
    except Exception as err:
        utils.handle_exception(err)
    ret = sorted(ret, key=lambda o: -o['id'])
    return ret

def get_old_tweets(account, PREV_TWEETS_FILE):
    ret = []
    if not os.path.exists(PREV_TWEETS_FILE):
        ret = get_new_tweets(account)
        with open(PREV_TWEETS_FILE, 'w') as fp:
            json.dump(ret, fp)
    else:
        with open(PREV_TWEETS_FILE, 'r') as fp:
            ret = json.load(fp)
    ret = sorted(ret, key=lambda o: -o['id'])
    return ret


async def update():
    global TWITTER_LISTENERS, Agent
    for account, webhook in TWITTER_LISTENERS.items():
        PREV_NEWS_FILE = f"{account}_prevtweets.json"
        news = []
        try:
            news = get_new_tweets(account)
            news = sorted(news, key=lambda o: -o['id'])
        except Exception as err:
            utils.handle_exception(err)
            return
        olds = get_old_tweets()
        o_cksum = 0
        if olds:
            o_cksum = int(datetime.fromisoformat(olds[0]['postedAt']).timestamp())
        n_cksum = int(datetime.fromisoformat(news[0]['postedAt']).timestamp())
        if o_cksum > n_cksum:
            _G.log_warning(f"Old news newer than latest news ({o_cksum} > {n_cksum})")
        elif o_cksum == n_cksum and news[0]['message'] == olds[0]['message']:
            # _G.log_info("No news, skip")
            return

        _G.log_info(f"Gathering {account} tweets")
        ar = []
        for n in news:
            if not olds or n['id'] > olds[0]['id'] or (n['id'] == olds[0]['id'] and n['message'] != olds[0]['message']):
                ar.insert(0, n)
            else:
                break
        for a in ar:
            try:
                send_message(webhook, a)
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

def init():
    global Agent
    Agent = Twitter('session')
    Agent.sign_in(os.getenv('TWITTER_USERNAME'), os.getenv('TWITTER_PASSWORD'))

def reload():
    pass