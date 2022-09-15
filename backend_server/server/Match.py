from twisted.internet import task

from World import *
import logging
import time

from ServerConfig import *
from NetworkHandlers import *
import os
import hashlib
import random

import Enums


heroes = (
    ("Bear", "Sniper", "Fyrestein", "Celestial bear", "Alchemist"),  # Northerners
    ("Stone elemental", "Beaver", "Rogue"),  # Fay
    ()  # Parliament
)

bases = (
    "Townhall",    # Northerners
    "Fay throne",  # Fay
    ""             # Parliament
)


class NetworkChannel(object):
    def removeSession(self, usersession):
        if usersession in self.sessions:
            self.sessions.remove(usersession)

    def addSession(self, usersession):
        if usersession not in self.sessions:
            self.sessions.append( usersession )

    def sendCommand(self, cmd, data):
        self.match.writeToNetworkLog(True, self.getAllUserIDs(), cmd, data)
        for s in self.sessions:
            s.sendCommand(cmd, data)

    def getAllUserIDs(self):
        return [u.assignedId for u in self.sessions]

    def __init__(self, match):
        self.sessions = []
        self.match = match


class Team(object):
    def sessionCount(self):
        return len(self.networkChannel.sessions)

    def leave(self, usersession):
        self.networkChannel.removeSession(usersession)

    def join(self, usersession):
        self.networkChannel.addSession(usersession)

    def __init__(self, match):
        self.match = match
        self.networkChannel = NetworkChannel(self.match)
        self.teamId = Enums.MATCH_TEAM_NULL



class MatchRuleset(object):
    def createInitialEntities(self):
        pass

    def canStart(self):
        return False

    def winners(self):
        return None

    def scoreForTeam(self, teamId):
        return 0

    def scoreForUser(self, user):
        return 0

    def hasEnded(self):
        return False

    def suggestTeamForUser(self, user):
        pass

    def initializeForMatch(self, match):
        self.match = match

    def playersRequiredToStart(self):
        return 2

    def humansRequiredToStart(self):
        return 2

    def __init__(self):
        self.match = None
        self.teamSize = 2


class MatchRulesTwoTeamsWithTickets(MatchRuleset):
    def createInitialEntities(self):
        pass

    def initializeForMatch(self, match):
        self.match = match
        self.match.addTeam(Team(self.match))
        self.match.addTeam(Team(self.match))

    def winners(self):
        if self.hasEnded():
            return []
        return []

    def canStart(self):
        usersReady = False
        usercount = self.match.countActiveUsers()
        if usercount >= self.requiredHumans:
            usersReady = True
            for u in self.match.users:
                if u is None or not u.ready:
                   usersReady = False
                   break
        return usersReady

    def hasEnded(self):
        # check if either team has tix left
        pass

    def suggestTeamForUser(self, user):
        pass

    def setTeamSlot(self, teamId, slot_number, ai_or_human):
        assert( ai_or_human == Enums.MATCH_PLAYER_AI or ai_or_human == Enums.MATCH_PLAYER_HUMAN )
        t_idx = teamId - Enums.MATCH_TEAM_A
        self.teamConfig[ t_idx ][slot_number] = ai_or_human

    def playersRequiredToStart(self):
        return self.playersPerTeam * 2

    def humansRequiredToStart(self):
        return self.requiredHumans

    def __init__(self, match, players_per_team = 1, min_humans_per_team = 1):   # default to 1v1 config
        self.playersPerTeam = players_per_team
        self.requiredHumans = min_humans_per_team
        self.teamConfig = [[ Enums.MATCH_PLAYER_HUMAN ] * players_per_team] * 2
        if min_humans_per_team < players_per_team:
            for i in range( 0, players_per_team - min_humans_per_team):
                self.setTeamSlot( Enums.MATCH_TEAM_A, (players_per_team - 1) - i, Enums.MATCH_PLAYER_AI )
                self.setTeamSlot( Enums.MATCH_TEAM_B, (players_per_team - 1) - i, Enums.MATCH_PLAYER_AI )


