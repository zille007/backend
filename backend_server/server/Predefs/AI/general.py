import Enums
import random
from euclid import *
from utils import findClosestEntity


general_macro_unit_map = {
    "Northerners": {
        "Garrison":"Garrison",
        "Barracks":"Barracks",
        "Axeman":"Axeman",
        "Hunter":"Hunter",
        "Sapper":"Sapper",
        "Balloonist":"Balloonist",
        "Townhall":"Townhall"
    },
    "Fay": {
        "Garrison":"Goblin ancestor",
        "Barracks":"Battlestump",
        "Axeman":"Satyr",
        "Hunter":"Nymph",
        "Sapper":"Ghost",
        "Balloonist":"Spectre",
        "Townhall":"Fay throne"
    }
}

def aiBuildHandler(entity, world, (wantBuildingType, location)):
    attr = entity.getAttributes()
    user = world.getMatch().findUserById( attr.get( "OwnerId") )

    if user.userType != "Master":
        return

    faction = "Northerners" if user.requestedFaction is 0 else "Fay" if user.requestedFaction is 1 else "Parliament"
    unitmap = general_macro_unit_map[faction]

    if wantBuildingType in unitmap.keys():
        buildingType = unitmap[wantBuildingType]
    else:
        buildingType = wantBuildingType  # try this anyway

    if not world.prefabExists(buildingType):
        return

    team = attr.get("Team")
    user = world.getUserForUnit(entity)
    base = world.getBaseForTeamID(team)
    baseAttr = base.getAttributes()
    basePos = base.getPosition()
    if isinstance(location, Vector3):
        basePos = location
    elif location == "Left":
        basePos = basePos + Vector3(-12.5, -5.0, 0.0)
    elif location == "Right":
        basePos = basePos + Vector3(12.5, -5.0, 0.0)
    elif location == "Center":
        basePos = basePos + Vector3(0.0, -10.0, 0.0)

    slots = [s for s in world.getBuildingSlotsForTeamID(team) if s.getAttribute("Status") == "Open"]
    if len(slots) is 0:
        return
    slot = findClosestEntity(basePos, slots)

    workers = baseAttr.get("Workers")
    worker = None
    for w in workers:
        if w.getAttribute("Task") == "None":
            worker = w
            break
    if worker is None:
        return

    slot.getAttributes().set("Status", "Closed")
    building = world.createGameEntityForUser(
        buildingType,
        slot.getPosition(),
        Vector3(0, -1, 0),
        user,
        (
            ("Team", team),
            ("Status", "Unbuilt"),   # will be set to building once the worker arrives
        )
    )
    buildingFsm = building.getComponent(Enums.COMP_TYPE_FSM)
    if buildingFsm:
        buildingFsm.setState("Unbuilt")
    worker.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Build", building.id)
    if building is not None:
        buildings = attr.get("Buildings")
        buildings.append(building.id)
        attr.set("Buildings", buildings)


def aiTrainHandler(entity, world, (creepType, buildingIndex)):
    if not world.prefabExists(creepType):
        return
    attr = entity.getAttributes()
    buildings = attr.get("Buildings")
    if len(buildings) <= buildingIndex:
        return
    bid = buildings[buildingIndex]
    b = world.getEntityByID(bid)
    if b is not None and b.getAttribute("Subtype") == "Barracks" and b.getAttribute("Status") == "Idle":
        b.receiveEvent("Enqueue", creepType)


def aiUpgradeHandler(entity, world, buildingIndex):
    attr = entity.getAttributes()
    if isinstance(buildingIndex, str) or isinstance(buildingIndex, unicode):
        if buildingIndex == "Townhall":
            team = attr.get("Team")
            base = world.getBaseForTeamID(team)
            base.receiveEvent("Upgrade start")
    else:
        buildings = attr.get("Buildings")
        if buildings is not None and len(buildings) > 0:
            world.logInfo( "AI wants to upgrade building at index %d; building list length is %d" % (buildingIndex, len(buildings)))
            if buildingIndex < len(buildings):
                bid = attr.get("Buildings")[buildingIndex]
                b = world.getEntityByID(bid)
                if b is not None:
                    b.receiveEvent("Upgrade start")


def aiRepairHandler(entity, world, buildingIndex):
    pass


def aiCollectGoldHandler(entity, world, args):
    attr = entity.getAttributes()
    team = attr.get("Team")
    goldmines = [b for b in world.getBuildingsForTeam(team) if b.getAttribute("Subtype") == "Goldmine"]
    user = world.getMatch().findUserById( attr.get( "OwnerId") )
    match = world.getMatch()
    for goldmine in goldmines:
        if user is not None and match is not None:
            world.getMatch().playerStatIncEvent( "gold_collected", user.username, goldmine.getAttribute( "Gold" ) )
        goldmine.receiveEvent("Collect")


def aiCheckBuildingsHandler(entity, world, args):
    attr = entity.getAttributes()
    team = attr.get("Team")
    buildings = [b for b in world.getBuildingsForTeam(team) if b.getAttribute("Subtype") != "Townhall" and b.getAttribute("Subtype") != "Goldmine"]
    for b in buildings:
        hp = b.getAttribute("Hitpoints")
        hpMax = b.getAttribute("Hitpoints maximum")
        if hp < hpMax:
            worker = world.getIdleWorkerForTeamID(team)
            if worker:
                eventIO = worker.getComponent(Enums.COMP_TYPE_EVENTIO)
                eventIO.receiveEvent("Repair", b.id)
            return