import _G
from _G import log_debug,log_error,log_info,log_warning,handle_exception
import os
import discord
import json
from discord.ext import commands
from datetime import datetime
from base64 import b64decode
import requests

NAI_API_TOKEN = os.getenv('NAI_API_TOKEN')
NAI_API_HOST  = os.getenv('NAI_API_HOST')

_intents = discord.Intents.default()
_intents.message_content = True
Bot = commands.Bot(
    command_prefix='>',
    intents=_intents,
    help_command=commands.DefaultHelpCommand(
        no_category='commands'
    )
)

PermissionData = {}

def isCommandAuthorized(cmd, author, guild):
    global PermissionData
    aid = author.id
    gid = str(guild.id) if guild else 0
    roles = author.roles
    cmd = str(cmd)
    if str(aid) in os.getenv('DEVELOPER_ID').split(','):
        return True    
    if gid == 0 and str(aid) not in os.getenv('DEVELOPER_ID').split(','):
        return False
    if gid not in PermissionData:
        return False
    if cmd not in PermissionData[gid]['commands']:
        return False
    if PermissionData[gid]['commands'][cmd][0] == 0:
        return True
    return any([r.id in PermissionData[gid]['commands'][cmd] for r in roles])

def _verify_permission(ctx):
    global PermissionData
    return isCommandAuthorized(ctx.command, ctx.author, ctx.guild)

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

@Bot.command(name='ping')
@verify_permission
async def ping(ctx):
    msg = f"🏓 Pong! {round(Bot.latency * 1000)}ms"
    return await ctx.reply(msg)


@Bot.command(name='naigen')
@verify_permission
async def naigen(ctx, tags, *args):
    await ctx.reply(f"Please wait while generating image with `{tags}`")
    params = {
        'token': NAI_API_TOKEN,
        'tags': tags
    }
    
    for kv in args:
        k,v = kv.split('=')
        params[k] = v
    
    res = requests.post(f"{NAI_API_HOST}/api/RequestNaiImage", params)
    fname = f".{hash(str(datetime.now())+ctx.author.name+tags)}.png"
    if res.status_code == 200:
        with open(fname, 'wb') as fp:
            fp.write(b64decode(res.json()['data']))
        with open(fname, 'rb') as fp:
            return await ctx.reply(file=discord.File(fp))
    else:
        return await ctx.reply(f"Generation failed with status {res.status_code}")

def run():
    global PermissionData
    with open(_G.PERM_FILE, 'r') as fp:
        PermissionData = json.load(fp)
    Bot.run(os.getenv('DC_BOT_TOKEN'))