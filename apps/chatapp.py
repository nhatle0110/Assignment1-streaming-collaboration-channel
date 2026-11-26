"""
apps.chatapp  [Owner: TV1 - Le Minh Nhat]

StreapRous HTTP routes (/api/*) bridging the browser UI to one user's Agent:
  POST /api/login, /api/send, /api/logout, /api/events, /api/file/offer, /api/file/respond
"""
import json
from urllib.parse import unquote

from daemon import StreapRous


def _json(body):
    # TODO (TV1): parse JSON body safely (return {} on error)
    raise NotImplementedError


def _reply(obj):
    # TODO (TV1): serialize dict to UTF-8 JSON bytes
    raise NotImplementedError


def build_app(agent):
    # TODO (TV1): create StreapRous() app and register the 6 POST /api/* routes calling agent
    raise NotImplementedError


def create_chatapp(ip, port, agent):
    # TODO (TV1): build_app(agent), prepare_address(ip, port), and app.run()
    raise NotImplementedError
