import json
import requests
from copy import copy
from random import randint
from _G import log_debug,log_error,log_info,log_warning
from base64 import b64decode

LONG_MAX_VAL = 0xffffffff

POST_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/json',
    'Connection': 'keep-alive',
    'Host': 'api.novelai.net',
    'Origin': 'https://novelai.net',
    'Referer': 'https://novelai.net/',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0',
    'TE': 'trailers',
    'Authorization': '',
}

IMG_GEN_INPUT = {
    'input': 'masterpiece, best quality',
    'model': 'nai-diffusion',
    'parameters': {
        'n_samples': 1,
        'sampler': 'k_euler_ancestral',
        'scale': 11,
        'steps': 28,
        'seed': 20221010,
        'height': 768,
        'width': 512,
        'ucPreset': 0,
        'uc': "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
    }
}


class ImageGenRequest:
    def __init__(self):
        self.out_name = ''
        self.tags = ''
        self.seed = ''
        self.width = 512
        self.height = 768
        self.scale = 11
        self.steps = 28
        self.n_samples = 1
        self.sampler = 'k_euler_ancestral'

IMAGE_QUEUE = [None] * 20

def generate_image(out_name, tags, seed=None):
    global POST_HEADERS,IMG_GEN_INPUT
    payload = copy(IMG_GEN_INPUT)
    payload['input'] += ', '+tags
    if seed == None or type(seed) != int or seed > LONG_MAX_VAL:
        payload['seed'] = randint(0, LONG_MAX_VAL)
    res = requests.post(
        'https://api.novelai.net/ai/generate-image',
        json.dumps(payload),
        headers=POST_HEADERS
    )
    if res.status_code != 201:
        log_error("An error occurred during generating image")
        log_error(res, res.json())
        return False
    raw = res.content.decode().split('\n')[2]
    with open(out_name, 'wb') as fp:
        fp.write(b64decode(raw[2].split('data:')[1]))
    return out_name
    