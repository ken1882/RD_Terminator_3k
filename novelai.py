import _G
import json
import requests
from copy import copy
from random import randint
from _G import log_debug,log_error,log_info,log_warning,handle_exception
from base64 import b64decode
from threading import Thread
from time import sleep
from pprint import pprint

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
        'ucPreset': 2,
        'uc': "lowres",
    }
}

def reload():
    global POST_HEADERS
    with open(_G.PERM_FILE, 'r') as fp:
        dat = json.load(fp)
        POST_HEADERS['Authorization'] = dat['0']['NAI_TOKEN']


VALID_SAMPLERS = (
    'k_euler_ancestral',
    'k_euler',
    'k_lms',
    'plms',
    'ddim'
)

VALID_MODELS = {
    'fur': 'nai-diffusion-furry',
    'nac': 'safe-diffusion',
    'naf': 'nai-diffusion'
}

UC_PRESET = {
    0: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry',
    1: 'lowres, text, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry',
    2: 'lowres',
}

def is_params_ok(tags, seed, steps, scale, sampler, model, uc, ucp):
    try:
        if len(tags) > 500 or len(uc) > 500:
            return False
        if steps < 1 or steps > 28:
            return False
        if seed < 0 or seed > LONG_MAX_VAL:
            return False
        if scale < 1 or scale > 99:
            return False
        if sampler not in VALID_SAMPLERS:
            return False
        if model not in VALID_MODELS:
            return False
        if ucp not in UC_PRESET:
            return False
    except Exception as err:
        handle_exception(err)
        return False
    return True

def generate_image(tags, seed=None, steps=28, scale=11, sampler='k_euler_ancestral', model='naf', uc='', ucp=0):
    global POST_HEADERS,IMG_GEN_INPUT
    payload = copy(IMG_GEN_INPUT)
    payload['input'] += ', '+tags
    if seed == None:
        seed = randint(0, LONG_MAX_VAL)
    if not is_params_ok(tags, seed, steps, scale, sampler, model, uc, ucp):
        return _G.ERRNO_BADDATA
    
    uc = f"{UC_PRESET[ucp]}, {uc}"
    payload['model'] = VALID_MODELS[model]
    payload['parameters']['seed']  = seed
    payload['parameters']['steps'] = steps
    payload['parameters']['scale'] = scale
    payload['parameters']['sampler'] = sampler
    payload['parameters']['ucPreset'] = ucp
    payload['parameters']['uc'] = uc
    log_info(f"Generating image with tags `{tags}`#{seed}")
    res = requests.post(
        'https://api.novelai.net/ai/generate-image',
        json.dumps(payload),
        headers=POST_HEADERS
    )
    if res.status_code != 201:
        log_error("An error occurred during generating image")
        log_error(res, res.json())
        return _G.ERRNO_FAILED
    log_info(f"Done image generation with tags `{tags}`#{seed}")
    raw = res.content.decode().split('\n')[2]
    return raw.split('data:')[1]