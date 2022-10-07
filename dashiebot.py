import _G
from _G import log_debug,log_error,log_info,log_warning
import os
import discord
import json
from discord.ext import commands


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

def verify_permission(func):
    global PermissionData
    async def wrapper(*args, **kwargs):
        msg = "You don't have permission to execute this command"
        if type(args[0]) == commands.Context:
            ctx = args[0]
            if isCommandAuthorized(ctx.command, ctx.author, ctx.guild):
                return await func(*args, **kwargs)
            return await ctx.reply(msg)            
    return wrapper


@Bot.event
async def on_ready():
    print(f"{Bot.user.name} has connected to Discord!")

@Bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title="Command not found. Please try --help", color=0xCC0066)
        await ctx.channel.send(embed=embed)
    else:
        log_error("Command error has occurred")
        log_error(error)

@Bot.command(name='ping')
@verify_permission
async def ping(ctx):
    msg = f"🏓 Pong! {round(Bot.latency * 1000)}ms"
    return await ctx.reply(msg)

def run():
    global PermissionData
    with open(_G.PERM_FILE, 'r') as fp:
        PermissionData = json.load(fp)
    Bot.run(os.getenv('DC_BOT_TOKEN'))