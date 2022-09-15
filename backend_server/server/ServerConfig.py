import logging
import uuid

SERVER_NAME = "Primary"
SERVER_PORT = 32073
SERVER_FPS = 60.0   # should read back from a config file, but this will do for now
SERVER_FRAME_QUOTA = 2.0/SERVER_FPS

PING_FREQUENCY = 3.0  # once per second if nothing else
LATENCY_BUFFER_LENGTH = 10  # how many latency samples will be stored and averaged to get an average latency measurement
NONACTIVITY_GRACE_PERIOD = 300.0  # if users do absolutely nothing for this amount of seconds the match will be terminated
NONACTIVITY_WARNING_PERIOD = 240.0  # if users do absolutely nothing for this amount of seconds a warning will be sent

VISUALIZE = False
ALLOW_DEBUG = True
ALLOW_DEBUG_COMMANDS = True

MATCH_UNIT_CAP = 400

MONGODB_HOST = "10.0.0.1"
MONGODB_PORT = 27017

FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 7070
FRONTEND_USERNAME = "th_frontend"
FRONTEND_PASSWORD = "e5e6af02519f110093d76dcc1f55b25d"

MATCHDEF_PATH = "matchdefs/"
MATCHLOG_PATH = "matchlogs/"
PERFLOG_PATH = "perflogs/"
WRITE_MATCH_LOGS_TO_FILE = True

GA_GAME_KEY = "100a05cb03fe3e06abc8ea46ece77719"
GA_SECRET_KEY = "f3da55791fa55ae43c0caf6b93ba7bf457123b08"
GA_ENDPOINT_URL = "http://api.gameanalytics.com/1"

MAC_ADDRESS = uuid.getnode()
MAC_HASH = ''.join([x.upper() for x in ''.join(['{:02x}'.format((MAC_ADDRESS >> i) & 0xff) for i in range(0,8*6,8)][::-1])])

LOG_LEVEL = logging.INFO
LOG_IGNORE = [ "PING", "PONG", "SET", "E_SET", "E_MOV_REQ", "E_MOV_RES", "G_MAP_PROP", "E_CREAT", "G_MAP_HEIGHT", "G_MAP_DEF", "G_MAP_SET" ]
