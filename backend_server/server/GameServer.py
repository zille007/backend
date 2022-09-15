from ServerConfig import *
from ServerVersion import *
import Match
import Enums
import ParsedMap
import txmongo

import string
import time
import json
import hashlib
import urllib2
import string
import logging
import traceback
from Lobby import Lobby
from utils import dictToNestedTuple, nestedListToNestedTuple

from twisted.application import internet, service
from twisted.web.iweb import IBodyProducer
from twisted.internet import protocol, reactor, defer, task
from twisted.protocols import basic
from twisted.web.client import Agent
from zope.interface import implements
from twisted.web.http_headers import Headers

#from txredis.client import RedisClient

import os
import sys
import urllib

class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class UserSession( object ):
    def sendRaw( self, data ):
        if self.isFakedUser:
            return

        self.transport.write( data )
        self.bytesOut += len(data)

    def sendCommand( self, cmd, data ):
        if self.isFakedUser:
            return

        if self.transport is not None:
            if( not data.has_key("t") and self.match is not None ):
                data["t"] = self.match.lastUpdate

            send_dict = { "cmd":cmd, "res_seq":-1, "data":data }

            json_str = json.dumps( send_dict )
            #if( cmd not in LOG_IGNORE ):
            #    self.log.debug( "(%s)=> %s: %s" % (self.username,cmd, data) )
            self.sendRaw( json_str + "\r\n" )
            self.commandsOut += 1
            self.lastCommandTimestamp = time.time()

        else:
            self.log.critical( "Transport is none in sendCommand(): user=%s/%s for match %s" % (self.screenname, self.username, self.match.matchToken if self.match is not None else "(null???)" ) )

    def sendReply( self, cmd, seq, data ):
        if self.isFakedUser:
            return

        if self.transport is not None:
            if( not data.has_key("t") and self.match is not None ):
                data["t"] = self.match.lastUpdate

            send_dict = { "cmd":cmd, "res_seq":seq, "data":data }
            json_str = json.dumps( send_dict )
            if( cmd not in LOG_IGNORE ):
                self.log.debug( "(%s)=> %s: %s " % (self.username, cmd, data) )
            self.commandsOut += 1
            self.sendRaw( json_str + "\r\n" )
            self.lastCommandTimestamp = time.time()
        else:
            self.log.critical( "Transport is none in sendReply() ???" )

    def pongRequest(self, seq_no, **kwargs):
        latency = (time.time() - self.match.startTime) - self.match.lastPing
        if len(self.latencyRecorder) is LATENCY_BUFFER_LENGTH:
            del self.latencyRecorder[0]
        self.latencyRecorder.append(latency)
        self.sendCommand("LATNC", {"last": latency, "avg": sum(self.latencyRecorder)/len(self.latencyRecorder)})

    #@defer.inlineCallbacks
    def authenticateRequest(self, seq_no, user="", password="", **kwargs):
        #mongo = self.protocol.factory.mongo
        #account = yield mongo.tatd.users.find_one({"username": user})

        srv = self.protocol.factory.server
        if srv.gracefulShutdownMode:
            self.log.error("User %s is not allowed to authenticate because server is in graceful shutdown mode")
            self.sendReply("AUTH_RES", seq_no, {
                "authenticated": False,
                "error": "Server is shutting down for maintenance."
            })
            return

        if user == "wrong" and password == "password" or not self.protocol.factory.server.authenticateLogin(user, password, ""):
            self.isAuthenticated = False
            self.sendReply( "AUTH_RES", seq_no,
                            {"authenticated":False,
                             "error":"Invalid username or password."} )
            self.rejectedAuths += 1
            self.log.warning( "Attempted login for user %s with invalid password. Rejections=%d" % (user, self.rejectedAuths) )
        else:
            if self.protocol.factory.server.authenticateFrontend( user, password ):
                self.log.info( "Frontend authentication successful.")
                self.isFrontend = True

            self.isAuthenticated = True
            self.username = unicode( user )
            self.screenname = unicode( self.username )
            self.log.info( "User %s logged in from %s" % (self.username, self.transport.getPeer().host) )
            self.sendReply( "AUTH_RES", seq_no,
                            {"authenticated":True,
                             "fps":self.protocol.factory.server.updateFrequency } )
            self.status = "Idle"

            if not self.isFrontend:
                self.protocol.factory.server.lobby.join(self)

    @defer.inlineCallbacks
    def joinRequest(self, seq_no, token="", hero=0, faction=0, name="", userType=0, user_id="", **kwargs):
        self.ga_user_id = user_id
        srv = self.protocol.factory.server
        if srv.gracefulShutdownMode:
            self.log.error("User %s is not allowed to join match %s because server is in graceful shutdown mode" % (self.username, token))
            cmd = "JOIN_RES"
            data = {
                "res": 0,
                "token": "invalid",
                "reason": "Server will be shutdown due to maintenance."
            }
            self.sendReply(cmd, seq_no, data)
            return
        mongo = self.protocol.factory.mongo

        # super ultra hack
        #self.log.info( "User %s joins")
        if hero > 2:
            factions = ( 0, 0, 0, 1, 1, 1, 0, 0 )
            heroes = ( 0, 1, 2, 1, 2, 0, 3, 4 )
            faction = factions[hero]
            hero = heroes[hero]

        self.requestedFaction = faction
        self.requestedHero = hero
        self.screenname = name
        self.userType = "Master" if userType is 0 else "Hero" if userType is 1 else "Observer"

        dbItems = yield mongo.tatd.items.find()
        self.items = self._parseDBItems(dbItems, self.itemNames)
        dbGems = yield mongo.tatd.gems.find()
        self.gems = self._parseDBItems(dbGems, self.gemNames)
        match = self.protocol.factory.server.findMatchByToken(token)

        if match is None:
            mapdb = mongo.tatd.maps
            prefabs = yield mongo.tatd.prefabs.find()

            mapdef = yield mapdb.find_one({"name": token})
            if mapdef is not None:
                # if we create our match through here always assume we need only one player to run
                match = self.protocol.factory.server.requestMatchWithMap(token, mapdef, prefabs)
                if match:
                    match.playersRequiredToStart = 1
                self.log.warning("Could not find match with token %s but it is a map; initializing a map-named match with a single player." % (token,))
                match.enableDirectConnect()
            else:
                self.log.error("Could not find match with token %s and no such map!" % (token,))
                cmd = "JOIN_RES"
                data = {
                    "res": 0,
                    "token": "invalid",
                    "reason": "Tried single-user but no such map!",
                }
                self.sendReply(cmd, seq_no, data)
                return

        if match is None:
            self.log.warning("Match join rejected for user %s with token %s: no such match and unable to create" % (self.username, token))
            cmd = "JOIN_RES"
            data = {
                "res": 0,
                "token": "invalid",
                "reason": "Could not create match"
            }
            self.sendReply(cmd, seq_no, data)
            return

        # Match will automatically query proper map + game setup from server
        if match.userCanJoin(self):
            self.match = match
            if self.match.allowedControl.has_key(self.username):
                self.userType = self.match.allowedControl[self.username].capitalize()

            if self.match.userItemAssignments.has_key(self.username):
                self.items = self.match.userItemAssignments[self.username] # self._parseDBItems(dbItems, self.match.userItemAssignments[self.username])
                #self.log.info( "Item assignments for user %s: %s" % (self.username, str(self.items)))

            if self.match.userGemAssignments.has_key(self.username):
                self.gems = self._parseDBItems(dbGems, self.match.userGemAssignments[self.username])

            if self.match.userProcAssignments.has_key(self.username):
                self.procs = self.match.userProcAssignments[self.username]

            team_rec = match.teamRecommendationForUser(self)
            self.playerIndex = match.allowedUsers[self.username][3]
            if team_rec != Enums.MATCH_TEAM_A and team_rec != Enums.MATCH_TEAM_B:
                # client doesn't support observing yet anyway, so reject any observer team on join for now
                self.log.info("User %s tried to join match with token %s, but the game is full." % (self.username, token))
                cmd = "JOIN_RES"
                data = {
                    "res": 0,
                    "token": "invalid",
                    "reason": "Game is full.",
                }
                match.writeToNetworkLog(True, [self.assignedId], cmd, data)
                self.sendReply(cmd, seq_no, data)
            else:
                cmd = "JOIN_RES"
                data = {
                    "res": 1,
                    "token": match.token,
                    "team": team_rec,
                    "faction": self.requestedFaction,
                    "name": self.screenname,
                    "user_type": self.userType,
                    "reason": "",
                }
                match.writeToNetworkLog(True, [self.assignedId], cmd, data)
                self.sendReply(cmd, seq_no, data)
                if match.join(self, team_rec):
                    self.log.info("User %s joined team %d on match %s, switching to match logger..." % (self.username, team_rec, match.token))
                    self.log = self.match.log
                    # TODO: make this be called automatically by match
                    #self.match.syncState(self,hero)
                else:
                    self.log.warning("User %s tried to join team %d on match %s but join failed!" % (self.username, team_rec, token))
                    cmd = "JOIN_RES"
                    data = {
                        "res": 0,
                        "token": "invalid",
                        "reason": "Could not join match!",
                    }
                    self.sendReply(cmd, seq_no, data)
        else:
            self.log.error("User %s is not allowed to join match %s" % (self.username, token))
            cmd = "JOIN_RES"
            data = {
                "res": 0,
                "token": "invalid",
                "reason": "Game is full.",
            }
            match.writeToNetworkLog(True, [self.assignedId], cmd, data)
            self.sendReply(cmd, seq_no, data)


    def frontendMatchItemAssignRequest(self, seq_no, token="", user="", stuff_list=""):
        try:
            match = self.protocol.factory.server.findMatchByToken(token)
            items = stuff_list["item"]
            gems = stuff_list["gem"]
            procs = stuff_list["procs"]

            if len(user) > 0 and type(items) is list:
                match.assignItemsForUsername(user, items)

            if len(user) > 0 and type(gems) is list:
                match.assignGemsForUsername(user, gems)

            if len(user) > 0 and type(procs) is list:
                match.assignProcsForUsername(user, procs)
            self.sendReply("FE_ITEM_RES", seq_no, {"res":1, "token":token})
        except Exception as e:
            self.log.critical("Invalid item assignment to user %s; item list: %s; exception: %s" % (user, str(stuff_list), str(e)))
            self.sendReply("FE_ITEM_RES", seq_no, {"res":0, "token":"invalid"})

    @defer.inlineCallbacks
    def frontendMatchCreationRequest(self, seq_no, token = "", map_name = "",  req_players = 2, player_limit = 4, team_max = 2, item_dict = None, allowed_users = None, user_control = {}, ai_difficulty="medium" ):
        mongo = self.protocol.factory.mongo
        mapdb = mongo.tatd.maps
        prefabs = yield mongo.tatd.prefabs.find()

        mapdef = yield mapdb.find_one( {"name":map_name } )
        if self.isFrontend:
            match = self.protocol.factory.server.requestMatchWithMap( token, mapdef, prefabs )
            match.mapName = map_name
            match.playersRequiredToStart = req_players
            match.allowedUsers = allowed_users
            match.allowedControl = user_control
            match.aiDifficulty = ai_difficulty

            self.log.info( "Frontend match creation request with AI difficulty %s" % (match.aiDifficulty,))

            for k in item_dict.keys():
                self.frontendMatchItemAssignRequest( seq_no, token, k, item_dict[k] )

            if match is not None:
                # report back to the frontend server
                self.protocol.factory.server.sendHTTPRequest("GET", "http://%s:%d/internal_match_update/%s/created" % (FRONTEND_HOST, FRONTEND_PORT, str(token)))
                self.log.info( "Frontend created match %s with map %s, players required: %d" % (token,map_name,match.playersRequiredToStart))

            else:
                self.log.critical( "Frontend tried to create match %s with map %s but could not create it!" % (token, map_name) )

    @defer.inlineCallbacks
    def frontendMatchSetupRequest(self, seq_no, token= "", map_name = "", playerConfig = {}, tutorial = False ):
        mongo = self.protocol.factory.mongo
        mapdb = mongo.tatd.maps
        prefabs = yield mongo.tatd.prefabs.find()

        mapdef = yield mapdb.find_one( {"name":map_name } )
        self.log.info( "Frontend match creation req for token %s; playerConfig=%s" % (token, str(playerConfig) ))
        if self.isFrontend:
            match = self.protocol.factory.server.requestMatchWithMap( token, mapdef, prefabs )
            match.mapName = map_name

            humans = 0
            ais = 0
            for t in playerConfig.keys():
                team = playerConfig[t]
                team_no = int(t)
                for p in team:
                    #self.log.info( "p=%s" % (repr(p),))
                    p_type, p_control, p_name, p_hero, p_uid, p_index, p_items_procs = p
                    #self.log.info( "Player of type %s control %s: %s with hero %d (index %d)" % (p_type, p_control, p_name, int(p_hero), int(p_index) ))
                    if p_type == "ai":
                        ai_fake_user = self.createFakedUser( int(p_hero) )
                        ai_fake_user.username = unicode( ai_fake_user.username + " " + str(ais+1) )
                        ai_fake_user.teamId = team_no
                        ai_fake_user.userType = p_control.capitalize()
                        ai_fake_user.playerIndex = p_index
                        match.addUser( ai_fake_user, team_no )
                        match.world.addAI( p_name, ai_fake_user, team_no )
                        ais += 1
                    elif p_type == "human":
                        match.allowedUsers[p_name] = (team_no, p_uid, p_control.capitalize(), p_index)
                        match.allowedControl[p_name] = p_control.capitalize()

                        if p_items_procs.has_key( "item" ):
                            match.assignItemsForUsername( p_name, p_items_procs["item"] )
                        if p_items_procs.has_key( "procs" ):
                            match.assignProcsForUsername( p_name, p_items_procs["procs"] )
                        humans +=1

            match.tutorial = tutorial
            if tutorial:
                ai_fake_user = self.createFakedUser( 1 )
                ai_fake_user.username = unicode( "Tutorial" )
                ai_fake_user.teamId = 2
                ai_fake_user.userType = "Master"
                ai_fake_user.playerIndex = 2
                match.addUser( ai_fake_user, 2 )
                ais += 1
                pass


            match.playersRequiredToStart = humans + ais
            if match is not None:
                # report back to the frontend server
                self.protocol.factory.server.sendHTTPRequest("GET", "http://%s:%d/internal_match_update/%s/created" % (FRONTEND_HOST, FRONTEND_PORT, str(token)))
                self.log.info( "Frontend created match %s with map %s; %d humans %d AIs" % (token,map_name, humans, ais))
                if match.tutorial:
                    self.log.info( "Match %s is running as a tutorial match." % (token,) )
            else:
                self.log.critical( "Frontend tried to create match %s with map %s but could not create it!" % (token, map_name) )




    def frontendShutdownRequest(self, seq_no):
        self.protocol.factory.server.activateGracefulShutdownMode()

    def statRequest(self, seq_no, **kwargs ):
        if self.match != None:
            stat_entry = ( time.ctime(), time.time(), self.match.frame, self.match.token, self.username, kwargs )
            #self.statEvents.append( stat_entry )
        else:
            self.log.error( "STAT event without match: %s" % (str(kwargs),) )

    def _parseDBItems(self, dbItems, itemNames):
        items = []
        for itemName in itemNames:
            for dbi in dbItems:
                if itemName == dbi["name"]:
                    items.append(dictToNestedTuple(dbi))
                    break
        return items

    def process(self, cmd_dict):
        assert( type(cmd_dict) is dict )
        assert( cmd_dict.has_key( "cmd" ) )

        self.commandsIn += 1
        cmd = cmd_dict["cmd"]
        cmd = string.upper( cmd )
        seq = cmd_dict["seq"] if cmd_dict.has_key( "seq" ) else -1

        cb_table = {
            "PONG": self.pongRequest,
            "AUTH": self.authenticateRequest,
            "FE_MATCH_CREATE": self.frontendMatchCreationRequest,
            "FE_MATCH_SETUP": self.frontendMatchSetupRequest,
            "FE_MATCH_ITEMS": self.frontendMatchItemAssignRequest,
            "FE_SHUTDOWN": self.frontendShutdownRequest,
            "JOIN_REQ": self.joinRequest,
            "STAT": self.statRequest
        }

        data_dict = cmd_dict["data"]
        if cmd not in LOG_IGNORE:
            self.log.debug("<=(%s) %s: %s" % (self.username, cmd, data_dict))

        # don't do anything until we are authenticated successfully
        if self.isAuthenticated == False and cmd != "AUTH":
            return False

        # this will succeed, as guaranteed by the assertion above
        if(cb_table.has_key(cmd)):
            cb_table[cmd](seq, **data_dict)
        else:
            self.match.networkRequest(self, cmd, seq, data_dict)

        return True

    def endSession(self):
        if self.match is not None:
            self.match.leave(self)
            if not self.isFakedUser:
                if len( self.statEvents ) > 0:
                    ts = time.strftime( "%Y-%m-%d-%H%M%S", time.gmtime() )
                    fn = PERFLOG_PATH + "/" + ts + "-statlog-%s.log" % (self.match.token[0:8],)
                    #self.log.info( "Writing %d stat events to %s..." % (len(self.statEvents), fn))
                    try:
                        #f = open( fn, "wt" )
                        #for entry in self.statEvents:
                        #    s = "%s,%d,%s" % (entry[0],entry[2],entry[4])
                        #    for k in entry[5]:
                        #        f.write( "%s,%s,%s\n" % (s,k,entry[5][k]) )
                        #f.close()
                        pass
                    except Exception:
                        self.log.error( "Could not write to perflog at %s" % (fn,))
                        pass

        if self.lobby is not None:
            self.lobby.leave(self)

        self.statEvents = None
        self.match = None
        self.lobby = None
        self.itemNames = None
        self.items = None
        self.gemNames = None
        self.gems = None

    def createFakedUser(self, requestedHero=0):
        factions = ( 0, 0, 0, 1, 1, 1, 0, 0 )
        heroes = ( 0, 1, 2, 1, 2, 0, 3, 4)
        faction = factions[requestedHero]
        hero = heroes[requestedHero]

        self.log.info( "Created faked user with faction %d hero %d" % (faction, hero))

        fakedUser = UserSession( self.transport, self.protocol )
        fakedUser.username = Match.heroes[ faction ][ hero ]
        fakedUser.screenname = Match.heroes[faction][hero]
        fakedUser.isAuthenticated = True
        fakedUser.isFakedUser = True
        fakedUser.ready = True
        fakedUser.requestedFaction = faction
        fakedUser.requestedHero = hero
        fakedUser.teamId = Enums.MATCH_TEAM_B
        return fakedUser

    def processSurrender(self):
        self.protocol.factory.server.sessionSurrendered( self )

    def forceCloseConnection(self):
        self.transport.loseConnection()

    def __init__(self, transport, protocol):
        assert( transport is not None )
        assert( protocol is not None )

        self.transport = transport
        self.protocol = protocol

        self.username = u"<UNKNOWN>"
        self.screenname = u"<UNKNOWN>"
        self.ga_user_id = ""

        self.itemNames = []
        self.items = []
        self.gemNames = []
        self.gems = []
        self.procs = []

        self.sessionStartTimestamp = time.time()
        self.lastCommandTimestamp = time.time()
        self.isAuthenticated = False
        self.isFrontend = False
        self.isFakedUser = False

        self.bytesIn = 0
        self.bytesOut = 0
        self.commandsIn = 0
        self.commandsOut = 0

        self.latencyRecorder = []

        self.rejectedAuths = 0

        self.match = None
        self.lobby = None
        self.status = ""
        self.log = logging.getLogger( "server" )

        self.requestedFaction = -1
        self.requestedHero = -1
        self.teamId = 0
        self.start = False
        self.ready = False
        self.userType = "Master"  # Master | Hero | Observer

        self.assignedId = None  # assigned by the match instance, don't mess with this
        self.statEvents = []

        self.log.info( "New connection from %s" % (str(self.transport.getPeer().host),) )


