import os, sys
import json
import traceback
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

ENCODING = 'UTF-8'
IS_WIN32 = False
IS_LINUX = False

if sys.platform == 'win32':
  IS_WIN32 = True
elif sys.platform == 'linux':
  IS_LINUX = True

ARGV = {}

PRODUCTION = ((os.getenv('FLASK_ENV') or '').lower() == 'production')

# 0:NONE 1:ERROR 2:WARNING 3:INFO 4:DEBUG
VerboseLevel = 3
VerboseLevel = 4 if ('--verbose' in sys.argv) else VerboseLevel

FlagRunning = True
FlagPaused  = False
FlagWorking = False
FlagReady   = False

ERRNO_OK          = 0x0
ERRNO_LOCKED      = 0x1
ERRNO_UNAUTH      = 0x2
ERRNO_BADDATA     = 0x3
ERRNO_MAINTENANCE = 0x10
ERRNO_DAYCHANGING = 0x11
ERRNO_FAILED      = 0xfe
ERRNO_UNAVAILABLE = 0xff

SERVER_TICK_INTERVAL = 60


PERM_FILE = '.permission.json'
PermissionData = {}
CommandLimit   = {}

MODULE_NOVELAI = False
MODULE_FFXIV   = True
MODULE_MTDNEWS = True

MTD_NEWS_TAG = {
  1: 'MAINTENANCE',
  2: 'UPDATE',
  3: 'GACHA',
  4: 'EVENT',
  5: 'CAMPAIGN',
  6: 'BUG',
  7: 'MISC',
}

MTD_NEWS_ICON = {
  1: 'https://cdn-icons-png.flaticon.com/512/777/777081.png',
  2: 'https://cdn.icon-icons.com/icons2/1508/PNG/512/updatemanager_104426.png',
  3: 'https://cdn-icons-png.flaticon.com/512/4230/4230567.png',
  4: 'https://cdn-icons-png.flaticon.com/512/4285/4285436.png',
  5: 'https://cdn-icons-png.flaticon.com/512/3867/3867424.png',
  6: 'https://www.iconsdb.com/icons/preview/red/error-7-xxl.png',
  7: 'https://cdn-icons-png.flaticon.com/512/1827/1827301.png'
}

MTD_NEWS_COLOR = {
  1: 0xfc3aef,
  2: 0x5299f7,
  3: 0xfad73c,
  4: 0x50faf4,
  5: 0xff5cb0,
  6: 0xdb043e,
  7: 0xcccccc,
}

MTD_VOCAB_JP = {
  'NEWS_TAG': {
    1: 'メンテナンス',
    2: 'アップデート',
    3: 'ガチャ',
    4: 'イベント',
    5: 'キャンペーン',
    6: '不具合',
    7: 'その他',
  }
}

def reload():
  global PermissionData,CommandLimit
  with open(PERM_FILE, 'r') as fp:
    PermissionData = json.load(fp)
  for g in PermissionData:
    if 'commands' not in PermissionData[g]:
      continue
    CommandLimit[g] = {}
    for cmd in PermissionData[g]['commands']:
      CommandLimit[g][cmd] = {
        'total': 0,
        'ttl': datetime.now()
      }
reload()


def collect_scmd_guids(cmd):
  global PermissionData
  ret = []
  for g in PermissionData:
    if 'commands' not in PermissionData[g]:
      continue
    if cmd not in PermissionData[g]['commands']:
      continue
    ret.append(int(g))
  return ret

def format_curtime():
  return datetime.strftime(datetime.now(), '%H:%M:%S')

def log_error(*args, **kwargs):
  if VerboseLevel >= 1:
    print(f"[{format_curtime()}] [ERROR]:", *args, **kwargs)

def log_warning(*args, **kwargs):
  if VerboseLevel >= 2:
    print(f"[{format_curtime()}] [WARNING]:", *args, **kwargs)

def log_info(*args, **kwargs):
  if VerboseLevel >= 3:
    print(f"[{format_curtime()}] [INFO]:", *args, **kwargs)

def log_debug(*args, **kwargs):
  if VerboseLevel >= 4:
    print(f"[{format_curtime()}] [DEBUG]:", *args, **kwargs)

def handle_exception(err):
  err_info = traceback.format_exc()
  msg = f"{err}\n{err_info}\n"
  log_error(msg)