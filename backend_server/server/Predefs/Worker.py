import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector

def workerRepairHandler(entity, world, buildingID):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    building = world.getEntityByID(buildingID)
    if building is None:
        return
    attr.set("Target", buildingID)
    attr.set("Task", "Repair")
    attr.set("Status", "Repairing")

    battr = building.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set("Repair amount", int(battr.get("Hitpoints maximum") * attr.get("Repair percentage")))

    entity.getComponent(Enums.COMP_TYPE_FSM).setState("Repairing")
    path = world.findPath(entity.getPosition(), building.getPosition())
    entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER).setWaypoints(path)


def workerRepairTick(entity, world, args):
    attr = entity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    building = world.getEntityByID( attr.get( "Target" ) )

    if building is not None:
        battr = building.getComponent( Enums.COMP_TYPE_ATTRIBUTES )

        repair_remaining = attr.get( "Repair amount" )
        if repair_remaining > 0:
            repair = min( attr.get( "Repair per tick" ), repair_remaining )
            repair_remaining -= repair
            hitpoints = battr.get("Hitpoints")
            maxHitpoints = battr.get("Hitpoints maximum")

            # check if the player has enough gold for the repair
            cost = attr.get( "Repair cost" ) * repair
            team = world.getTeamEntity( attr.get("Team") )
            if team.getAttribute( ("Resources", "Gold") ) < cost or hitpoints == maxHitpoints:
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Return")
                return

            hitpoints = battr.get("Hitpoints")
            maxHitpoints = battr.get("Hitpoints maximum")
            if hitpoints >= maxHitpoints:
                return
            healCap = hitpoints + repair - maxHitpoints
            if healCap > 0.0:
                repair -= healCap
            battr.inc("Hitpoints", repair)

            repair_remaining = max( 0, repair_remaining )
            attr.set( "Repair amount", repair_remaining)

            team.getComponent( Enums.COMP_TYPE_ATTRIBUTES ).inc( ("Resources", "Gold"), -cost )
            world.networkCommand(Enums.WORLD_EVENT_HEAL_RECEIVED, (repair, entity.id), building )


def workerBuildHandler(entity, world, buildingID):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    building = world.getEntityByID(buildingID)
    if building is None:
        return
    attr.set("Target", buildingID)
    attr.set("Task", "Build")
    attr.set("Status", "MovingSite")
    entity.getComponent(Enums.COMP_TYPE_FSM).setState("Building")
    path = world.findPath(entity.getPosition(), building.getPosition())
    entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER).setWaypoints(path)


def workerReturnHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set("Target", Enums.NULL_ID)
    attr.set("Task", "None")
    attr.set("Status", "MovingHome")
    attr.set("Repair amount", 0)
    entity.getComponent(Enums.COMP_TYPE_TIMER).removeTimer( "Repair timer" )
    entity.getComponent(Enums.COMP_TYPE_FSM).setState("Idle")
    path = world.findPath(entity.getPosition(), world.getBaseForTeamID(attr.get("Team")).getPosition())
    entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER).setWaypoints(path)


def workerIdleUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get("Task") == "Build":
        mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
        waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
        building = world.getEntityByID(attr.get("Target"))
        if building is None or building.getAttribute("Status") == "Idle":
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Return")
            return
        if mover.isMoving():
            if entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getDistanceSquaredToEntity(building) < 2.0:
                waypointMover.clearWaypoints()
                mover.stop()
                attr.set("Status", "Building")
                building.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Build")


def workerBuildingUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    building = world.getEntityByID(attr.get("Target"))
    if building is None or building.getAttribute("Status") == "Idle":
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Return")
        return
    if mover.isMoving():
        if entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getDistanceSquaredToEntity(building) < 2.0:
            waypointMover.clearWaypoints()
            mover.stop()
            attr.set("Status", "Building")
            building.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Build")


def workerRepairingUpdate(entity, world, args):
    attr = entity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    building = world.getEntityByID(attr.get("Target"))

    if building is None or attr.get( "Repair amount" ) == 0:
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Return")
        return
    if mover.isMoving():
        if entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getDistanceSquaredToEntity(building) < 2.0:
            waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
            waypointMover.clearWaypoints()
            mover.stop()
            attr.set("Status", "Building")
            timer = entity.getComponent( Enums.COMP_TYPE_TIMER )
            timer.addTimer( "Repair timer", "Repair tick", -1, attr.get( "Repair interval") )
