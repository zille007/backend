from Component import *
from ComponentManager import ComponentManager
from ComponentSystem import *
from SpatialHash import *
from Map import *
from euclid import Vector3
import logging
from EntityManager import EntityManager
from EntityAssembler import *
from EntityDismantler import *
from EntityPrefabs import ENTITY_PREFABS
import Enums
from utils import listToVector, isVector3, dbStringListToTuple, dbListToList, getFromNestedTuple, moveToPerimeter, nestedTupleToDict
import Intersection
import copy


class World(object):
    def __init__(self, network_callback=None, prefabDict=None, usePrefabFile=False):
        self.log = logging.getLogger("server")
        self.dt = None

        self.networkCallback = network_callback

        self.prefabs = {}
        if prefabDict is not None:
            self.addPrefabs(prefabDict)
        if usePrefabFile:
            self.prefabs = copy.copy(EntityPrefabs.ENTITY_PREFABS)

        self.entityManager = EntityManager(self)
        self.entityAssembler = EntityAssembler(self)

        self.entityDismantler = EntityDismantler(self)
        self.componentManagers = [ComponentManager(COMP_TYPES[i], self) for i in range(COMP_TYPE_COUNT)]
        self.componentSystems = [COMPSYS_TYPES[i](self) for i in range(COMPSYS_TYPE_COUNT)]

        self.spatialHash = None
        self.map = None
        self.width = 0
        self.height = 0
        self.mapProps = []

        self.pathCache = {}

        self.ai = None
        self.tutorial = None

        self.matchEntity = None
        self.teamEntities = []
        self.userEntities = []
        self.heroes = []
        self.buildingSlots = []
        self.victoryPoints = []
        self.goldMines = []
        self.bases = []
        self.teamBaseLocations = {}
        self.teamBuildings = [[]]
        self.teamCreeps = [[]]
        self.teamWards = [[]]

        self.destroyedEntities = []

    def initialize(self, mapWidth, mapHeight, mapGrid, heightMap=None):
        if Enums.USE_SPATIAL_HASH:
            self.spatialHash = SpatialHash(mapWidth, mapHeight, Enums.SPATIAL_HASH_BUCKET_SIZE)
        self.map = GridMap(mapWidth, mapHeight, mapGrid, heightMap)
        self.width = mapWidth
        self.height = mapHeight

    def addPrefabs(self, prefabs):
        prefabs.sort(key=lambda p: -1 if p["name"] == "ATTRIBUTES" else 1 if p["name"] == "NETWORK" else 0)
        for p in prefabs:
            self.addPrefab(p["name"], p["components"])

    def addPrefab(self, name, components):
        prefab = []
        for cname in components:
            if cname == "TRANSFORM":
                prefab.append((Enums.COMP_TYPE_TRANSFORM, None))
            elif cname == "PHYSICAL":
                prefab.append((Enums.COMP_TYPE_PHYSICAL, self._getPhysicalPrefab(components[cname])))
            elif cname == "SENSOR":
                prefab.append((Enums.COMP_TYPE_SENSOR, self._getSensorPrefab(components[cname])))
            elif cname == "ATTRIBUTES":
                prefab.insert(0, (Enums.COMP_TYPE_ATTRIBUTES, self._getAttributePrefab(components[cname])))
            elif cname == "TAGS":
                prefab.append((Enums.COMP_TYPE_TAGS, self._getTagsPrefab(components[cname])))
            elif cname == "COMBATATTRIBUTES":
                prefab.append((Enums.COMP_TYPE_COMBATATTRIBUTES, None))
            elif cname == "MOVER":
                prefab.append((Enums.COMP_TYPE_MOVER, None))
            elif cname == "WAYPOINTMOVER":
                prefab.append((Enums.COMP_TYPE_WAYPOINTMOVER, None))
            elif cname == "EFFECT":
                prefab.append((Enums.COMP_TYPE_EFFECT, self._getEffectPrefab(components[cname])))
            elif cname == "FSM":
                prefab.append((Enums.COMP_TYPE_FSM, self._getFSMPrefab(components[cname])))
            elif cname == "PROCESS":
                prefab.append((Enums.COMP_TYPE_PROCESS, self._getProcessPrefab(components[cname])))
            elif cname == "EVENTIO":
                prefab.append((Enums.COMP_TYPE_EVENTIO, self._getEventIOPrefab(components[cname])))
            elif cname == "TIMER":
                prefab.append((Enums.COMP_TYPE_TIMER, self._getTimerPrefab(components[cname])))
            elif cname == "PREDICATE":
                prefab.append((Enums.COMP_TYPE_PREDICATE, self._getPredicatePrefab(components[cname])))
            elif cname == "NETWORK":
                prefab.append((Enums.COMP_TYPE_NETWORK, None))
        self.prefabs[str(name)] = tuple(prefab)

    def _getAttributePrefab(self, attributeDict):
        if attributeDict is None:
            return None
        attributes = []
        for key in attributeDict:
            value = attributeDict[key]
            if isinstance(value, dict):
                attributes.append((str(key), self._getAttributePrefab(value)))
            elif isinstance(value, unicode) or isinstance(value, str):
                attributes.append((str(key), str(value)))
            elif isinstance(value, list):
                if isVector3(value):
                    attributes.append((str(key), listToVector(value)))
                else:
                    attributes.append((str(key), dbListToList(value)))
            else:
                attributes.append((str(key), value))
        return tuple(attributes)

    def _getTagsPrefab(self, tagsList):
        if tagsList is None:
            return None
        return dbStringListToTuple(tagsList)

    def _getPhysicalPrefab(self, physicalList):
        if physicalList is None:
            return None
        physicals = []
        for p in physicalList:
            if p[0] == "Point":
                physicals.append((Enums.SHAPE_TYPE_POINT, listToVector(p[1])))
            elif p[0] == "Circle":
                physicals.append((Enums.SHAPE_TYPE_CIRCLE, listToVector(p[1]), p[2]))
            elif p[0] == "AABB":
                physicals.append((Enums.SHAPE_TYPE_AABB, listToVector(p[1]), p[2], p[3]))
        return tuple(physicals)

    def _getSensorPrefab(self, sensorDict):
        if sensorDict is None:
            return None
        sensors = []
        for key in sensorDict:
            s = sensorDict[key]
            if s[0] == "Point":
                sensors.append((Enums.SHAPE_TYPE_POINT, str(key), listToVector(s[1])))
            elif s[0] == "Circle":
                if isinstance(s[2], unicode) or isinstance(s[2], str):
                    sensors.append((Enums.SHAPE_TYPE_CIRCLE, str(key), listToVector(s[1]), str(s[2])))
                if isinstance(s[2], list):
                    sensors.append((Enums.SHAPE_TYPE_CIRCLE, str(key), listToVector(s[1]), dbStringListToTuple(s[2])))
                else:
                    sensors.append((Enums.SHAPE_TYPE_CIRCLE, str(key), listToVector(s[1]), s[2]))
            elif s[0] == "AABB":
                sensors.append((Enums.SHAPE_TYPE_AABB, str(key), listToVector(s[1]), s[2], s[3]))
        return tuple(sensors)

    def _getEffectPrefab(self, effectDict):
        if effectDict is None:
            return None
        effects = []
        for key in effectDict:
            effects.append((str(key), str(effectDict[key])))
        return tuple(effects)

    def _getFSMPrefab(self, FSMList):
        if FSMList is None:
            return None
        return tuple(FSMList)

    def _getProcessPrefab(self, processDict):
        if processDict is None:
            return None
        processes = []
        for key in processDict:
            p = processDict[key]
            processes.append((str(key), str(p[0]), p[1]))
        return tuple(processes)

    def _getEventIOPrefab(self, eventIODict):
        if eventIODict is None:
            return None
        events = []
        for key in eventIODict:
            value = eventIODict[key]
            if isinstance(value, list):
                events.append((str(key), value))
            else:
                events.append((str(key), str(value)))
        return tuple(events)

    def _getTimerPrefab(self, timerDict):
        if timerDict is None:
            return None
        timers = []
        for key in timerDict:
            t = timerDict[key]
            if len(t) == 4:
                if isinstance(t[2], unicode) or isinstance(t[2], str):
                    timers.append((str(key), str(t[0]), t[1], str(t[2]), t[3]))
                elif isinstance(t[2], list):
                    timers.append((str(key), str(t[0]), t[1], dbStringListToTuple(t[2]), t[3]))
                else:
                    timers.append((str(key), str(t[0]), t[1], t[2], t[3]))
            else:
                if isinstance(t[2], unicode) or isinstance(t[2], str):
                    timers.append((str(key), str(t[0]), t[1], str(t[2])))
                elif isinstance(t[2], list):
                    timers.append((str(key), str(t[0]), t[1], dbStringListToTuple(t[2])))
                else:
                    timers.append((str(key), str(t[0]), t[1], t[2]))
        return tuple(timers)

    def _getPredicatePrefab(self, predicateDict):
        if predicateDict is None:
            return None
        predicates = []
        for key in predicateDict:
            p = predicateDict[key]
            if isinstance(p[2], unicode) or isinstance(p[2], str):
                predicates.append((str(key), str(p[0]), p[1], str(p[2])))
            elif isinstance(p[2], list):
                predicates.append((str(key), str(p[0]), p[1], dbStringListToTuple(p[2])))
            else:
                predicates.append((str(key), str(p[0]), p[1], p[2]))
        return tuple(predicates)

    def setMatch(self, match):
        self.matchEntity = self.createEntity()
        self.assemblePrefab(self.matchEntity, "Match")
        matchAttr = self.matchEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        matchAttr.set("Match instance", match)
        matchAttr.set("Map name", match.mapName)
        self.matchEntity.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
        self.log = match.log

    def addUser(self, user, team, faction, hero, hero_control="Master"):

        self.log.info( "World: Adding user of type %s" % (hero_control,))

        username = user.username if user is not None else "FAKED USER"
        items = user.items if user is not None else {}
        gems = user.gems if user is not None else {}

        userEntity = self.createEntity()
        self.assemblePrefab(userEntity, "User")
        userAttr = userEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        userAttr.set("User instance", user)
        userAttr.set("Username", username)
        userAttr.set("Team", team)
        userAttr.set("Hero", hero)
        userAttr.set("Faction", faction)
        userAttr.set("Control type", hero_control)
        userAttr.set("Items", items)
        #userAttr.set("Gems", [nestedTupleToDict(g) for g in gems])
        userEntity.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
        #if user.userType == "Master":
        #    townhall = self.getBaseForTeamID(team)
        #    townAttr = townhall.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        #    townAttr.set("OwnerId", user.assignedId)
        #    townAttr.set("Owner name", user.username)
        #    workers = townAttr.get("Workers")
        #    for w in workers:
        #        wAttr = w.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        #        wAttr.set("OwnerId", user.assignedId)
        #        wAttr.set("Owner name", user.username)
        self.userEntities.append(userEntity)

    def addTeam(self, team):
        teamEntity = self.createEntity()
        self.assemblePrefab(teamEntity, "Team")
        teamAttr = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        teamAttr.set("Team instance", team)
        teamAttr.set("Team", team.teamId)
        teamEntity.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
        self.teamEntities.append(teamEntity)
        self.teamBuildings.append([])
        self.teamCreeps.append([])
        self.teamWards.append([])

    def removeUser(self, user):
        entity = None
        for e in self.userEntities:
            if e.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("User instance") is user:
                entity = e
                break
        if entity is not None:
            self.userEntities.remove(entity)
            self.entityDismantler.destroyEntity(entity)
        # TODO: what about the user's units?

    def createTutorial(self):
        self.logInfo( "Creating tutorial runner...")
        prefab = "Tutorial"
        if not self.prefabExists(prefab):
            return
        tutorialEntity = self.createEntity()
        self.assemblePrefab( tutorialEntity, prefab )
        self.tutorial = tutorialEntity

        #enemybasepos = self.teamBaseLocations[2]
        #e = self.createGameEntity("Townhall", enemybasepos.copy(), Vector3(0, -1, 0), (
        #    ("Team", 2),
        #))
        #e.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True


    def getTutorialEntity(self):
        return self.tutorial

    def addAI(self, difficulty, user, team):
        self.logInfo("Adding AI of difficulty %s..." % (difficulty,))
        prefab = "Single player AI " + difficulty.lower()
        if not self.prefabExists(prefab):
            return
        aiEntity = self.createEntity()
        self.assemblePrefab(aiEntity, prefab)
        aiAttr = aiEntity.getAttributes()
        aiAttr.set("Team", team)
        aiAttr.set("OwnerId", user.assignedId)
        aiAttr.set("Owner name", user.username)
        self.ai = aiEntity

    def getWards(self):
        wards = []
        for team in self.teamWards:
            for ward in team:
                wards.append(ward)
        return wards

    def getWardsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamWards):
            return self.teamWards[teamID]
        return

    def getHeroes(self):
        return self.heroes

    def getHeroForUser(self, user):
        for h in self.heroes:
            if h is not None and h.getAttribute("Username") == user.username:
                return h
        return None

    def getUserEntities(self):
        return self.userEntities

    def getTeamEntities(self):
        return self.teamEntities

    def getMatchEntity(self):
        return self.matchEntity

    def getTeamEntityForTeam(self, team):
        for t in self.teamEntities:
            if t.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team instance") is team:
                return t
        return None

    def getTeamEntityForUser(self, user):
        for t in self.teamEntities:
            if t.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team") is user.teamId:
                return t
        return None

    def getTeamEntity(self, teamID):
        for t in self.teamEntities:
            if t.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team") is teamID:
                return t
        return None

    def getUserEntityForUser(self, user):
        for u in self.userEntities:
            if u.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Username") == user.username:
                return u
        return None

    def getUserEntity(self, username):
        for u in self.userEntities:
            if u.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Username") == username:
                return u
        return None

    def getTeamCount(self):
        return len(self.teamEntities)

    def getHeroesForTeam(self, teamID):
        heroes = []
        for hero in self.heroes:
            if hero.getAttribute("Team") is teamID:
                heroes.append(hero)
        return heroes

    def getEnemyHeroesForTeam(self, teamID):
        heroes = []
        for hero in self.heroes:
            if hero.getAttribute("Team") is not teamID:
                heroes.append(hero)
        return heroes

    def getUnitsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamBuildings):
            return self.teamBuildings[teamID] + self.teamCreeps[teamID] + self.getHeroesForTeam(teamID)
        return None

    def getEnemyUnitsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamBuildings):
            enemies = self.getEnemyHeroesForTeam(teamID)
            for id in range(len(self.teamBuildings)):
                if id is not teamID:
                    enemies += self.teamBuildings[id] + self.teamCreeps[id]
            return enemies
        return None

    def getCreeps(self):
        creeps = []
        for team in self.teamCreeps:
            creeps += team
        return creeps

    def getCreepsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamCreeps):
            return copy.copy(self.teamCreeps[teamID])
        return None

    def getEnemyCreepsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamCreeps):
            enemies = []
            for id in range(len(self.teamCreeps)):
                if id is teamID:
                    continue
                enemies += self.teamCreeps[id]
            return enemies
        return None

    def getBuildingsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamBuildings):
            return copy.copy(self.teamBuildings[teamID])
        return None

    def getEnemyBuildingsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamBuildings):
            enemies = []
            for id in range(len(self.teamBuildings)):
                if id is teamID:
                    continue
                enemies += self.teamBuildings[id]
            return enemies
        return None

    def getBuildings(self):
        buildings = []
        for team in self.teamBuildings:
            buildings += team
        return buildings

    def getUserForUnit(self, unit):
        return self.getMatch().findUserById(unit.getAttribute("OwnerId"))

    def changeTeamForUnit(self, unit, newTeamID):
        if newTeamID is None:
            return
        attr = unit.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr.get("Type") != "Unit":
            return
        oldTeamID = attr.get("Team")
        if oldTeamID is None:
            return
        isBuilding = unit.hasTag("Building")
        isCreep = unit.hasTag("Creep")
        if 0 <= oldTeamID < len(self.teamBuildings):
            try:
                self.teamBuildings[oldTeamID].remove(unit)
            except ValueError:
                pass
            try:
                self.teamCreeps[oldTeamID].remove(unit)
            except ValueError:
                pass
        if 0 <= newTeamID < len(self.teamBuildings):
            attr.set("Team", newTeamID)
            if isBuilding:
                self.teamBuildings[newTeamID].append(unit)
            if isCreep:
                self.teamCreeps[newTeamID].append(unit)

    def removeUnitFromTeam(self, unit):
        attr = unit.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr.get("Type") != "Unit":
            return
        teamID = attr.get("Team")
        if teamID is None:
            return
        if 0 <= teamID < len(self.teamBuildings):
            try:
                self.teamBuildings[teamID].remove(unit)
            except ValueError:
                pass
            try:
                self.teamCreeps[teamID].remove(unit)
            except ValueError:
                pass
            try:
                self.teamWards[teamID].remove(unit)
            except ValueError:
                pass

    def addUnitToTeam(self, unit, teamID):
        if teamID is None:
            return
        attr = unit.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr.get("Type") != "Unit":
            return
        isBuilding = unit.hasTag("Building")
        isCreep = unit.hasTag("Creep")
        isWard = unit.hasTag("Ward")
        if 0 <= teamID < len(self.teamBuildings):
            attr.set("Team", teamID)
            if isBuilding:
                self.teamBuildings[teamID].append(unit)
            if isCreep:
                self.teamCreeps[teamID].append(unit)
            if isWard:
                self.teamWards[teamID].append(unit)

    def clipWorldPositionToMap(self, position):
        # if inside map, return immediately
        if position.x >= 0.0 and position.x <= self.map.width and position.y >= 0.0 and position.y <= self.map.height:
            return position.copy()

        x = max( 0.5, position.x )
        x = min( x, self.map.width - 0.5)
        y = max( 0.5, position.y )
        y = min( y, self.map.height - 0.5 )
        return Vector3( x, y, position.z )

    def getMapMidpoint(self):
        w, h = (self.map.width, self.map.height)
        return Vector3( w/2.0, h/2.0, 0 )

    def getBases(self):
        return copy.copy(self.bases)

    def getBaseForTeamID(self, teamID):
        for b in self.bases:
            if b.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team") is teamID:
                return b
        return None

    def getGoldMines(self):
        return copy.copy(self.goldMines)

    def getVictoryPoints(self):
        return copy.copy(self.victoryPoints)

    def getVictoryPointsForTeamID(self, teamID):
        return [vp for vp in self.victoryPoints if vp.getAttribute("Team") is teamID]

    def getBuildingSlots(self):
        return copy.copy(self.buildingSlots)

    def getBuildingSlotsForTeamID(self, teamID):
        return [bs for bs in self.buildingSlots if bs.getAttribute("Team") is teamID]

    def getWorkersForTeamID(self, teamID):
        baseAttr = self.getBaseForTeamID(teamID).getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        workers = baseAttr.get("Workers")
        return copy.copy(workers)

    def getIdleWorkerForTeamID(self, teamID):
        workers = self.getWorkersForTeamID(teamID)
        worker = None
        for w in workers:
            if w.getAttribute("Status") == "Idle":
                worker = w
                break
        return worker

    def findPath(self, startPos, endPos, optimize=True, repelPoints=None):
        start = self.map.getGridNodeByWorldPos(startPos)
        end = self.map.getGridNodeByWorldPos(endPos)

        path = self.map.findPath(start, end, repelPoints)
        if len(path) > 1:
            path = path[1:]
        else:
            return [endPos.copy()]

        if optimize:
            newpath = []
            prev_off = None
            prev_tile = path[0]
            offset = (0,0)
            for tile in path:
                offset = (tile[Enums.NODE_DATA][Enums.GRIDNODE_X] - prev_tile[Enums.NODE_DATA][Enums.GRIDNODE_X], tile[Enums.NODE_DATA][Enums.GRIDNODE_Y] - prev_tile[Enums.NODE_DATA][Enums.GRIDNODE_Y])
                if prev_off is not None:
                    if offset[0] != prev_off[0] or offset[1] != prev_off[1]:
                        newpath.append(prev_tile)
                prev_off = offset
                prev_tile = tile
            # must explicitly add the final tile
            if len(path) > 1:
                newpath.append(end)
            path = newpath

        if path is not None:
            p = [Vector3(n[Enums.NODE_DATA][Enums.GRIDNODE_X] + .5, n[Enums.NODE_DATA][Enums.GRIDNODE_Y] + .5, 0) for n in path] + [endPos.copy()]
            return p
        return None

    def isLineWalkable(self, startPos, endPos ):
        # i.e. does the line pass through any map geometry?
        tiles = self.map.rayCast( startPos, endPos )
        for t in tiles:
            self.logInfo( "Raycast from %4.2f,%4.2.f to %4.2f,%4.2f tile: " + str(tiles) )
            pass

    def findLineAvoidBuildings(self, startPos, endPos, lineRadius=.5, avoidDist=2.5, recursionLimit=0, n=0):  # n is for recursion limiting
        if n > recursionLimit:
            return [endPos]
        buildings = self.getBuildings() + self.getVictoryPoints()
        for b in buildings:
            pos = b.getPosition()
            siz = b.getSize()
            startPos = moveToPerimeter(startPos, pos, siz + .1)
            endPos = moveToPerimeter(endPos, pos, siz + .1)
            if Intersection.lineSegmentToCircle(startPos, endPos, pos, siz + lineRadius):
                normal = (endPos - startPos).normalized()
                normal2 = Vector3(-normal.y, normal.x)
                normal = Vector3(normal.y, -normal.x)
                distSqr = ((pos + normal) - startPos).magnitude_squared()
                distSqr2 = ((pos + normal2) - startPos).magnitude_squared()
                if distSqr < distSqr2:
                    return self.findLineAvoidBuildings(startPos, normal*avoidDist + pos, lineRadius, avoidDist, recursionLimit, n + 1) + self.findLineAvoidBuildings(normal*avoidDist + pos, endPos, lineRadius, avoidDist, recursionLimit, n + 1)
                else:
                    return self.findLineAvoidBuildings(startPos, normal2*avoidDist + pos, lineRadius, avoidDist, recursionLimit, n + 1) + self.findLineAvoidBuildings(normal2*avoidDist + pos, endPos, lineRadius, avoidDist, recursionLimit, n + 1)
        return [endPos]

    def addProp(self, typeId, pos):
        self.mapProps.append((typeId, pos))

    def addStructure(self, typeId, pos, teamId):
        # map from old building types to new entities

        b_map = {2: "Goldmine", 6: "Victory point", 7: "Goldmine", 8: "Neutral boss lair"}

        etype = b_map[typeId] if b_map.has_key(typeId) else None
        if etype is None:
            return

        self.log.debug("Creating structure of typeId %d (entity prefab id %s) at %s for team %d" % (typeId, etype, str(pos), teamId))
        e = self.createEntity()
        self.assemblePrefab(e, etype)
        xform = e.getComponent(Enums.COMP_TYPE_TRANSFORM)
        xform.setWorldPosition(pos)
        xform.setWorldDirection(Vector3(0, -1, 0))
        attr = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        attr.set("Team", teamId)
        if attr.get("Type") == "Unit":
            teamID = attr.get("Team")
            self.addUnitToTeam(e, teamID)
            if Enums.CALCULATE_VISIBILITY:
                for i in range(self.getTeamCount()):
                    attr.set(("Visibility", str(i + 1)), teamID is (i + 1))
            else:
                for i in range(self.getTeamCount()):
                    attr.set(("Visibility", str(i + 1)), True)
        e.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True

    def createEntity(self):
        return self.entityAssembler.createEntity()

    def prefabExists(self, prefabName):
        return self.prefabs.has_key(prefabName)

    def assemblePrefab(self, entity, prefab, pos=None):
        self.entityAssembler.assemblePrefab(entity, prefab, pos)
        if prefab == "Building slot":
            self.buildingSlots.append(entity)
        elif prefab == "Victory point":
            self.victoryPoints.append(entity)
        elif prefab == "Goldmine":
            self.goldMines.append(entity)
        elif prefab == "Townhall" or prefab == "Fay throne":
            self.bases.append(entity)

    def createGameEntity(self, prefabName, pos, dir, attribs=None, increases=None):
        entity = self.createEntity()
        self.assemblePrefab(entity, prefabName, pos)
        xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        xform.setWorldPosition(pos)
        xform.setWorldDirection(dir)
        attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        attr.initialize(attribs)
        if attr.get("Type") == "Unit":
            teamID = attr.get("Team")
            self.addUnitToTeam(entity, teamID)
            if entity.hasTag("Creep"):
                if increases:
                    self.addIncreasesToCreep(entity, increases)
            elif entity.hasTag("Building"):
                if increases:
                    self.addIncreasesToBuilding(entity, increases)
            elif entity.hasTag("Hero"):
                self.heroes.append(entity)
                if increases:
                    self.addIncreasesToHero(entity, increases)
            if Enums.CALCULATE_VISIBILITY:
                for i in range(self.getTeamCount()):
                    attr.set(("Visibility", str(i + 1)), teamID is (i + 1))
            else:
                for i in range(self.getTeamCount()):
                    attr.set(("Visibility", str(i + 1)), True)
        self.networkCommand(Enums.WORLD_EVENT_ENTITY_CREATE, None, entity)
        return entity

    def createGameEntityDelayNetwork(self, prefabName, pos, dir, attribs=None, increases=None):
        entity = self.createEntity()
        self.assemblePrefab(entity, prefabName, pos)
        xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        xform.setWorldPosition(pos)
        xform.setWorldDirection(dir)
        attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        attr.initialize(attribs)
        if attr.get("Type") == "Unit":
            teamID = attr.get("Team")
            self.addUnitToTeam(entity, teamID)
            if entity.hasTag("Creep"):
                if increases:
                    self.addIncreasesToCreep(entity, increases)
            elif entity.hasTag("Building"):
                if increases:
                    self.addIncreasesToBuilding(entity, increases)
            elif entity.hasTag("Hero"):
                self.heroes.append(entity)
                if increases:
                    self.addIncreasesToHero(entity, increases)
            if Enums.CALCULATE_VISIBILITY:
                for i in range(self.getTeamCount()):
                    attr.set(("Visibility", str(i + 1)), teamID is (i + 1))
            else:
                for i in range(self.getTeamCount()):
                    attr.set(("Visibility", str(i + 1)), True)
        return entity

    def createGameEntityForUser(self, prefabName, pos, dir, userOrUserId, attribs=None, increases=None):
        if userOrUserId is None:
            self.logError("Trying to create game entity from prefab %s for a null user!" % (prefabName,))
            return None

        user = userOrUserId
        if type(userOrUserId) is int:
            user = self.getMatch().findUserById(userOrUserId)
            if user is None:
                self.logError("Trying to create game entity from prefab %s to non-existent userid %d" % (prefabName, userOrUserId))
                return None

        if attribs is None:
            attribs = ()

        e = self.createGameEntity(prefabName, pos, dir, attribs  + ( ("OwnerId", user.assignedId), ("Owner name", user.username) ), increases)
        return e

    def createGameEntityForUserDelayNetwork(self, prefabName, pos, dir, userOrUserId, attribs=None, increases=None):
        if userOrUserId is None:
            self.logError( "Trying to create delayed game entity from prefab %s for a null user!" % (prefabName,))
            return None

        user = userOrUserId
        if type(userOrUserId) is int:
            user = self.getMatch().findUserById(userOrUserId)
            if user is None:
                self.logError( "Trying to create delayed game entity from prefab %s to non-existent userid %d" % (prefabName, userOrUserId))
                return None

        if attribs is None:
            attribs = ()

        e = self.createGameEntityDelayNetwork(prefabName, pos, dir, attribs + ( ("OwnerId", user.assignedId), ("Owner name", user.username) ), increases)
        return e

    def getItemIncreasesForUser(self, user, heroLevel, levelMin=1):
        increases = []
        if user is not None:
            for item in user.items:
                level = item["level_req_hero"]
                if level is None:
                    level = 1
                if levelMin <= level <= heroLevel:
                    increases.append( item["increases"] )
            if len(increases) is 0:
                return None
        return increases

    def getGemIncreasesForUser(self, user, buildingLevel, levelMin=1):
        return self.getItemIncreasesForUser( user, buildingLevel, levelMin )

    def getProcsForUser(self, user):
        if user is not None:
            return user.procs
        return None

    def addIncreasesToTeam(self, team, increases):
        if increases is None:
            return
        attr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        for inc in increases:
            for incType in inc.keys():
                if incType == "team" and team.hasTag("Team"):
                    attr.applyMultiple(inc[incType].items())

    def addIncreasesToBuilding(self, building, increases):
        self.logInfo( "Will add increases %s to building %s" % (str(increases,), building.getName()))
        if increases is None:
            return
        attr = building.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        for inc in increases:
            for incType in inc.keys():
                if incType == "buildings" and building.hasTag("Building"):
                    attr.applyMultiple(inc[incType].items())
                elif incType == attr.get("Subtype"):
                    attr.applyMultiple(inc[incType].items())

    def addIncreasesToHero(self, hero, increases):
        self.logInfo( "Will add increases %s to hero %s" % (str(increases,), hero.getName()))
        if increases is None:
            return
        attr = hero.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        for inc in increases:
            for incType in inc.keys():
                if incType == "hero" and hero.hasTag("Hero"):
                    attr.applyMultiple(inc[incType].items())
                elif incType == attr.get("Subtype"):
                    attr.applyMultiple(inc[incType].items())

    def addIncreasesToCreep(self, creep, increases):
        self.logInfo( "Will add increases %s to creep %s" % (str(increases,), creep.getName()))
        if increases is None:
            return
        attr = creep.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        for inc in increases:
            for incType in inc.keys():
                if incType == "creeps" and creep.hasTag("Creep"):
                    attr.applyMultiple(inc[incType].items())
                elif incType == attr.get("Subtype"):
                    attr.applyMultiple(inc[incType].items())
        if creep is not None and attr is not None:
            dmgmin = attr.get( "Damage minimum" )
            dmgmax = attr.get( "Damage maximum" )
            if dmgmin is not None and dmgmax is not None:
                self.logInfo( "Creep %s hp %d/%d speed %4.2f damage %d-%d" % (
                    creep.getName(),
                    attr.get( "Hitpoints"), attr.get("Hitpoints maximum"),
                    attr.get( "Speed"), dmgmin, dmgmax
                ))


    def addProcsToUnit(self, unit, procs):
        self.logInfo( "Will add procs %s to unit %s" % (str(procs), unit.getName()))
        if procs is None or not isinstance(procs, list) or len(procs) is 0:
            return
        attr = unit.getAttributes()
        for p in procs:
            procList = attr.get("Procs." + p[0])
            if procList is not None:
                # p[0] is the proc event, which can be for example On damage or On attack
                # p[1] is the hero level that is required for the proc to start working
                # p[2] is the proc chance, which is a float in the closed range [0.0, 1.0]
                # p[3] is the proc effect that takes place when the proc happens to happen. Can be for example Damage token, which gives a damage multiplier to the next attack.
                # p[4] is the data that is fed to the proc effect handler when the proc happens.
                procList.append([p[1], p[2], p[3], p[4]])

    def getEntityByID(self, id):
        return self.entityManager.getEntityByID(id)

    def getEntities(self):
        return self.entityManager.getEntities()

    def queryEntities(self, fltr):
        return self.entityManager.filterEntities(fltr)

    def queryEntitiesByPoint(self, center, fltr=None):
        if Enums.USE_SPATIAL_HASH:
            if fltr:
                return [e for e in map(lambda p: p.entity, self.spatialHash.queryPoint(center)) if not e.isDestroyed() and fltr(e)]
            else:
                return [e for e in map(lambda p: p.entity, self.spatialHash.queryPoint(center)) if not e.isDestroyed()]
        else:
            if fltr:
                return [p.entity for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsPoint(center) and not p.entity.isDestroyed() and fltr(p.entity)]
            else:
                return [p.entity for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsPoint(center) and not p.entity.isDestroyed()]

    def queryEntitiesByCircle(self, center, radius, fltr=None):
        if Enums.USE_SPATIAL_HASH:
            if fltr:
                return [e for e in map(lambda p: p.entity, self.spatialHash.queryCircle(center, radius)) if not e.isDestroyed() and fltr(e)]
            else:
                return [e for e in map(lambda p: p.entity, self.spatialHash.queryCircle(center, radius)) if not e.isDestroyed()]
        else:
            if fltr:
                return [p.entity for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsCircle(center, radius) and not p.entity.isDestroyed() and fltr(p.entity)]
            else:
                return [p.entity for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsCircle(center, radius) and not p.entity.isDestroyed()]

    def queryEntitiesByAABB(self, lowerLeft, width, height):
        ## TODO
        if Enums.USE_SPATIAL_HASH:
            return []
        else:
            return []

    def queryTeamUnitsByPoint(self, teamID, center, fltr=None):
        if fltr:
            return [e for e in self.getUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsPoint(center) and fltr(e)]
        else:
            return [e for e in self.getUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsPoint(center)]

    def queryTeamUnitsByCircle(self, teamID, center, radius, fltr=None):
        if fltr:
            return [e for e in self.getUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsCircle(center, radius) and fltr(e)]
        else:
            return [e for e in self.getUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsCircle(center, radius)]

    def queryEnemyUnitsByPoint(self, teamID, center, fltr=None):
        if fltr:
            return [e for e in self.getEnemyUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsPoint(center) and fltr(e)]
        else:
            return [e for e in self.getEnemyUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsPoint(center)]

    def queryEnemyUnitsByCircle(self, teamID, center, radius, fltr=None):
        if fltr:
            return [e for e in self.getEnemyUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsCircle(center, radius) and fltr(e)]
        else:
            return [e for e in self.getEnemyUnitsForTeam(teamID) if e.getComponent(Enums.COMP_TYPE_PHYSICAL).intersectsCircle(center, radius)]

    def iterateHeroes(self):
        for hero in self.heroes:
            yield hero

    def iterateEnemyHeroesForTeam(self, teamID):
        for hero in self.heroes:
            if hero.getAttribute("Team") is not teamID:
                yield hero

    def iterateCreeps(self):
        for id in range(len(self.teamCreeps)):
            for creep in self.teamCreeps[id]:
                yield creep

    def iterateCreepsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamCreeps):
            for creep in self.teamCreeps[teamID]:
                yield creep

    def iterateEnemyCreepsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamCreeps):
            teamIDs = range(len(self.teamCreeps))
            teamIDs.remove(teamID)
            teamIDs.reverse()
            for id in teamIDs:
                for creep in self.teamCreeps[id]:
                    yield creep

    def iterateEnemyCreepsAndHeroesForTeam(self, teamID):
        for hero in self.heroes:
            if hero.getAttribute("Team") is not teamID:
                yield hero
        if 0 <= teamID < len(self.teamCreeps):
            teamIDs = range(len(self.teamCreeps))
            teamIDs.remove(teamID)
            teamIDs.reverse()
            for id in teamIDs:
                for creep in self.teamCreeps[id]:
                    yield creep

    def iterateBuildings(self):
        for id in range(len(self.teamBuildings)):
            for building in self.teamBuildings[id]:
                yield building

    def iterateBuildingsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamBuildings):
            for building in self.teamBuildings[teamID]:
                yield building

    def iterateEnemyBuildingsForTeam(self, teamID):
        if 0 <= teamID < len(self.teamBuildings):
            teamIDs = range(len(self.teamBuildings))
            teamIDs.remove(teamID)
            teamIDs.reverse()
            for id in teamIDs:
                for building in self.teamBuildings[id]:
                    yield building

    def iterateEnemyUnitsForTeam(self, teamID):
        for hero in self.heroes:
            if hero.getAttribute("Team") is not teamID:
                yield hero
        if 0 <= teamID < len(self.teamCreeps):
            teamIDs = range(len(self.teamCreeps))
            teamIDs.remove(teamID)
            teamIDs.reverse()
            for id in teamIDs:
                for creep in self.teamCreeps[id]:
                    yield creep
        if 0 <= teamID < len(self.teamBuildings):
            teamIDs = range(len(self.teamBuildings))
            teamIDs.remove(teamID)
            teamIDs.reverse()
            for id in teamIDs:
                for building in self.teamBuildings[id]:
                    yield building

    def getEntityCount(self):
        return self.entityManager.getEntityCount()

    def destroyEntity(self, entity):
        if entity is None or entity.isDestroyed():
            return
        self.destroyedEntities.append(entity)
        self.entityManager.removeEntity(entity)
        self.removeUnitFromTeam(entity)
        entity.destroy()
        entity.getComponent(Enums.COMP_TYPE_NETWORK).activate()

    def destroyEntityByID(self, id):
        entity = self.getEntityByID(id)
        if entity is None or entity.isDestroyed():
            return
        self.destroyedEntities.append(entity)
        self.entityManager.removeEntity(entity)
        self.removeUnitFromTeam(entity)
        entity.destroy()
        entity.getComponent(Enums.COMP_TYPE_NETWORK).activate()

    def getDestroyedEntities(self):
        return self.destroyedEntities

    def releaseDestroyedEntity(self, entity):
        self.entityDismantler.destroyEntity(entity)

    def removeDestroyedEntities(self):
        self.destroyedEntities = filter(lambda e: not e.isReleased(), self.destroyedEntities)

    def attachComponent(self, entity, componentType, initList=None):
        self.entityAssembler.attachComponent(entity, componentType, initList)

    def detachComponent(self, entity, componentType):
        self.entityDismantler.detachComponent(entity, componentType)

    def getAllComponents(self, componentType):
        return self.componentManagers[componentType].getBuffer()

    def getReservedComponents(self, componentType):
        return self.componentManagers[componentType].getReserved()

    def getAttachedComponents(self, componentType):
        return self.componentManagers[componentType].getAttached()

    def getActiveComponents(self, componentType):
        return self.componentManagers[componentType].getActive()

    def getAwakeComponents(self, componentType):
        return self.componentManagers[componentType].getAwake()

    def queryComponents(self, componentType, fltr):
        return self.componentManagers[componentType].filterComponents(fltr)

    def queryPhysicalsByPoint(self, center, fltr=None):
        if Enums.USE_SPATIAL_HASH:
            if fltr:
                return [p for p in self.spatialHash.queryPoint(center) if not p.entity.isDestroyed() and fltr(p)]
            else:
                return [p for p in self.spatialHash.queryPoint(center) if not p.entity.isDestroyed()]
        else:
            if fltr:
                return [p for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsPoint(center) and not p.entity.isDestroyed() and fltr(p)]
            else:
                return [p for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsPoint(center) and not p.entity.isDestroyed()]

    def queryPhysicalsByCircle(self, center, radius, fltr=None):
        if Enums.USE_SPATIAL_HASH:
            if fltr:
                return [p for p in self.spatialHash.queryCircle(center, radius) if not p.entity.isDestroyed() and fltr(p)]
            else:
                return [p for p in self.spatialHash.queryCircle(center, radius) if not p.entity.isDestroyed()]
        else:
            if fltr:
                return [p for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsCircle(center, radius) and not p.entity.isDestroyed() and fltr(p)]
            else:
                return [p for p in self.componentManagers[Enums.COMP_TYPE_PHYSICAL].getActive() if p.intersectsCircle(center, radius) and not p.entity.isDestroyed()]

    def queryPhysicalsByAABB(self, lowerLeft, width, height, fltr=None):
        ## TODO
        if Enums.USE_SPATIAL_HASH:
            return []
        else:
            return []

    def queryLineOfSight(self, startPos, endPos):
        nodes = self.map.rayCast(startPos, endPos)
        height = nodes[0][Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
        ascending = False
        for i in range(len(nodes)):
            nodeHeight = nodes[i][Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
            if nodeHeight > height:
                height = nodeHeight
                ascending = True
            elif nodeHeight < height and ascending:
                return False
        return True

    def queryLineOfSightForEntity(self, entity, targetPos):
        return self.queryLineOfSight(entity.getPosition(), targetPos)

    def queryMapObstacle(self, startPos, endPos):
        nodes = self.map.rayCast(startPos, endPos)
        height = nodes[0][Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
        for i in range(len(nodes)):
            nodeHeight = nodes[i][Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
            if abs(nodeHeight - height) > .75:
                return True
        return False

    def broadcastEvent(self, eventType, data):
        for e in self.componentManagers[Enums.COMP_TYPE_EVENTIO].getActive():
            e.receiveEvent(eventType, data)

    def sendEventToFilteredEntities(self, eventType, data, fltr):
        entities = filter(fltr, map(lambda e: e.entity, self.componentManagers[Enums.COMP_TYPE_EVENTIO].getActive()))
        for e in entities:
            e.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent(eventType, data)

    def sendEventToEntity(self, eventType, data, id):
        entity = self.entityManager.getEntityByID(id)
        if entity:
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent(eventType, data)

    def networkCommand(self, eventType, data=None, entity=None):
        if eventType == Enums.WORLD_EVENT_ENTITY_DEATH and entity.hasTag( "Hero" ):
            originatorID, = data
            originator = self.getEntityByID( originatorID )
            if originator is not None and (originator.hasTag( "Hero" ) or originator.getAttribute( "Type" ) == "Projectile"):
                owner_username = entity.getAttribute( "Owner name" )
                killer_username = originator.getAttribute( "Owner name" )
                self.getMatch().killStatisticsUpdate( killer_username, owner_username )

        # a network event on entity (or without one), for now just pass it up the chain to match
        # and let it resolve the network traffic
        if self.networkCallback is not None:
            self.networkCallback(eventType, data, entity)
        else:
            self.log.error( "Network event %d on entity id %d but world network callback is empty!" % (eventType, entity.id) )

    def networkRequest(self, user, request, sequence_number, request_dict):
        # a received network request. network system must take care of this,
        # so just pass it on. we can do prefiltering here if we think we can and should
        self.componentSystems[Enums.COMPSYS_TYPE_NETWORK].queueRequest(user, request, sequence_number, request_dict)

    def networkAbilityImmediateSuccess(self, abilityName, entity):
        # convenience
        self.networkCommand(Enums.WORLD_EVENT_CAST_STARTED, (abilityName, 0.0), entity)
        self.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, abilityName, entity)

    def step(self, dt):
        self.dt = dt

        try:
            self.componentSystems[Enums.COMPSYS_TYPE_NETWORK].processRequests()

            self.componentSystems[Enums.COMPSYS_TYPE_TRANSFORM].step()
            self.componentSystems[Enums.COMPSYS_TYPE_PREDICATE].step()
            self.componentSystems[Enums.COMPSYS_TYPE_TIMER].step()
            self.componentSystems[Enums.COMPSYS_TYPE_FSM].step()
            self.componentSystems[Enums.COMPSYS_TYPE_EVENTIO].step()
            self.componentSystems[Enums.COMPSYS_TYPE_PROCESS].step()
            self.componentSystems[Enums.COMPSYS_TYPE_WAYPOINTMOVER].step()
            self.componentSystems[Enums.COMPSYS_TYPE_MOVER].step()
            self.componentSystems[Enums.COMPSYS_TYPE_PHYSICAL].step()
            self.componentSystems[Enums.COMPSYS_TYPE_VISIBILITY].step()

            #this should be the last component system processed
            self.componentSystems[Enums.COMPSYS_TYPE_NETWORK].step()
            self.componentSystems[Enums.COMPSYS_TYPE_DEATH].step()
        except ComponentError as e:
            self.log.critical( "On frame %d, t=%4.2f: component error: %s" % (self.getMatch().frame, self.getMatch().lastUpdate, str(e)) )
            raise e

    def getMatch(self):
        return self.matchEntity.getAttribute("Match instance")

    def logInfo(self, msg):
        if self.matchEntity is not None:
            match = self.matchEntity.getAttribute("Match instance")
            if match is not None:
                match.log.info(msg)
                return
        self.log.info( str(msg) )

    def logDebug(self, msg):
        if self.matchEntity is not None:
            match = self.matchEntity.getAttribute("Match instance")
            if match is not None:
                match.log.debug(msg)
                return
        self.log.debug( str(msg) )

    def logWarning(self, msg):
        if self.matchEntity is not None:
            match = self.matchEntity.getAttribute("Match instance")
            if match is not None:
                match.log.warning(msg)
                return
        self.log.warn( str(msg) )

    def logError(self, msg):
        if self.matchEntity is not None:
            match = self.matchEntity.getAttribute("Match instance")
            if match is not None:
                match.log.error(msg)
                return
        self.log.error( str(msg) )

    def release(self):
        self.log = None
        self.networkCallback = None
        self.componentSystems[Enums.COMPSYS_TYPE_NETWORK].networkRequestHandlers = None
        self.prefabs = None
        self.entityManager = None
        self.entityAssembler = None
        self.entityDismantler = None
        self.componentManagers = None
        self.componentSystems = None
        self.spatialHash = None
        self.map = None
        self.mapProps = None
        self.ai = None
        if self.matchEntity is not None:
            self.matchEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Match instance", None)
            self.matchEntity = None
        if self.teamEntities is not None:
            for t in self.teamEntities:
                if t is not None:
                    t.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Team instance", None)
            self.teamEntities = None
        if self.userEntities is not None:
            for u in self.userEntities:
                if u is not None:
                    u.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("User instance", None)
            self.userEntities = None
        self.heroes = None
        self.buildingSlots = None
        self.victoryPoints = None
        self.bases = None
        self.teamBaseLocations = None
        self.teamBuildings = None
        self.teamCreeps = None
        self.teamWards = None
        self.destroyedEntities = None