class Match(object):
    """
    A straight forward match class.
    """
    def __init__(self, token, prefabs, rules = None):
        self.initialized = False
        self.world = World(network_callback=self.networkCommand, prefabDict=prefabs, usePrefabFile=False)
        self.state = Enums.MATCH_STATE_WAITING
        self.syncDone = False
        self.requestedState = -1
        self.token = token

        self.redis = None
        self.gameServer = None
        m = hashlib.md5()
        m.update(token)                              # The session_id is a hash of the match token,
        m.update("%032x" % random.getrandbits(128))  # with a pinch of salt added in,
        self.session_id = m.hexdigest()              # and finally served as a hex digest string created from 128-bits

        self.frame = 0
        self.date = time.strftime("%Y-%m-%d")
        self.startTimeStr = time.strftime("%H%M%S")
        self.startTime = time.time()  # Timestamp when the match started
        self.finalJoinTime = time.time() + 60   # allow 60 secs for all players to get in
        self.lastUpdate = 0.0  # Elapsed seconds, i.e. how many seconds the match has been running
        self.lastNonPong = 0.0
        self.lastPing = 0.0
        self.frameSkips = 0
        self.periodCumulativeFrametime = 0.0
        self.id = 0

        self.broadcastChannel = NetworkChannel(self)
        self.networkCommandHandlers = None
        self.pendingRequests = {}

        self.log = logging.getLogger( "server.%s..." % (self.token[0:8],) )
        self.log.info( "Match %s initialized" % (self.token,) )

        self.mapName = "none"
        self.users = []
        self.teams = []
        self.killStatistics = {}
        self.matchStatistics = {}
        self.userStatistics = {}

        self.directConnect = False

        self.userProcAssignments = {}
        self.userItemAssignments = {}
        self.userGemAssignments = {}
        self.userProcAssignments = {}

        self.world.setMatch(self)

        self.playersRequiredToStart = 2    # require this many players ready to start the game
        self.maximumUsers = 4     # allow this many players in total
        self.teamSize = 2         # allow this many players in a single team
        self.allowedUsers = {}
        self.allowedControl = {}
        self.winningTeamId = None
        self.aiDifficulty = "medium"
        self.tutorial = False

        self.networkLog = []  # Contains 5-tuples of form: (is_command: bool,
                              #                             server_frame: int,
                              #                             userIDs: list of int,
                              #                             cmd: str,
                              #                             data: dict)
        self.errorLog = []    # Contains error messages of type str

        self.rules = rules
        if self.rules is not None:
            self.rules.initializeForMatch( self )
        else:
            self.addTeam(Team(self))
            self.addTeam(Team(self))

        self.registerNetworkCommandHandlers()
        self.registerNetworkRequestHandlers()

    def writeToErrorLog(self, message):
        self.errorLog.append(message)

    def writeToNetworkLog(self, is_command, userIDs, cmd, data):
        if WRITE_MATCH_LOGS_TO_FILE:
            self.networkLog.append((is_command, self.frame, self.lastUpdate, userIDs, cmd, data))

    def writeNetworkLogToDisk(self):
        if WRITE_MATCH_LOGS_TO_FILE:
            if not os.path.exists(MATCHLOG_PATH):
                os.makedirs(MATCHLOG_PATH)
            if len(self.errorLog) > 0:
                filename = MATCHLOG_PATH + self.date + "__" + self.startTimeStr + "-" + time.strftime("%H%M%S") + "_ERROR.log"
            else:
                filename = MATCHLOG_PATH + self.date + "__" + self.startTimeStr + "-" + time.strftime("%H%M%S") + ".log"
            with open(filename, "w") as f:
                f.write("CMD/REQ\tFrame\tTime\tUsers\tCommand\tData\n\n")
                for entry in self.networkLog:
                    f.write(("CMD" if entry[0] else "REQ") + "\t" + str(entry[1]) + "\t" + str(entry[2]) + "\t" + str(entry[3]) + "\t" + str(entry[4]) + "\t" + str(entry[5]) + "\n")
                if len(self.errorLog) > 0:
                    f.write("\n")
                    for entry in self.errorLog:
                        f.write("ERROR: " + entry)

    def sendAnalyticsForAllUsers(self, message, category=None):
        #for u in self.users:
        #    self.sendAnalyticsForUser(u, message, category)
        pass

    def sendAnalyticsForUser(self, user, message, category=None):
        # If the user has not provided a ga_user_id hash, then no analytics will be gathered
        if user is None or user.ga_user_id == "" or user.isFakedUser:
            return
        # The intent of the ga_user_id is to gather anonymous user statistics
        message["user_id"] = user.ga_user_id
        message["session_id"] = self.session_id
        #self.gameServer.sendGameAnalyticsRequest(message, category)

    def registerNetworkCommandHandlers(self):
        self.networkCommandHandlers = {
            Enums.COMP_EVENT_MOVEMENT_STARTED: movementStarted,
            Enums.COMP_EVENT_MOVEMENT_SPEED: movementSpeed,
            Enums.COMP_EVENT_MOVEMENT_ENDED: movementEnded,
            Enums.COMP_EVENT_MOVEMENT_TELEPORT: movementTeleport,
            Enums.COMP_EVENT_ATTRIBUTES_CHANGED: attributesChanged,
            Enums.COMP_EVENT_USERLOCAL_ATTRIBUTES_CHANGED: attributesChanged,
            Enums.COMP_EVENT_COMBATATTRIBUTE_ADDED: combatAttributeAdded,
            Enums.COMP_EVENT_COMBATATTRIBUTE_REMOVED: combatAttributeRemoved,
            Enums.COMP_EVENT_EFFECT_LAUNCHED: effectLaunched,
            Enums.WORLD_EVENT_ENTITY_CREATE: entityCreated,
            Enums.WORLD_EVENT_ENTITY_DESTROY: entityDestroyed,
            Enums.WORLD_EVENT_ENTITY_DEATH: entityDied,
            Enums.WORLD_EVENT_ENTITY_SELL: entitySold,
            Enums.WORLD_EVENT_ENTITY_RESPAWN: entityRespawned,
            Enums.WORLD_EVENT_DAMAGE: entityDamaged,
            Enums.WORLD_EVENT_ATTACK: entityAttacked,
            Enums.WORLD_EVENT_CHARGE: entityCharged,
            Enums.WORLD_EVENT_TIMED_CHARGE: entityChargedWithTime,
            Enums.WORLD_EVENT_LEAP: entityLeaped,
            Enums.WORLD_EVENT_HEAL_PERFORMED: entityPerformedHeal,
            Enums.WORLD_EVENT_HEAL_RECEIVED: entityHealed,
            Enums.WORLD_EVENT_BUFF: entityBuffed,
            Enums.WORLD_EVENT_BUFF_EXPIRED: entityBuffExpired,
            Enums.WORLD_EVENT_BUILDING: building,
            Enums.WORLD_EVENT_BUILDING_READY: buildingReady,
            Enums.WORLD_EVENT_BUILDING_UPGRADING: buildingUpgrading,
            Enums.WORLD_EVENT_BUILDING_UPGRADED: buildingUpgraded,
            Enums.WORLD_EVENT_REACH_BASE: unitReachedBase,
            Enums.WORLD_EVENT_START_WAVE: startWave,
            Enums.WORLD_EVENT_END_GAME_WITH_WINNER: endGameWithWin,
            Enums.WORLD_EVENT_TEAM_ELIMINATED: teamEliminated,
            Enums.WORLD_EVENT_LAST_HIT: heroPerformedLastHit,
            Enums.WORLD_EVENT_STUN: unitStunned,
            Enums.WORLD_EVENT_ITEM_PICKUP: itemPickedUp,
            Enums.WORLD_EVENT_SCOPE: entityUsedScope,

            Enums.WORLD_EVENT_CAST_STARTED: heroCastStarted,
            Enums.WORLD_EVENT_CAST_SUCCESS: heroCastFinished,
            Enums.WORLD_EVENT_CAST_CANCELED: heroCastCanceled,
            Enums.WORLD_EVENT_ABILITY_USED: unitAbilityUsed,
            Enums.WORLD_EVENT_ABILITY_ENDED: unitAbilityEnded,
            Enums.WORLD_EVENT_PROC: procHappened,

            Enums.WORLD_EVENT_AOE_HEAL_PERFORMED: entityAoeHealed,
            Enums.WORLD_EVENT_AOE_DAMAGE_PERFORMED: entityAoeDamaged,

            Enums.WORLD_EVENT_TUTORIAL_MESSAGE: tutorialMessageDisplayed,
            Enums.WORLD_EVENT_TUTORIAL_UI: tutorialUIControlled,
            Enums.WORLD_EVENT_TUTORIAL_END: tutorialEnded,

            Enums.WORLD_EVENT_TELEPORT: entityTeleported
        }

    def registerNetworkRequestHandlers(self):
        self.world.componentSystems[Enums.COMPSYS_TYPE_NETWORK].networkRequestHandlers = {
            Enums.REQ: request,
            Enums.E_MOV_REQ: entityMovementRequest,
            Enums.E_STOP_REQ: entityStopRequest,
            Enums.E_ACT_REQ: entityActionRequest
        }
        if ALLOW_DEBUG_COMMANDS:
            self.world.componentSystems[Enums.COMPSYS_TYPE_NETWORK].networkRequestHandlers[Enums.E_CREAT_REQ] = entityCreateRequest
            self.world.componentSystems[Enums.COMPSYS_TYPE_NETWORK].networkRequestHandlers[Enums.E_DESTR_REQ] = entityDestroyRequest
            self.world.componentSystems[Enums.COMPSYS_TYPE_NETWORK].networkRequestHandlers[Enums.E_ATTR_GET_REQ] = entityAttributeGetRequest
            self.world.componentSystems[Enums.COMPSYS_TYPE_NETWORK].networkRequestHandlers[Enums.E_ATTR_SET_REQ] = entityAttributeSetRequest

    def getAllUserIDs(self):
        return [u.assignedId for u in self.users]

    def sendReady(self):
        cmd = "READY_RES"
        data = {}
        self.writeToNetworkLog(True, self.getAllUserIDs(), cmd, data)
        for u in self.users:
            u.sendCommand(cmd, data)

    def networkCommand(self, event, data, entity):
        try:
            self.networkCommandHandlers[event](self, event, data, entity)
        except KeyError:
            #self.log.critical( "Key error in networkCommand() for event %d in entity %d" % (event,entity.id))
            return

        if event == Enums.WORLD_EVENT_END_GAME_WITH_WINNER:
            self.requestState( Enums.MATCH_STATE_ENDED )

    def networkRequest(self, user, request, sequence_number, request_dict):
        if request != "PONG":
            self.lastNonPong = time.time() - self.startTime
        self.writeToNetworkLog(False, [user.assignedId], request, request_dict)
        if request == "READY_REQ":
            playerReadyRequest(user, sequence_number)
        elif request == "SURR_REQ":
            playerSurrenderRequest(user, sequence_number)
        else:
            self.world.networkRequest(user, request, sequence_number, request_dict)

    def networkRequestReply(self, user, sequence_number, cmd, data):
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        if user is not None:
            user.sendCommand(cmd, data)
        else:
            self.log.critical("Attempting to send response %s with sequence number %d to a null user!" % (cmd, sequence_number))

    def countActiveUsers(self):   # basically "count humans"
        return len( filter( lambda u: u is not None and not u.isFakedUser, self.users ) )

    def countReadyUsers(self):
        return len( filter( lambda u: u is not None and (u.isFakedUser or u.ready), self.users ) )

    def assignItemsForUsername(self, username, item_list):
        for item in item_list:
            pass
        self.log.info("User %s assigned items: %s" % (username, str(item_list)))
        self.userItemAssignments[username] = item_list

    def assignGemsForUsername(self, username, gem_list):
        #self.log.info("User %s assigned gems: %s" % (username, str(gem_list)))
        self.userGemAssignments[username] = gem_list

    def assignProcsForUsername(self, username, proc_list):
        self.log.info("User %s assigned procs: %s" % (username, str(proc_list)))
        self.userProcAssignments[username] = proc_list

    def addTeam(self, team):
        team.teamId = len(self.teams) + 1
        self.teams.append(team)
        self.world.addTeam(team)

    def usersInTeam(self, teamId):
        return len( filter( lambda u: (u is not None and u.teamId == teamId), self.users ) )

    def addUser(self, user, teamID):
        self.users.append(user)
        self.userStatistics[user.username] = {
            "player_match_index":user.playerIndex,
            "player_name":user.username,
           "level":1,
           "total_experience":0,
           "kills":0,
           "creep_kills":0,
           "deaths":0,
           "captures":0,
           "gold_collected":0,
           "total_damage_out":0,
           "total_damage_in":0,
           "potions_collected":0
        }
        faction = "Northerners" if user.requestedFaction is 0 else "Fay" if user.requestedFaction is 1 else "Parliament"
        self.world.addUser(user, teamID, faction, heroes[user.requestedFaction][user.requestedHero] if user.userType != "Observer" else "", user.userType )

        if user.assignedId == None:
            user.assignedId = self.users.index(user)
            self.log.info( "User %s/%s added with assigned id %d" % (user.screenname, user.username, user.assignedId))
        else:
            self.log.warning( "Attempting to re-add user %s/%s with assigned id %d" % (user.screenname, user.username, user.assignedId))

        if user.userType == "Master":
            base_prefab = bases[user.requestedFaction]
            dir = Vector3( 0, 1, 0 ) if user.teamId == 1 else Vector3( 0, -1, 0 )
            base = self.world.createGameEntityForUserDelayNetwork( base_prefab, self.world.teamBaseLocations[user.teamId], dir,
                                                                   user, ( ("Team", user.teamId ), ) )
            base.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True    # make sure the network comp is listening
            townAttr = base.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            townAttr.set("OwnerId", user.assignedId)
            townAttr.set("Owner name", user.username)
            #self.log.info( "Created HQ prefab %s for master user %s" % (base_prefab, user.username))

            otherUsers = [u for u in self.users if u.assignedId is not user.assignedId]
            cmd = "E_CREAT"
            data = {
                "id": base.id,
                "pos": tuple(base.getPosition()),
                "dir": tuple(base.getDirection()),
                "size": float(base.getSize()),
                "attributes": townAttr.getNetworkDictionary(),
            }
            self.writeToNetworkLog(True, self.getAllUserIDs(), cmd, data)
            for u in otherUsers:
                u.sendCommand(cmd, data)

    def removeUser(self, user):
        if user is None:
            return
        # update stats for one last time...
        self.updateMatchStatisticsForUser( user )
        self.world.removeUser(user)
        # must guarantee that previous userids still work
        i = self.users.index( user )
        self.users[i] = None

    def removeAllUsers(self):
        for u in self.users:
            self.removeUser(u)

    def disconnectAllUsers(self):
        for i in range(len(self.users)).__reversed__():
            u = self.users[i]
            if u is not None and not u.isFakedUser:
                u.forceCloseConnection()

    def findUserById(self, userId):
        if userId is not None and userId >= 0 and userId < len(self.users):
            return self.users[userId]

        return None

    def findUserByName(self, username):
        for u in self.users:
            if u.username == username:
                return u

        return None

    def userControlsUnit(self, user, unit_id):
        return True

    def teamControlsUnit(self, team_id, unit_id):
        return True

    def prepareTutorial(self):
        self.world.createTutorial()

    def syncDataForUser(self, user):
        ## TODO send enums and perhaps other similar data to user
        self.log.info( "Synchronizing data for user %s..." % (user.screenname,))
        cmd = "ENUM_DATA"
        data = {
            "attributes": AttributeEnums,
            "e_actions": EntityActionEnums,
            "game_signals": GameSignalEnums,
        }
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        user.sendCommand(cmd, data)

    def syncMapForUser(self, user):
        self.log.info( "Synchronizing map for user %s h=%d w=%d..." % (user.screenname,self.world.map.height, self.world.map.width))
        deftotile = "0ABCDE12345678FGH"
        # TODO: might want to move this somewhere else
        propToClientString = {
            Enums.PROP_ROAD_CROSS: "Road cross",
            Enums.PROP_ROAD_NS: "Road NS",
            Enums.PROP_ROAD_EW: "Road EW",
            Enums.PROP_ROAD_NE: "Road NE",
            Enums.PROP_ROAD_NW: "Road NW",
            Enums.PROP_ROAD_SE: "Road SE",
            Enums.PROP_ROAD_SW: "Road SW",
            Enums.PROP_ROAD_TN: "Road TN",
            Enums.PROP_ROAD_TS: "Road TS",
            Enums.PROP_ROAD_TE: "Road TE",
            Enums.PROP_ROAD_TW: "Road TW",
            Enums.PROP_FOREST_3X3: "Forest 3x3"
        }

        cmd = "G_MAP_DEF"
        data = {
            "origin": (0.0, 0.0, 0.0),
            "width": self.world.map.width,
            "height": self.world.map.height,
            "tilesize": 1.0,
            "id": self.mapName,
            "map": self.mapName
        }
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        user.sendCommand(cmd, data)

        for i in range(0, self.world.map.height):
            defstr = ""
            for j in range(0, self.world.map.width):
                defstr += deftotile[self.world.map.getGridNode(j, i)[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_NODETYPE]]
            cmd = "G_MAP_SET"
            data = {
                "defstring": defstr,
                "xoffset": 0,
                "yoffset": i
            }
            self.writeToNetworkLog(True, [user.assignedId], cmd, data)
            user.sendCommand(cmd, data)

        cmd = "G_MAP_HEIGHT"
        data = {
            "heightMap": self.world.map.getHeightMap(),
            "width": self.world.map.width,
            "height": self.world.map.height
        }
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        user.sendCommand(cmd, data)

        for p in self.world.mapProps:
            cmd = "G_MAP_PROP"
            data = {
                "pos": tuple(p[1]),
                "dir": (0.0, 0.0, 0.0),
                "size": 0.5,
                "type": propToClientString[p[0]]
            }
            self.writeToNetworkLog(True, [user.assignedId], cmd, data)
            user.sendCommand(cmd, data)

        cmd = "G_MAP_END"
        data = {}
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        user.sendCommand(cmd, data)

    def syncGameStateForUser(self, user):
        self.log.info( "Synchronizing game state for user %s..." % (user.screenname,))
        matchEntity = self.world.getMatchEntity()
        teamEntities = self.world.getTeamEntities()
        userEntities = self.world.getUserEntities()

        matchAttribs = matchEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        cmd = "SET"
        data = {
            "scope": matchAttribs.get("Subtype"),
            "type": Enums.ATTR_SET_MULTIPLE,
            "attributes": matchAttribs.getNetworkDictionary(),
        }
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        user.sendCommand(cmd, data)
        for teamEntity in teamEntities:
            teamAttribs = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            cmd = "SET"
            data = {
                "scope": teamAttribs.get("Subtype"),
                "team": teamAttribs.get("Team"),
                "type": Enums.ATTR_SET_MULTIPLE,
                "attributes": teamAttribs.getNetworkDictionary(),
            }
            self.writeToNetworkLog(True, [user.assignedId], cmd, data)
            user.sendCommand(cmd, data)
        for userEntity in userEntities:
            userAttribs = userEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            cmd = "SET"
            data = {
                "scope": userAttribs.get("Subtype"),
                "username": userAttribs.get("Username"),
                "type": Enums.ATTR_SET_MULTIPLE,
                "attributes": userAttribs.getNetworkDictionary(),
            }
            self.writeToNetworkLog(True, [user.assignedId], cmd, data)
            user.sendCommand(cmd, data)

        # we assume here that we're syncing to an empty game state OR that the client can just deal with this
        # we also pass only networked entities, but we will want to consider other filtering as well
        for entity in self.world.queryEntities(
                lambda e: e.hasComponent(Enums.COMP_TYPE_NETWORK) and
                        e.hasComponent(Enums.COMP_TYPE_TRANSFORM) and
                        e.hasComponent(Enums.COMP_TYPE_ATTRIBUTES) and
                        e.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Type") != "Info"):
            xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
            attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
            physical = entity.getComponent(Enums.COMP_TYPE_PHYSICAL)
            attrDict = attributes.getNetworkDictionary()
            if tags:
                attrDict[AttributeEnums["Tags"]] = tags.getList()
            cmd = "E_CREAT"
            data = {
                "id": entity.id,
                "pos": tuple(xform.getWorldPosition()),
                "dir": tuple(xform.getWorldDirection()),
                "size": float(physical.getSize()) if physical else 0.0,
                "attributes": attrDict,
            }
            self.writeToNetworkLog(True, [user.assignedId], cmd, data)
            user.sendCommand(cmd, data)
        #cmd = "SYNC_DONE"
        #data = {}
        #self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        #user.sendCommand(cmd, data)

    def userCanJoin(self, user):
        if self.directConnect:
            return True
        if user.username in self.allowedUsers.keys():
            return True

        return False

    def enableDirectConnect(self):
        self.directConnect = True

    def userTypesOnTeam(self, teamId, usertype):
        team = None
        for t in self.teams:
            if t.teamId == teamId:
                team = t

        if team is not None:
            c = 0
            for u in team.networkChannel.sessions:
                if u.userType == usertype:
                    c += 1
            return c
        else:
            self.log.error( "Could not count %s users for team with id %d!" % (usertype, teamId))

    def teamRecommendationForUser(self, user):
        if self.allowedUsers.has_key( user.username ):
            return int( self.allowedUsers[user.username][0] )

        if( user.userType == "Master" or user.userType == "Hero"):
            # only support 1v1 and 2v2 so do some basic checking here

            m1 = self.userTypesOnTeam( Enums.MATCH_TEAM_A, user.userType )
            m2 = self.userTypesOnTeam( Enums.MATCH_TEAM_B, user.userType )

            if m1 == 1 and m1 == m2:
                self.log.error( "Cannot recommend proper team for user %s: both teams are full!" % (user.username, ))
                return Enums.MATCH_TEAM_OBSERVER

            rec = Enums.MATCH_TEAM_OBSERVER

            if m1 > m2:
                rec = Enums.MATCH_TEAM_B
            else:
                rec = Enums.MATCH_TEAM_A
            self.log.info( "Team user counts of usertype %s: A=%d B=%d; recommending teamid %d for user %s" % (user.userType,m1,m2,rec,user.username))
            return rec

        if user.userType == "Observer":
            return Enums.MATCH_TEAM_OBSERVER

        self.log.error( "Could not recommend a team for user %s with user type %s!" % (user.username, user.userType))

    def syncState(self, user, hero):
        if user.userType != "Observer":
            self.log.info("Synchronizing state for %s: hero %s selected." % (user.screenname, hero) )

            faction = user.requestedFaction
            try:
                hero = heroes[faction][hero]
            except IndexError:
                try:
                    hero = heroes[faction][0]
                except IndexError:
                    hero = heroes[0][0]

            # predict the entity id the hero will get on creation. this is VERY EVIL and we
            # really should not be doing this...

            increases = self.world.getItemIncreasesForUser(user, 1)
            self.log.info( "Increases on user %s: %s" % (user.username, str(increases)))
            h = self.world.createGameEntityForUser(
                hero,
                self.world.teamBaseLocations[user.teamId],
                Vector3( 1.0, 0.0, 0.0 ),
                user,
                (
                    ("Username", user.username),
                    ("Team", user.teamId),
                ),
                increases
            )
            userAttr = self.world.getUserEntityForUser(user).getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            userAttr.set("HeroID", h.id)
            self.world.addProcsToUnit(h, self.world.getProcsForUser(user))

            self.log.info( "Created hero %s with id %d" % (h.getName(), h.id))
            #self.log.info( "Added procs: %s to user %s" % (self.world.getProcsForUser(user), user.username))
            #self.log.info( "Hero On attack proc is now: " + str(h.getAttribute( "Procs.On attack")))
            #self.log.info( "Hero On last hit proc is now: " + str(h.getAttribute( "Procs.On last hit")))

            eventio = h.getComponent(Enums.COMP_TYPE_EVENTIO)
            eventio.receiveEvent("Respawn")

        self.syncDataForUser(user)
        self.syncGameStateForUser(user)
        self.syncMapForUser(user)

        gemIncreases = self.world.getGemIncreasesForUser(user, 1)
        goldmines = filter(lambda e: e.getAttribute("Subtype") == "Goldmine", self.world.getBuildingsForTeam(user.teamId))
        for goldmine in goldmines:
            self.world.addIncreasesToBuilding(goldmine, gemIncreases)

        cmd = "G_STATE"
        data = {
            "state": 1,
            "message": "",
        }
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        user.sendCommand(cmd, data)

        cmd = "SYNC_DONE"
        data = {}
        self.writeToNetworkLog(True, [user.assignedId], cmd, data)
        user.sendCommand(cmd, data)

    def join(self, user, team_id):
        if team_id > len(self.teams):
            return False

        user.teamId = team_id

        self.broadcastChannel.addSession(user)
        self.teams[team_id - 1].join(user)

        self.addUser(user, team_id)

        userTeamEntity = self.world.getTeamEntity(user.teamId)
        teamIncreases = self.world.getGemIncreasesForUser(user, 1)
        self.world.addIncreasesToTeam(userTeamEntity, teamIncreases)

        return True

    def leave(self, user):
        self.sendAnalyticsForUser(user, {
            "event_id": "match:leave"
        })
        self.log.info("User %s leaving match...", user.username)
        self.broadcastChannel.removeSession(user)
        for t in self.teams:
            if user in t.networkChannel.sessions:
                t.leave(user)
                self.broadcastChannel.sendCommand("DISCO", {"user": user.username, "team": t.teamId})
        try:
            self.removeUser(user)
        except:
            pass

        if self.playersRequiredToStart == 1:
            self.disconnectAllUsers()
            self.removeAllUsers()

        # if this user's team ran out of players, resolve the match as a win for the opposing team
        # TODO: in the future do this if there is only ONE team left with active players
        count = self.usersInTeam( user.teamId )
        if count == 0 and self.state == Enums.MATCH_STATE_RUNNING:
            opposing_team = Enums.MATCH_TEAM_A if user.teamId == Enums.MATCH_TEAM_B else Enums.MATCH_TEAM_B
            self.log.info( "Team %d has no more users; declaring team %d as winner.", user.teamId, opposing_team )
            self.world.networkCommand(Enums.WORLD_EVENT_END_GAME_WITH_WINNER, opposing_team )

        # end and terminate match when the last user leaves
        #if self.countActiveUsers() == 0:
        #    self.removeAllUsers()
        #    self.end()


    def loadMap(self, mapdef):
        self.mapName = mapdef.name
        self.world.getMatchEntity().getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Map name", self.mapName)
        # a bit of a misnomer here, we're not really loading it per se, just mangling an
        # already loaded map appropriately
        deftotile = "0ABCDE12345678FGH"

        grid = []
        for str in mapdef.tiles:
            for ch in str:
                grid.append(deftotile.index(ch))
        self.world.initialize(mapdef.width, mapdef.height, grid, mapdef.heightMap)

        y = 0.5
        for str in mapdef.tiles:
            x = 0.5
            for ch in str:
                if ch == '7':
                    e = self.world.createGameEntityDelayNetwork("Building slot", Vector3(x, y, 0), Vector3(1, 0, 0), (
                        ("Team", 1),
                    ))
                    e.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
                elif ch == '8':
                    e = self.world.createGameEntityDelayNetwork("Building slot", Vector3(x, y, 0), Vector3(1, 0, 0), (
                        ("Team", 2),
                    ))
                    e.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
                elif ch == 'H':
                    e = self.world.createGameEntityDelayNetwork("Building slot", Vector3(x, y, 0), Vector3(1, 0, 0), (
                        ("Team", 0),
                        ("Neutral", True),
                    ))
                    e.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
                elif ch == '1':
                    self.world.teamBaseLocations[1] = Vector3( x, y, 0 )
                    #e = self.world.createGameEntityDelayNetwork("Townhall", Vector3(x, y, 0), Vector3(0, -1, 0), (
                    #    ("Team", 1),
                    #))
                    #e.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
                elif ch == '2':
                    self.world.teamBaseLocations[2] = Vector3( x, y, 0 )
                    #e = self.world.createGameEntityDelayNetwork("Townhall", Vector3(x, y, 0), Vector3(0, -1, 0), (
                    #    ("Team", 2),
                    #))
                    #e.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
                x += 1.0
            y += 1.0

        for p in mapdef.props:
            self.world.addProp(p["type"], list(listToVector(p["pos"]) + Vector3(.5, .5, .0)))

        for s in mapdef.structures:
            self.world.addStructure(s["type"], listToVector(s["pos"]) + Vector3(.5, .5, .0), s["team"])

        if self.mapName == "Air8":
            e = self.world.createGameEntityDelayNetwork( "Practice dummy", Vector3( 5, 8, 0), Vector3( 1, 0, 0),
                ( ("Team", 1), ) )
            ea = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            ea.set( "Hitpoints", ea.get("Hitpoints") /2 )

            e = self.world.createGameEntityDelayNetwork( "Practice dummy", Vector3( 8, 8, 0), Vector3( 1, 0, 0),
                ( ("Team", 1), ) )
            ea = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            ea.set( "Hitpoints", ea.get("Hitpoints") /2 )

            e = self.world.createGameEntityDelayNetwork( "Practice dummy", Vector3( 11, 10, 0), Vector3( 1, 0, 0),
                ( ("Team", 2), ) )
            ea = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            ea.set( "Hitpoints", ea.get("Hitpoints") /2 )
            ea.set( ("Visibility", "1"), True )  # force it visible

            e = self.world.createGameEntityDelayNetwork( "Practice dummy", Vector3( 14, 10, 0), Vector3( 1, 0, 0),
                ( ("Team", 2), ) )
            ea = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            ea.set( "Hitpoints", ea.get("Hitpoints") /2 )
            ea.set( ("Visibility", "1"), True ) # force it visible

            e = self.world.createGameEntityDelayNetwork( "Practice dummy", Vector3( 13, 6, 0), Vector3( 1, 0, 0),
                ( ("Team", 2), ) )
            ea = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            ea.set( "Hitpoints", ea.get("Hitpoints") /2 )
            ea.set( ("Visibility", "1"), True ) # force it visible

            e = self.world.createGameEntityDelayNetwork( "Practice dummy", Vector3( 16, 7, 0), Vector3( 1, 0, 0),
                ( ("Team", 2), ) )
            ea = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            ea.set( "Hitpoints", ea.get("Hitpoints") /2 )
            ea.set( ("Visibility", "1"), True ) # force it visible

        self.initialized = True

    def requestState(self, newstate):
        self.log.info( "Match with id %d changing state: %d => %d" % (self.id, self.state, newstate))
        self.requestedState = newstate

    def resolveMatchWithWinner(self, winningTeamId):
        self.winningTeamId = winningTeamId

    def resolveMatchAsDraw(self):
        pass

    def getWinningTeam(self):
        for t in self.teams:
            if t.teamId == self.winningTeamId:
                return t
        return None

    def killStatisticsTotalKillsOfUser(self, username, target):
        l = self.killStatistics[username] if self.killStatistics.has_key(username) else None
        if l:
            return l.count( target )

        return 0

    def killStatisticsTotalKills(self, username):
        return len(self.killStatistics[username]) if self.killStatistics.has_key(username) else 0

    def killStatisticsUpdate(self, killer, target):
        if not self.killStatistics.has_key(killer):
            self.killStatistics[killer] = []

        self.killStatistics[killer].append( target )
        #self.log.info( "%s killed %s; total kills %d (total %d for this user)" % (killer, target, self.killStatisticsTotalKills(killer), self.killStatisticsTotalKillsOfUser(killer, target)))

    def updateMatchStatisticsForUser(self, user):
        d = {}
        d["total_kills"] = self.killStatisticsTotalKills( user.username )
        d["level"] = -1
        d["team_tickets"] = -1
        user_hero = self.world.getHeroForUser( user )
        user_team = self.world.getTeamEntityForUser( user )
        if user_hero is not None:
            d["level"] = user_hero.getAttribute( "Stats.Level" )
        if user_team is not None:
            d["team_tickets"] = user_team.getAttribute( "Resources.Tickets" )
        self.matchStatistics[user.username] = d

    def matchStatisticForUser(self, username, stat_key ):
        if self.matchStatistics.has_key( username ) and self.matchStatistics[username].has_key( stat_key ):
            return self.matchStatistics[username][stat_key]
        return None

    def playerStatAssignEvent(self, stat, playername, value):
        #self.log.info( "Stat assign event on player %s stat %s value %s" % (playername, stat, str(value)) )
        if self.userStatistics.has_key(playername):
            self.userStatistics[playername][stat] = int(value)

    def playerStatIncEvent(self, stat, playername, value):
        #self.log.info( "Stat inc event on player %s stat %s value %s" % (playername, stat, str(value)) )
        if self.userStatistics.has_key(playername):
            self.userStatistics[playername][stat] += int(value)

    def twisted_update_cb(self, dt):
        self.frame += 1

        #if self.frame %
        #self.log.debug( "fps=%4.2f dt=%4.2f elapsed=%4.2f frame=%d" % (1.0/SERVER_FPS, dt, self.lastUpdate, self.frame))

        t = time.time()
        self.update(dt)
        self.lastUpdate = t - self.startTime

        # quick and dirty performance measurements

        frametime = time.time() - t
        self.periodCumulativeFrametime += frametime
        measure_period_in_seconds = 10
        measure_period_in_frames = int(measure_period_in_seconds * SERVER_FPS)

        if (self.frame % measure_period_in_frames) == 0:
            cum_ft_ms = self.periodCumulativeFrametime * 1000
            try:
                avg_ft_ms = cum_ft_ms / float(measure_period_in_frames)
                avg_fps = 1.0 / (self.periodCumulativeFrametime / float(measure_period_in_frames))
                frametime_ms = frametime * 1000.0
                frames_per_second = 1.0 / frametime
                self.sendAnalyticsForAllUsers({
                    "event_id": "match:frametime",
                    "frame": self.frame,
                    "frametime_ms": frametime_ms,
                    "frames_per_second": "frames_per_second",
                    "averaged_frames": measure_period_in_frames,
                    "avg_frametime_ms": avg_ft_ms,
                    "avg_frames_per_second": avg_fps,
                })
                #self.log.info("Match with id %d measured frametime on frame %d: %4.4f ms (%4.2f fps)" % (self.id, self.frame, frametime_ms, frames_per_second))
                #self.log.info("Match with id %d measured avg over %d frames: %4.4f ms (%4.2f fps)  cum=%4.2f ms" % (self.id, measure_period_in_frames, avg_ft_ms, avg_fps, cum_ft_ms))
            except ZeroDivisionError:
                self.log.info("Match with id %d measured frametime on frame %d: 0.0000 ms (inf fps)" % (self.id, self.frame,))
            self.periodCumulativeFrametime = 0.0
            # redis:
            # tdta:srv:match:<match_token+uuid>:perf:fps_limit
            # tdta:srv:match:<match_token+uuid>:perf:measure_period
            # tdta:srv:match:<match_token+uuid>:perf:avg_fps_samples
            # tdta:srv:match:<match_token+uuid>:perf:cum_ft_samples
            # tdta:srv:match:<match_token+uuid>:perf:avg_ft_samples


        if frametime > 1.0 / SERVER_FPS:
            frametime_ms = frametime * 1000.0
            self.frameSkips += 1
            self.sendAnalyticsForAllUsers({
                "event_id": "match:frameskip",
                "message": "Server is skipping frames!",
                "frame": self.frame,
                "frametime_ms": frametime_ms,
                "skip_count": self.frameSkips,
            }, "quality")
            self.log.critical("Match with id %d is skipping frames! Frame %d took %4.2f ms" % (self.id, self.frame, frametime_ms))

    def wait(self):
        self.state = Enums.MATCH_STATE_WAITING

    def createBaseForTeam(self, team_id):
        base_prefab = bases[0]
        dir = Vector3( 0, 1, 0 ) if team_id == 1 else Vector3( 0, -1, 0 )
        base = self.world.createGameEntityDelayNetwork( base_prefab, self.world.teamBaseLocations[team_id], dir, ( ("Team", team_id ), ) )
        base.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True    # make sure the network comp is listening
        townAttr = base.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

        # this is bad but someone needs to own them...
        townAttr.set("OwnerId", self.users[0].assignedId )
        townAttr.set("Owner name", self.users[0].username )
        #self.log.info( "Created HQ prefab %s for master user %s" % (base_prefab, user.username))

        users = self.users # [u for u in self.users if u.assignedId is not user.assignedId]
        cmd = "E_CREAT"
        data = {
            "id": base.id,
            "pos": tuple(base.getPosition()),
            "dir": tuple(base.getDirection()),
            "size": float(base.getSize()),
            "attributes": townAttr.getNetworkDictionary(),
        }
        self.writeToNetworkLog(True, self.getAllUserIDs(), cmd, data)
        for u in users:
            u.sendCommand(cmd, data)


    def sync(self):
        # make sure we have bases made in case master user did not join...

        if self.world.getBaseForTeamID(1) is None:
            self.createBaseForTeam( 1 )

        if self.world.getBaseForTeamID(2) is None:
            self.createBaseForTeam( 2 )

        userEntities = self.world.getUserEntities()

        for user in self.users:
            for userEntity in userEntities:
                userAttribs = userEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                if userAttribs.get("User instance") is user:
                    cmd = "SET"
                    data = {
                        "scope": userAttribs.get("Subtype"),
                        "username": userAttribs.get("Username"),
                        "type": Enums.ATTR_SET_MULTIPLE,
                        "attributes": userAttribs.getNetworkDictionary(),
                    }
                    for u in self.users:
                        if u is user or u is None:
                            continue
                        self.writeToNetworkLog(True, [u.assignedId], cmd, data)
                        u.sendCommand(cmd, data)

        for u in self.users:
            self.syncState(u, u.requestedHero)

        self.syncDone = True


    def run(self):
        if self.initialized:
            self.state = Enums.MATCH_STATE_RUNNING
            if self.playersRequiredToStart == 1:
                # if we start with a single player, create a dummy base for the other
                # team so the single player bases work correctly
                dir = Vector3( 0, -1, 0 )
                base = self.world.createGameEntityDelayNetwork( "Townhall", self.world.teamBaseLocations[2], dir,
                                                                ( ("Team", 2 ), ) )
                base.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True    # make sure the network comp is listening

            if self.tutorial:
                self.prepareTutorial()

    def end(self):
        self.requestState( Enums.MATCH_STATE_ENDED )


    def forceTerminate(self):
        self.state = Enums.MATCH_STATE_FORCE_TERM

    def release(self):
        self.world.release()
        self.world = None
        self.gameServer = None
        self.redis = None
        self.broadcastChannel.match = None
        self.broadcastChannel = None
        self.networkCommandHandlers = None
        self.pendingRequests = None
        self.log = None
        if self.users is not None:
            for u in self.users:
                if u is not None:
                    u.match = None
            self.users = None
        if self.teams is not None:
            for t in self.teams:
                if t is not None:
                    t.networkChannel.match = None
                    t.networkChannel = None
                    t.match = None
            self.teams = None
        self.userItemAssignments = None
        self.userGemAssignments = None
        self.userProcAssignments = None
        self.allowedUsers = None
        self.allowedControl = None
        self.networkLog = None
        self.errorLog = None


    def update(self, dt):
        t = time.time()
        if (t - self.startTime) - self.lastNonPong > NONACTIVITY_GRACE_PERIOD:
            self.log.info("Client inactivity for %4.2f seconds; terminating match." % NONACTIVITY_GRACE_PERIOD)
            self.disconnectAllUsers()
            self.forceTerminate()
            return

        if ((t - self.startTime) - self.lastPing) > PING_FREQUENCY:
            self.lastPing = t - self.startTime
            for u in self.broadcastChannel.sessions:
                u.sendCommand("PING", {})
                if t - self.lastNonPong > NONACTIVITY_WARNING_PERIOD:
                    u.sendCommand("MSG", {"channel": 3, "text": "Warning: continued player inactivity will result in the match being terminated!"})

        if self.state is Enums.MATCH_STATE_RUNNING:
            self.world.step(dt)
        elif self.state is Enums.MATCH_STATE_WAITING:
            if time.time() > self.finalJoinTime and not self.syncDone:
                # force the game to go ahead
                self.playersRequiredToStart = len(self.users)
                self.sync()

            if len(self.users) == self.playersRequiredToStart and not self.syncDone:
                self.sync()

            usersReady = True
            for u in self.users:
                if u is None or not u.ready:
                   usersReady = False
                   break

            if len(self.users) < self.playersRequiredToStart:
                usersReady = False

            if usersReady:
                self.run()
        elif self.state is Enums.MATCH_STATE_ENDED:
            # keep network reqs alive even if the game has ended
            self.world.componentSystems[Enums.COMPSYS_TYPE_NETWORK].processRequests()
            self.world.componentSystems[Enums.COMPSYS_TYPE_NETWORK].step()

        if self.requestedState != -1:
            self.state = self.requestedState
            self.requestedState = -1
