import _G
import dashiebot
from time import sleep
from dashiebot import Bot
from threading import Thread
from discord.ext import tasks

if _G.MODULE_NOVELAI:
    import module.dashie_novelai as dashie_novelai
    Bot.dashie_modules.append(dashie_novelai)

if _G.MODULE_FFXIV:
    import module.dashie_ffxiv as dashie_ffxiv
    Bot.dashie_modules.append(dashie_ffxiv)

if _G.MODULE_MTDNEWS:
    import module.mtd_news as mtd_news
    Bot.dashie_modules.append(mtd_news)

if _G.MODULE_TSKNEWS:
    import module.tsk_news as tsk_news
    Bot.dashie_modules.append(tsk_news)

if _G.MODULE_MSTNEWS:
    import module.mst_news as mst_news
    Bot.dashie_modules.append(mst_news)

if _G.MODULE_TWITTER:
    import module.twitter as twitter
    Bot.dashie_modules.append(twitter)

if __name__ == '__main__':
    try:
        dashiebot.run()
    finally:
        print("loop closed")
        _G.FlagRunning = False