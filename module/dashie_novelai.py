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

from dashiebot import Bot, verify_permission

NAI_API_TOKEN = os.getenv('NAI_API_TOKEN')
NAI_API_HOST  = os.getenv('NAI_API_HOST')

NAI_API_HEADERS = {
    'Accept-Encoding': 'gzip, deflate',
    'Accept': '*/*',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'User-Agent': os.getenv('NAI_API_USERAGENT')
}

def request_nai_gen(fname, params):
    res = requests.post(f"{NAI_API_HOST}/api/RequestNaiImage", json.dumps(params), headers=NAI_API_HEADERS)
    if res.status_code == 200:
        with open(fname, 'wb') as fp:
            fp.write(b64decode(res.json()['data']))
    return res


UCP_OPTIONS = ['Low Quality + Bad Anatomy', 'Low Quality', 'None']

@Bot.slash_command(name='naigen', 
    description="Novel AI image generation",
    guild_ids=_G.collect_scmd_guids('naigen')
)
@option(
    'tags', str,
    description='Prompt for generating image',
    required=True,
)
@option(
    'model', str,
    description='Model to use',
    choices=['naf', 'nac', 'fur'],
    default='naf'
)
@option(
    'sampler', str,
    description='Sampler to use',
    choices=['k_euler_ancestral', 'k_euler', 'k_lms', 'plms', 'ddim'],
    default='k_euler_ancestral'
)
@option(
    'steps', int,
    description='Interations to refine the image',
    default=28,
    min_value=1,
    max_value=28,
)
@option(
    'scale', int,
    description='Prompt followness',
    default=11,
    min_value=1,
    max_value=99,
)
@option(
    'seed', int,
    description='Randomness seed',
    min_value=0,
    max_value=0xffffffff,
    required=False
)
@option(
    'ucp', str,
    description='Preset Undesired content.',
    choices=['Low Quality + Bad Anatomy', 'Low Quality', 'None'],
    default='Low Quality + Bad Anatomy'
)
@option(
    'uc', str,
    description='Undesired content',
    default=''
)
@verify_permission
async def naigen(ctx, tags, model, sampler, steps, scale, seed, ucp, uc):
    await ctx.respond(f"Please wait while generating image with `{tags}`")
    ucp = UCP_OPTIONS.index(ucp)
    params = {
        'tags': tags,
        'model': model,
        'sampler': sampler,
        'steps': steps,
        'scale': scale,
        'uc': uc,
        'ucp': ucp
    }
    log_info(f"{ctx.author.name}: {tags}\n{params}")
    if seed:
        params['seed'] = seed

    params['token'] = NAI_API_TOKEN
    loop = Bot.loop
    fname = f"cache/.{hash(str(datetime.now())+ctx.author.name+tags)}.png"
    res = await loop.run_in_executor(None, request_nai_gen, fname, params)
    if res.status_code == 200:
        with open(fname, 'rb') as fp:
            await ctx.respond(f"seed: {res.json()['seed']}", file=discord.File(fp))
    else:
        await ctx.respond(f"Generation failed with status {res}")

def reload():
    return requests.post(
        f"{NAI_API_HOST}/api/ReloadConfig", 
        json.dumps({'token': os.getenv('FLASK_REFRESH_KEY')}), 
        headers=NAI_API_HEADERS
    )

async def update():
    pass

def init():
    pass