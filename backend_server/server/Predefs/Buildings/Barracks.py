import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector


def enqueueUnit(entity, world, unit):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get( "Status" ) == "Upgrading":
        return

    queue = attr.get("Unit queue")
    if world.prefabExists(unit):
        for i in range(len(queue)):
            if queue[i] == "":
                queue[i] = unit
                attr.set("Unit queue", queue)
                # the queue has already been changed by the time Attributes::set tries to find out
                # if a change occurred in the list, so force the update here
                entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, ("Unit queue", queue, queue, Enums.ATTR_SET))
                break

def clearUnitSlot(entity, world, slot):
    try:
        slot = int(slot)
    except:
        world.logError( "Trying to clear slot on entity %d but cannot convert slot to integer: %s" % (entity.id, slot))
        return

    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get("Status") == "Upgrading":
        return

    queue = attr.get("Unit queue")
    if isinstance(queue[slot], int):
        # not allowed to clear locked slots
        return

    # just a standard clear
    if slot < len(queue):
        queue[slot] = ""
        attr.set("Unit queue", queue)
        # the queue has already been changed by the time Attributes::set tries to find out
        # if a change occurred in the list, so force the update here
        entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, ("Unit queue", queue, queue, Enums.ATTR_SET))
    else:
        world.log.critical( "Trying to clear slot %s on %s but queue length is %d!" % (str(slot), entity.getName(), len(queue)))


def openUnitSlot(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get("Status") == "Upgrading":
        return

    queue = attr.get("Unit queue")
    queue.append("")
    attr.set("Unit queue", queue)
    entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, ("Unit queue", queue, queue, Enums.ATTR_SET))


def swapUnitSlots(entity, world, (slot, targetSlot)):
    try:
        slot = int(slot)
        targetSlot = int(targetSlot)
    except:
        world.logError( "Trying to swap slots on entity %d but cannot convert slot/targetslot to integers: %s/%s" % (entity.id, str(slot), str(targetSlot)))
        return

    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get( "Status" ) == "Upgrading":
        return

    queue = attr.get("Unit queue")
    if slot >= len(queue) or targetSlot >= len(queue):
        return
    temp = queue[slot]
    queue[slot] = queue[targetSlot]
    queue[targetSlot] = temp
    attr.set("Unit queue", queue)
    # the queue has already been changed by the time Attributes::set tries to find out
    # if a change occurred in the list, so force the update here
    entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, ("Unit queue", queue, queue, Enums.ATTR_SET))


def spawnQueuedUnit(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")

    # no spawning if incorrect status
    if status == "Dead" or status == "Sold" or status == "Building" or status == "Upgrading" or status == "Freeze" or status == "Unbuilt":
        entity.getComponent(Enums.COMP_TYPE_TIMER).removeTimer("Spawn timer")
        attr.set("Queue index", 0)

    path = attr.get("Unit path")
    if path is None or len(path) is 0:
        bases = filter(
            lambda b: b.getAttribute("Team") is not entity.getAttribute("Team"),
            world.getBases()
        )
        enemyBase = findClosestEntity(entity.getPosition(), bases)
        if enemyBase is not None:
            ourBase = world.getBaseForTeamID(attr.get("Team"))
            attr.set("Unit path", world.findPath(entity.getPosition(), enemyBase.getPosition(), True, [ourBase.getPosition()]))
            path = attr.get("Unit path")

    queueIndex = attr.get("Queue index")
    unitQueue = attr.get("Unit queue")
    attr.inc("Queue index", 1)
    prefab = unitQueue[queueIndex]

    if world.prefabExists(prefab):
        level = attr.get(("Stats", "Level"))

        allincs = []
        for h in world.getHeroesForTeam( attr.get( "Team" ) ):
            u = world.getUserForUnit( h )
            #world.logInfo( "Hero unit %s on team %d owned by user %s" % (h.getName(), attr.get("Team"), u.username ) )
            if u is not None:
                incs = world.getItemIncreasesForUser( u, h.getComponent( Enums.COMP_TYPE_ATTRIBUTES ).get( "Stats.Level" ) )
                if incs is not None:
                    allincs.append( incs  )

        if attr.get("OwnerId") is None:
            unit = world.createGameEntity(
                prefab,
                entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
                Vector3(1, 0, 0),
                (
                    ("Team", attr.get("Team")),
                )
            )
        else:
            unit = world.createGameEntityForUser(
                prefab,
                entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
                Vector3(1, 0, 0),
                attr.get( "OwnerId" ),
                (
                    ("Team", attr.get("Team")),
                )
            )
        if unit is not None:
            for i in allincs:
                world.addIncreasesToCreep( unit, i )

        if unit is not None:
            # grant spawn structure upgrade boosts, if applicable
            unit_attr = unit.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
            bonuses = attr.get( "Unit bonuses" )
            if bonuses and unit_attr:
                for key in bonuses.getDictionary().keys():
                    if unit_attr.get( key ) is not None:
                        blvl = attr.get( ("Stats", "Level") ) - 1
                        blvl = max( 0, blvl )   # insurance
                        val = bonuses.getDictionary()[key]
                        v = float( val ) * blvl
                        unit_attr.inc( key, v )

        if unit is not None:
            bases = filter(
                lambda b: b.getAttribute("Team") is not entity.getAttribute("Team"),
                world.getBases()
            )
            enemyBase = findClosestEntity(entity.getPosition(), bases)
            ourBase = world.getBaseForTeamID(attr.get("Team"))
            if unit.getAttribute("Subtype") == "Balloonist" or unit.getAttribute("Subtype") == "Spectre":
                #path = world.findPath(entity.getPosition(), enemyBase.getPosition(), False, [ourBase.getPosition()])
                startPos = entity.getPosition()
                endPos = enemyBase.getPosition()
                midPos = startPos + (endPos - startPos)/2.0
                midPos.x = random.random()*(world.width - 10) + 5
                path = [startPos, midPos, endPos]
                #path = [addJitterToVector(path[i*3], 2) for i in range(int(len(path)/3))] + [path[-1]]
            else:
                #path = world.findPath(entity.getPosition(), enemyBase.getPosition(), True, [ourBase.getPosition()])
                path = [addJitterToVector(path[i], 1) for i in range(int(len(path)))] + [path[-1]]

        if unit is not None and unit.hasComponent(Enums.COMP_TYPE_WAYPOINTMOVER):
            unit.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER).setWaypoints(path)


    if attr.get("Queue index") >= len(unitQueue):
        entity.getComponent(Enums.COMP_TYPE_TIMER).removeTimer("Spawn timer")
        attr.set("Queue index", 0)


def upgradeBarracks(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    base = world.getBaseForTeamID(attr.get("Team"))
    if base is None:
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    baseLevel = base.getAttribute(("Stats", "Level"))
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    maxLevel = min(baseLevel + 1, maxLevel)
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    attr.inc(("Stats", "Level"), 1)
    attr.inc("Hitpoints", 50)
    attr.inc("Hitpoints maximum", 50)
    if attr.get(("Stats", "Level")) is 3:
        attr.inc(("Stats", "Armor"), 10)

    if attr.get( "Status" ) == "Upgrading":
        attr.set( "Status", "Idle" )

    level = attr.get(("Stats", "Level"))
    user = world.getUserForUnit(entity)
    #increases = world.getGemIncreasesForUser(user, level, level)
    #world.addIncreasesToBuilding(entity, increases)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    eventIO.receiveEvent("Open slot")
    eventIO.receiveEvent("Open slot")

    world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADED, None, entity)
