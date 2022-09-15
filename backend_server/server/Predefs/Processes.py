import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector
from Intersection import circleToCircle


def matchProcess(entity, world, args):
    """
    matchProcess
    """
    pass



def teamProcess(entity, world, args):
    """
    teamProcess
    """
    # prevent multiple signaling of winning team

    m_attr = world.getMatchEntity().getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    if m_attr.get( "Winner" ) != -1:
        return

    attr = entity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    tix = attr.get( ("Resources", "Tickets") )
    if tix <= 0 and attr.get( "Status" ) == "Active":
        attr.set( ("Resources", "Tickets"), 0 )
        # TODO: this will fail for multiple teams as we automatically assume that the
        # team that currently holds the maximum amount of victory points is
        # the winner. Additional teams that can be eliminated will require extra
        # effort on client side anyway, so go with this for now.
        world.logInfo( "Team %d ran out of tickets; signaling end of game." % (entity.getAttribute( "Team" ), ) )
        world.networkCommand(Enums.WORLD_EVENT_TEAM_ELIMINATED, attr.get( "Team" ) )
        attr.set( "Status", "Eliminated" )


def userProcess(entity, world, args):
    """
    userProcess
    """
    pass


def vpProcess(entity, world, args):
    """
    vpProcess
    """
    attr = entity.getAttributes()
    unitFilter = (lambda e: circleToCircle(e.getPosition(), e.getSize(), entity.getPosition(), attr.get("Capture range")) and
                            not e.hasTag("No capture") and
                            e.getAttribute("Team") is not 0)
    units = filter(unitFilter, world.getHeroes() + world.getCreeps())

    if len(units) is 0:
        if attr.get("Status") != "Idle":
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
                for u in units:
                    if u.hasTag( "Hero" ):
                        u_attr = u.getAttributes()
                        # trigger capturing procs
                        eio = u.getComponent( Enums.COMP_TYPE_EVENTIO )
                        if eio:
                            eio.receiveEvent( "Capture", "Victory point" )
                        world.getMatch().playerStatIncEvent( "captures", u_attr.get("Username"), 1 )
                team = units[0].getAttribute("Team")
                attr.set("Team", team)
                attr.set("Capture counter", attr.get("Capture time"))

                teams = world.getTeamEntities()
                for t in teams:
                    teamAttr = t.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                    teamAttr.set("Resources.Victory points captured", len(world.getVictoryPointsForTeamID(t.getAttribute("Team"))))

                slotFilter = (lambda e: circleToCircle(e.getPosition(), e.getSize(), entity.getPosition(), attr.get("Build range")) and
                                        e.getAttribute("Neutral"))
                slots = filter(slotFilter, world.getBuildingSlots())
                for s in slots:
                    s.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Team", team)



def updateTickets( entity, world, args ):
    teams = world.getTeamEntities()
    match = world.getMatchEntity()
    maxVP = 0
    teamWithMaxVP = 0
    for t in teams:
        vps = world.getVictoryPointsForTeamID(t.getAttribute("Team"))
        if len(vps) > maxVP:
            maxVP = len(vps)
            teamWithMaxVP = t.getAttribute("Team")
    if teamWithMaxVP is 0:
        return

    activeTeams = []
    ticket_defecit_per_vp = match.getComponent( Enums.COMP_TYPE_ATTRIBUTES ).get( "VP defecit ticket loss")
    for t in teams:
        tix = t.getComponent( Enums.COMP_TYPE_ATTRIBUTES ).get( ("Resources", "Tickets") )
        mintix = t.getComponent( Enums.COMP_TYPE_ATTRIBUTES ).get( ("Resources", "Tickets minimum") )
        loseTickets = (maxVP - len(world.getVictoryPointsForTeamID(t.getAttribute("Team"))) * ticket_defecit_per_vp)

        if tix > 0 and t.getAttribute( "Team") not in (Enums.MATCH_TEAM_OBSERVER, Enums.MATCH_TEAM_ADMIN, Enums.MATCH_TEAM_NULL):
            activeTeams.append(t.getAttribute( "Team" ))

        if t.getAttribute("Team") is teamWithMaxVP:
            continue
        if loseTickets <= 0:
            continue
        if tix > mintix:
            tix = max( 0, tix - loseTickets )
            t.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set(("Resources", "Tickets"), int(tix) )

    m_attr = match.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    if m_attr.get( "Winner" ) != -1:
        return

    if len(activeTeams) == 1:
        # just a single active team left, obviously the winner
        world.networkCommand(Enums.WORLD_EVENT_END_GAME_WITH_WINNER, activeTeams[0] )
        m_attr.set( "Winner", activeTeams[0] )

    if len(activeTeams) == 0:
        # no active teams left, an odd draw by tickets (but possible, if both teams run out of tickets on the same frame)
        world.networkCommand(Enums.WORLD_EVENT_END_GAME_WITH_WINNER, Enums.MATCH_TEAM_NULL)
        m_attr.set( "Winner", Enums.MATCH_TEAM_NULL )


def bulletAI(entity, world, args):
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    physicals = sensor.queryPhysicals(
        "Damage",
        world,
        lambda p: p.entity.hasTag("Targetable") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.getAttribute("Team") is not attr.get("Team"))
    targets = map(lambda p: p.entity, physicals)
    victims = entity.getAttribute(("Victims"))
    targets = [t for t in targets if t not in victims]
    for t in targets:
        victims.append(t)
    entity.getComponent(Enums.COMP_TYPE_EFFECT).launchEffect("Charge", world, targets)
    pass


def mineAI(entity, world, args):
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)


    attr.set("Speed", attr.get("Speed") - float(0.1))

    physicals = sensor.queryPhysicals(
        "Damage",
        world,
        lambda p: p.entity.hasTag("Targetable") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.getAttribute("Team") is not attr.get("Team"))
    targets = map(lambda p: p.entity, physicals)
    victims = entity.getAttribute(("Victims"))
    targets = [t for t in targets if t not in victims]
    for t in targets:
        victims.append(t)

    entity.getComponent(Enums.COMP_TYPE_EFFECT).launchEffect("Charge", world, targets)
    pass


def healingTotemAI(entity, world, args):
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)


    attr.set("Speed", attr.get("Speed") - float(0.1))

    physicals = sensor.queryPhysicals(
        "Damage",
        world,
        lambda p: p.entity.hasTag("Targetable") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.getAttribute("Team") is not attr.get("Team"))
    targets = map(lambda p: p.entity, physicals)
    victims = entity.getAttribute(("Victims"))
    targets = [t for t in targets if t not in victims]
    for t in targets:
        victims.append(t)

    entity.getComponent(Enums.COMP_TYPE_EFFECT).launchEffect("Charge", world, targets)
    pass
