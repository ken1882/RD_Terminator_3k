import _G
from _G import log_debug,log_error,log_info,log_warning,handle_exception
import os
import discord
import json
from typing import Union
from discord.ext import commands
from discord import option
from datetime import datetime,timedelta
from base64 import b64decode
import requests
from threading import Thread
from time import sleep
from pprint import pprint

NAI_API_TOKEN = os.getenv('NAI_API_TOKEN')
NAI_API_HOST  = os.getenv('NAI_API_HOST')

_intents = discord.Intents.default()
_intents.message_content = True
Bot = commands.Bot(
    command_prefix='>',
    intents=_intents,
    # help_command=commands.DefaultHelpCommand(
    #     no_category='commands'
    # )
)

NAI_API_HEADERS = {
    'Accept-Encoding': 'gzip, deflate',
    'Accept': '*/*',
    'Connection': 'keep-alive',
    'User-Agent': os.getenv('NAI_API_USERAGENT')
}

def isCommandCDOk(ctx):
    if ctx.guild:
        gid = str(ctx.guild.id)
    else:
        gid = 0
    if gid == 0:
        return True
    cmd = str(ctx.command)
    try:
        ldat = _G.PermissionData[gid]['commands'][cmd]
    except Exception:
        return True
    
    # pprint(_G.CommandLimit)
    cdat = _G.CommandLimit[gid][cmd]
    if 'limit' not in ldat or 'cooldown' not in ldat:
        return True

    curt = datetime.now()
    if cdat['total'] >= ldat['limit']:
        if curt >= cdat['ttl']:
            cdat['ttl'] = curt + timedelta(seconds=ldat['cooldown'])
            cdat['total'] = 0
        else:
            ctx.message = f"Server command limit reached, try after {str(cdat['ttl'])}"
            return False
    
    aid = ctx.author.id
    if aid in cdat and curt < cdat[aid]:
        ctx.message = f"Your command is in cooldown, try after {str(cdat[aid])}"
        return False
    
    cdat['total'] += 1
    cdat[aid] = curt + timedelta(seconds=ldat['cooldown'])
    return True

def isCommandUsable(ctx):
    aid = ctx.author.id
    if ctx.guild:
        gid = str(ctx.guild.id)
        roles = ctx.author.roles
    else:
        gid = 0
        roles = []
    cmd = str(ctx.command)
    if str(aid) in os.getenv('DEVELOPER_ID').split(','):
        return True    
    if gid == 0 and str(aid) not in os.getenv('DEVELOPER_ID').split(','):
        return False
    if gid not in _G.PermissionData:
        return False
    if cmd not in _G.PermissionData[gid]['commands']:
        return False
    if _G.PermissionData[gid]['commands'][cmd]['roles'][0] == 0:
        return True
    return any([r.id in _G.PermissionData[gid]['commands'][cmd]['roles'] for r in roles])

def _verify_permission(ctx):
    if not isCommandUsable(ctx):
        ctx.message = "You don't have permission to execute this command"
        return False
    elif not isCommandCDOk(ctx):
        return False
    return True

verify_permission = commands.check(_verify_permission)


@Bot.event
async def on_ready():
    print(f"{Bot.user.name} has connected to Discord!")

@Bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title="Command not found. Please try --help", color=0xCC0066)
        await ctx.channel.send(embed=embed)
    elif isinstance(error, commands.CheckFailure):
        await ctx.reply("You don't have permission to execute this command!")
    else:
        log_error("Command error has occurred")
        handle_exception(error)
        await ctx.reply("Command failed with unknown error")

@Bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, discord.errors.CheckFailure):
        await ctx.respond(ctx.message)
    else:
        log_error("Application command error has occurred")
        handle_exception(error)
        await ctx.respond("Command failed with unknown error")

@Bot.command(name='ping')
@verify_permission
async def ping(ctx):
    msg = f"🏓 Pong! {round(Bot.latency * 1000)}ms"
    return await ctx.reply(msg)

@Bot.command(name='reload')
@verify_permission
async def reload(ctx):
    _G.reload()
    requests.post(
        f"{NAI_API_HOST}/api/ReloadConfig", 
        json.dumps({'token': os.getenv('FLASK_REFRESH_KEY')}), 
        headers=NAI_API_HEADERS
    )
    return await ctx.reply('Configuation reloaded')

def request_nai_gen(fname, params):
    res = requests.post(f"{NAI_API_HOST}/api/RequestNaiImage", params, headers=NAI_API_HEADERS)
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

def run():
    Bot.run(os.getenv('DC_BOT_TOKEN'))