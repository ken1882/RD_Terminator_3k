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
MODULE_FFXIV   = False
MODULE_MTDNEWS = True
MODULE_TSKNEWS = True
MODULE_MSTNEWS = True
MODULE_TWITTER = True

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
  return datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M:%S')

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