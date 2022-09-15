import Enums
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector
from Intersection import circleToCircle


def goldmineProcess(entity, world, args):
    """
    goldmineProcess
    """
    attr = entity.getAttributes()

    unitFilter = (lambda e: circleToCircle(e.getPosition(), e.getSize(), entity.getPosition(), attr.get("Capture range")) and
                            not e.hasTag("No capture") and
                            e.getAttribute("Team") is not 0)
    units = filter(unitFilter, world.getHeroes() + world.getCreeps())

    if len(units) is 0:
        if attr.get("Status") != "Idle" and attr.get( "Status") != "Upgrading":
            attr.set("Status", "Idle")
        if attr.get("Capture counter") < attr.get("Capture time"):
            attr.inc("Capture counter", 1)
    else:
        if areOnSameTeam(units):
            if units[0].getAttribute("Team") is attr.get("Team"):
                return

            teamAttr = world.getTeamEntity( units[0].getAttribute( "Team" ) )
            if teamAttr.getAttribute( "Control toggles.Can capture") == False:
                return

            attr.inc("Capture counter", -1)
            if attr.get("Capture counter") <= 0:
                newTeamID = units[0].getAttribute("Team")
                world.changeTeamForUnit(entity, newTeamID)
                attr.set("Capture counter", attr.get("Capture time"))
                for u in units:
                    if u.hasTag( "Hero" ):
                        u_attr = u.getAttributes()
                        world.getMatch().playerStatIncEvent( "captures", attr.get("Username"), 1 )
                        eio = u.getComponent( Enums.COMP_TYPE_EVENTIO )
                        if eio:
                            eio.receiveEvent( "Capture", "Goldmine" )



def generateGold(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")

    # no gold generation on neutral mines
    if attr.get("Team") == 0:
        return

    # no gold generation if upgrading or frozen
    if status == "Upgrading" or status == "Freeze":
        return

    gold = attr.get("Gold")
    amt = attr.get("Generation amount")
    goldmax = attr.get("Gold maximum")

    newgold = min(gold + amt, goldmax)
    if newgold != gold:
        attr.set("Gold", newgold)


def goldCollectionHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    gold = attr.get("Gold")
    minimum = attr.get("Collect minimum")
    if gold >= minimum and status != "Freeze":
        attr.set("Gold", 0)
        teamEntity = world.getTeamEntity(attr.get("Team"))
        teamAttributes = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        teamAttributes.inc(("Resources", "Gold"), gold)


def upgradeGoldmine(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    base = world.getBaseForTeamID(attr.get("Team"))
    if base is None:
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    baseLevel = base.getAttribute(("Stats", "Level"))
    maxLevel = min(baseLevel + 1, maxLevel)
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    attr.inc(("Stats", "Level"), 1)
    attr.inc("Gold maximum", teamAttr.get(("Units", "None", "Goldmine", "Gold maximum increase")))
    attr.inc("Generation interval", -teamAttr.get(("Units", "None", "Goldmine", "Generation interval decrease")))
    attr.inc("Hitpoints", 100)
    attr.inc("Hitpoints maximum", 100)

    attr.set("Status", "Idle")

    world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADED, None, entity)