class GameServerProtocol( basic.LineReceiver ):
    def connectionMade(self):
        self.session = UserSession( self.transport, self )
        self.log = logging.getLogger("server")

        #res = yield self.factory.server.redis.info()
        #self.log.debug( "redis: %s" % (str(res), ) )

    def lineReceived(self, line):
        if self.session:
            try:
                decoded = json.loads( line )
                self.session.bytesIn += len(line)
                if not self.session.process( decoded ):
                    self.log.error( "Invalid command %s from %s (user %s  authenticated: %s)" % (decoded["cmd"], self.transport.getPeer().host,
                                                                                                 self.session.username, self.session.isAuthenticated))
            except ValueError, err:
                self.log.error( "JSON decode error: %s input was: %s" % (err,line) )
                self.transport.loseConnection()
        else:
            self.log.critical( "Protocol has no session???")
            self.transport.loseConnection()

    def connectionLost(self, reason):
        self.session.endSession()
        self.log.info( "Connection to %s closed: %s" % (self.transport.getPeer().host,reason))
        self.log.info( "Connection duration %4.2f seconds" % (time.time() - self.session.sessionStartTimestamp,))
        self.log.info( "Connection cmds in/out: %d/%d  bytes in/out: %d/%d" %
                       (self.session.commandsIn, self.session.commandsOut,
                       self.session.bytesIn, self.session.bytesOut))
        self.factory.server.sessionEnded( self.session )


