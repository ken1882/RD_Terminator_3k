import _G
from _G import log_debug,log_error,log_info,log_warning,handle_exception
import os
import discord
import json
from discord.ext import commands, tasks
from discord import option
from datetime import datetime,timedelta
from base64 import b64decode
import requests
from time import sleep
from pprint import pprint

_intents = discord.Intents.default()
_intents.message_content = True
Bot = commands.Bot(
    command_prefix='>',
    intents=_intents,
    # help_command=commands.DefaultHelpCommand(
    #     no_category='commands'
    # )
)

Bot.dashie_modules = []

@tasks.loop(seconds=60)
async def main_loop():
    for m in Bot.dashie_modules:
        await m.update()

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
    for m in Bot.dashie_modules:
        m.init()
    _G.FlagReady = True
    await main_loop.start()

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
    for m in Bot.dashie_modules:
        m.reload()
    return await ctx.reply('Configuation reloaded')

def run():
    Bot.run(os.getenv('DC_BOT_TOKEN'))