import _G
import traceback

def handle_exception(err):
  errinfo = traceback.format_exc()
  _G.log_error(f"An error occured!\n{str(err)}\n{errinfo}")

def chunk(it, n):
  return [it[i * n:(i + 1) * n] for i in range((len(it) + n - 1) // n )]