class GameServerFactory( protocol.ServerFactory ):
    protocol = GameServerProtocol
    mongo = txmongo.lazyMongoConnectionPool( MONGODB_HOST, MONGODB_PORT )

    def startFactory(self):
        pass

    def stopFactory(self):
        pass

    def __init__(self, server, **kwargs):
        self.server = server
        self.log = logging.getLogger("server")


class GameServer(object):
    def __init__(self):
        logging.basicConfig(format="%(asctime)-15s  %(levelname)-8s %(name)s: %(message)s", level=LOG_LEVEL)
        self.log = logging.getLogger("server")
        self.redis = None

        self.lobby = Lobby()
        self.matches = {}
        self.active = True
        self.gracefulShutdownMode = False
        self.matchIDPool = 0

        self.updateFrequency = SERVER_FPS
        self.startupPort = SERVER_PORT
        self.updateTask = task.LoopingCall(self.update)
        self.startTime = time.time()  # This is the timestamp when the server was started
        self.lastUpdate = time.time() - self.startTime  # And this measures how many seconds the server has been running
        self.dt = SERVER_FPS

    def activateGracefulShutdownMode(self):
        """
        This should be called prior to entering maintenance procedures. It allows on-going games to end gracefully.
        New games are not allowed to begin.
        """
        self.gracefulShutdownMode = True

    @defer.inlineCallbacks
    def connectRedis(self):
        #rd_clientCreator = protocol.ClientCreator( reactor, RedisClient )
        #self.redis = yield rd_clientCreator.connectTCP( "10.0.0.1", 6379 )
        pass

    def authenticateFrontend(self, username, password):
        if username == FRONTEND_USERNAME and password == FRONTEND_PASSWORD:
            return True

        return False

    def authenticateLogin(self, username, password, account):
        if self.gracefulShutdownMode:
            return False
        self.log.debug( "Authenticating for user %s with password %s" % (username,password))

        return True
        #if account.has_key("password") and password == account["password"]:
        #    return True
        #return False

    def requestMatchWithMap(self, token, mapdef, prefabs):
        m = self.findMatchByToken(token)
        if m is None:
            parsedmap = ParsedMap.ParsedMap( mapdef )
            if parsedmap.isLegalMap():
                self.log.info( "Loaded map %s; width=%d height=%d with %d structures, %d props" %
                               (parsedmap.name, parsedmap.width, parsedmap.height, len(parsedmap.structures), len(parsedmap.props) ) )
                m = Match.Match(token, prefabs)
                m.gameServer = self
                m.id = self.matchIDPool
                self.matchIDPool += 1
                m.loadMap(parsedmap)
                m.wait()
                self.matches[token] = m
                return m

        return None

    def sendHTTPRequest(self, method, uri):
        agent = Agent(reactor)
        agent.request(method, uri)


    def sendHTTPPost(self, url, values = {}, headers = {}, method="POST"):
        agent = Agent(reactor)
        data = urllib.urlencode( values )

        d = agent.request(method,
                          url,
                          Headers(headers),
                          StringProducer(data) if data else None)

        def handle_response(response):
            if response.code == 204:
                d = defer.succeed('')
            else:
                class SimpleReceiver(protocol.Protocol):
                    def __init__(s, d):
                        s.buf = ''; s.d = d
                    def dataReceived(s, data):
                        s.buf += data
                    def connectionLost(s, reason):
                        # TODO: test if reason is twisted.web.client.ResponseDone, if not, do an errback
                        s.d.callback(s.buf)

                d = defer.Deferred()
                response.deliverBody(SimpleReceiver(d))
            return d

        d.addCallback(handle_response)
        return d

    def sendCompleteStatUpdate(self, token):
        if self.matches.has_key(token):
            match = self.matches[token]
            request_dict = {
                "duration": (time.time() - match.startTime),
                "winning_team": match.winningTeamId if match.winningTeamId is not None else -1,
                "tickets_team1":match.world.getTeamEntity(1).getAttributes().get(("Resources","Tickets")),
                "tickets_team2":match.world.getTeamEntity(2).getAttributes().get(("Resources","Tickets"))
            }
            rd = { "request_data":json.dumps(request_dict)}
            d = self.sendHTTPPost( "http://%s:%d/internal_match_stat_update/%s/basic" % (FRONTEND_HOST, FRONTEND_PORT, str(token)),
                                   rd, headers = {} )

            request_dict = {
                "players":[]
            }

            for u in match.userStatistics.keys():
                ud = {}
                for sk in match.userStatistics[u].keys():
                    ud[sk] = match.userStatistics[u][sk]
                request_dict["players"].append(ud)
            rd = { "request_data":json.dumps(request_dict)}
            d = self.sendHTTPPost( "http://%s:%d/internal_match_stat_update/%s/player" % (FRONTEND_HOST, FRONTEND_PORT, str(token)),
                                   rd, headers = {} )



    def sendGameAnalyticsRequest(self, message, category=None):
        message["build"] = GA_BUILD

        m = hashlib.sha1()
        m.update(MAC_HASH)

        json_message = json.dumps(message)
        digest = hashlib.md5()
        digest.update(json_message)
        digest.update(GA_SECRET_KEY)
        json_authorization = {"Authorization": digest.hexdigest()}

        if category is None:
            category = "design"

        url = "%s/%s/%s" % (GA_ENDPOINT_URL, GA_GAME_KEY, category)
        request = urllib2.Request(url, json_message, json_authorization)
        response = urllib2.urlopen(request)
        self.log.info(str(response.read()))

    def findMatchByToken(self, token):
        if self.matches.has_key(token):
            return self.matches[token]
        return None

    def sessionEnded(self, session):
        k = None
        for m_key in self.matches.keys():
            m = self.matches[m_key]
            if m.state == Enums.MATCH_STATE_ENDED:
                k = m_key

        if k is not None:
            self.log.info("Match %s removed" % (self.matches[k].token,))
            self.matches[k].writeNetworkLogToDisk()
            self.matches[k].release()
            del self.matches[k]

    def sessionSurrendered(self, session):
        _, uid, _, _, = session.match.allowedUsers[session.username]
        self.log.info( "Player %s surrendering; will do frontend update..." % (session.username,))
        self.log.info( "HTTP target: http://%s:%d/internal_match_surrender/%s/%d" % (FRONTEND_HOST, FRONTEND_PORT, str(session.match.token), int(uid)) )
        self.sendHTTPRequest("GET", "http://%s:%d/internal_match_surrender/%s/%d" % (FRONTEND_HOST, FRONTEND_PORT, str(session.match.token), int(uid)) )


    def update(self):
        t = time.time() - self.startTime
        self.dt = t - self.lastUpdate
        self.lastUpdate = t
        if self.dt > SERVER_FRAME_QUOTA:
            self.log.critical("Server reports update time %f exceeding quota %f! Current match count: %d" % (float(self.dt), SERVER_FRAME_QUOTA, len(self.matches)))
        if len(self.matches) is 0 and self.gracefulShutdownMode:
            self.sendHTTPRequest("GET", "http://%s:%d/internal_frontend_shutdown/%s" % (FRONTEND_HOST, FRONTEND_PORT, SERVER_NAME))
            reactor.stop()
            return
        crashed_keys = []
        for m_key in self.matches.keys():
            try:
                m = self.matches[m_key]
                oldstate = m.state
                m.twisted_update_cb(self.dt)
                if oldstate != m.state and m.state == Enums.MATCH_STATE_RUNNING:
                    self.log.info( "Match %s changed into running state. Reporting to frontend..." % (m.token, ))
                    self.sendHTTPRequest( "GET", "http://%s:%d/internal_match_update/%s/started" % (FRONTEND_HOST, FRONTEND_PORT, str(m.token)) )
                elif oldstate != m.state and m.state == Enums.MATCH_STATE_ENDED:
                    self.log.info("Match with id %d and token %s ended. Total skipped frames: %d" % (m.id, m.token, m.frameSkips))

                    winners = []
                    team = m.getWinningTeam()
                    if team is not None:
                        for u in m.users:
                            if u is not None and u.teamId == m.winningTeamId and m.allowedUsers.has_key(u.username):
                                winners.append(str(m.allowedUsers[u.username][1]))

                        self.log.info("Winning team id: %d with members: %s" % (m.winningTeamId,str(winners)))
                    else:
                        self.log.warning( "Could not resolve winners for match id %d (token %s)" % (m.id, m.token))
                    self.log.info("Reporting back to frontend...")

                    stat_items = ( "total_kills", "level", "team_tickets", "max_upgrades", "active_items")
                    match_stat_dict = {}
                    for uname in m.allowedUsers.keys():
                        match_stat_dict[uname] = {}
                        for si in stat_items:
                            match_stat_dict[uname][si] = m.matchStatisticForUser( uname, si )

                    #self.log.info( "Stat dict: %s" % (json.dumps(match_stat_dict),))
                    winstr = "winners=%s" % ( string.join(winners, ","), ) if len(winners) > 0 else ""
                    statstr = "stats=%s" % ( urllib.quote_plus( json.dumps( match_stat_dict ) ) )
                    self.sendHTTPRequest("GET",
                                         "http://%s:%d/internal_match_update/%s/ended?%s&%s" % (FRONTEND_HOST, FRONTEND_PORT, str(m.token), winstr, statstr ))
                    self.sendCompleteStatUpdate( m.token )
                    # kill all AIs
                    for u in m.users:
                        if u is not None and u.isFakedUser:
                            m.leave( u )
                    uc = m.countActiveUsers();
                    self.log.info( "Match has %d active users remaining" % (uc,) )
                    if uc == 0:
                        self.log.info("Match %s removed" % (self.matches[m_key].token,))
                        self.matches[m_key].writeNetworkLogToDisk()
                        self.matches[m_key].release()
                        del self.matches[m_key]
                elif m.state == Enums.MATCH_STATE_FORCE_TERM:
                    if self.matches.has_key(m_key):
                        self.log.info("Match %s removed" % (self.matches[m_key].token,))
                        self.matches[m_key].writeNetworkLogToDisk()
                        self.matches[m_key].release()
                        del self.matches[m_key]
                        self.sendHTTPRequest("GET", "http://%s:%d/internal_match_update/%s/terminated" % (FRONTEND_HOST, FRONTEND_PORT, str(m.token)))
            except Exception:
                tb = str(traceback.format_exc())
                self.log.error("Match with token " + str(m.token) + " crashed. Traceback: " + tb)
                self.matches[m_key].writeToErrorLog(tb)
                crashed_keys.append(m_key)
        for k in crashed_keys:
            for u in self.matches[k].users:
                if u is not None:  # insurance for faked users
                    u.forceCloseConnection()
            if self.matches.has_key(k):
                self.log.info("Match %s removed" % (self.matches[k].token,))
                self.matches[k].writeNetworkLogToDisk()
                self.matches[k].release()
                del self.matches[k]


    def run(self):
        self.log.info( "TDTA Master Server, build %s (%s) (%s)" % (BUILD_NUMBER, BUILD_JOB_NAME, BUILD_ID))
        self.log.info( "Server startup on port %d" % (self.startupPort,) )

        pid = str(os.getpid())
        pidfile = "./tdta_server.pid"

        if os.path.isfile( pidfile ):
            self.log.critical( "%s exists. Is the server already running?" % (pidfile,) )
            sys.exit()
        else:
            file(pidfile, "w").write(pid)

        #self.connectRedis()
        reactor.listenTCP( self.startupPort, GameServerFactory( self ) )
        self.updateTask.start( 1.0 / (SERVER_FPS) )
        reactor.run()

        self.log.info( "Server shutdown.")
        os.unlink( pidfile )
        #self.updateMatches(self.dt)
