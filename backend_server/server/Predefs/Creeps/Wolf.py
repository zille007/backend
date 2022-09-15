import Enums
import random
from euclid import Vector3

def wolfIdleUpdate(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    hero = world.getEntityByID(attr.get("Originator"))

    if hero and hero.getAttribute("Status") != "Dead":
        pos = entity.getPosition()
        heroPos = hero.getPosition()
        enemies = world.iterateEnemyCreepsAndHeroesForTeam(attr.get("Team"))
        aggroRange = attr.get("Aggro range")
        for e in enemies:
            epos = e.getPosition()
            esize = e.getSize()
            if (epos - heroPos).magnitude_squared() <= (aggroRange + esize)**2:
                attr.set("Target", e.id)
                attackRange = attr.get("Attack range")
                if (epos - pos).magnitude_squared() <= (attackRange + esize)**2:
                    mover.stop()
                    attr.set("Status", "Combat")
                    fsm.setState("Combat")
                    if attr.get("Attack ready"):
                        eventIO.receiveEvent("Attack first")
                    if not timer.hasTimer("Combat timer"):
                        timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
                else:
                    mover.setDestination(epos)
                    attr.set("Status", "Moving")
                    fsm.setState("Moving")
                return
        heroDir = hero.getDirection()
        dest = heroPos + heroDir*2.5 + attr.get("Offset")
        if (dest - pos).magnitude_squared() > .25:
            mover.setDestination(dest)
            attr.set("Status", "Moving")
            fsm.setState("Moving")
    else:
        pos = entity.getPosition()
        enemies = world.iterateEnemyCreepsAndHeroesForTeam(attr.get("Team"))
        aggroRange = attr.get("Aggro range")
        for e in enemies:
            epos = e.getPosition()
            esize = e.getSize()
            if (epos - pos).magnitude_squared() <= (aggroRange + esize)**2:
                attr.set("Target", e.id)
                attackRange = attr.get("Attack range")
                if (epos - pos).magnitude_squared() <= (attackRange + esize)**2:
                    mover.stop()
                    attr.set("Status", "Combat")
                    fsm.setState("Combat")
                    if attr.get("Attack ready"):
                        eventIO.receiveEvent("Attack first")
                    if not timer.hasTimer("Combat timer"):
                        timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
                else:
                    mover.setDestination(epos)
                    attr.set("Status", "Moving")
                    fsm.setState("Moving")


def wolfMovingUpdate(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    hero = world.getEntityByID(attr.get("Originator"))
    target = world.getEntityByID(attr.get("Target"))

    if hero and hero.getAttribute("Status") != "Dead":
        if target and not target.isDestroyed() and target.getAttribute("Status") != "Dead":
            tpos = target.getPosition()
            tsize = target.getSize()
            pos = entity.getPosition()
            attackRange = attr.get("Attack range")
            if (tpos - pos).magnitude_squared() <= (tsize + attackRange)**2:
                mover.stop()
                attr.set("Status", "Combat")
                fsm.setState("Combat")
                if attr.get("Attack ready"):
                    eventIO.receiveEvent("Attack first")
                if not timer.hasTimer("Combat timer"):
                    timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            else:
                mover.setDestination(tpos)
            return
        elif mover.hasDestination():
            heroPos = hero.getPosition()
            if (heroPos - mover.destination).magnitude_squared() > 4**2:
                heroDir = hero.getDirection()
                mover.setDestination(heroPos + heroDir*2.5 + attr.get("Offset"))
        else:
            attr.set("Status", "Idle")
            fsm.setState("Idle")
        attr.set("Target", Enums.NULL_ID)
    elif target and not target.isDestroyed() and target.getAttribute("Status") != "Dead":
        tpos = target.getPosition()
        tsize = target.getSize()
        pos = entity.getPosition()
        attackRange = attr.get("Attack range")
        if (tpos - pos).magnitude_squared() <= (tsize + attackRange)**2:
            mover.stop()
            attr.set("Status", "Combat")
            fsm.setState("Combat")
            if attr.get("Attack ready"):
                eventIO.receiveEvent("Attack first")
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        else:
            mover.setDestination(tpos)
    else:
        pos = entity.getPosition()
        enemies = world.iterateEnemyCreepsAndHeroesForTeam(attr.get("Team"))
        aggroRange = attr.get("Aggro range")
        for e in enemies:
            epos = e.getPosition()
            esize = e.getSize()
            if (epos - pos).magnitude_squared() <= (aggroRange + esize)**2:
                attr.set("Target", e.id)
                attackRange = attr.get("Attack range")
                if (epos - pos).magnitude_squared() <= (attackRange + esize)**2:
                    mover.stop()
                    attr.set("Status", "Combat")
                    fsm.setState("Combat")
                    if attr.get("Attack ready"):
                        eventIO.receiveEvent("Attack first")
                    if not timer.hasTimer("Combat timer"):
                        timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
                else:
                    mover.setDestination(epos)
                    attr.set("Status", "Moving")
                    fsm.setState("Moving")


def wolfCombatUpdate(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)

    hero = world.getEntityByID(attr.get("Originator"))
    target = world.getEntityByID(attr.get("Target"))

    heroPos = hero.getPosition()
    heroDir = hero.getDirection()
    pos = entity.getPosition()
    attackRange = attr.get("Attack range")
    aggroRange = attr.get("Aggro range")
    if target:
        tpos = target.getPosition()
        tsize = target.getSize()
    else:
        tpos = None
        tsize = None

    if (heroPos - pos).magnitude_squared() > aggroRange**2:
        attr.set("Target", Enums.NULL_ID)
        attr.set("Status", "Moving")
        fsm.setState("Moving")
        mover.setDestination(heroPos + heroDir*2.5 + attr.get("Offset"))
    elif not target or target.isDestroyed() or target.getAttribute("Status") == "Dead" or (tpos - pos).magnitude_squared() > (tsize + attackRange)**2:
        enemies = world.iterateEnemyCreepsAndHeroesForTeam(attr.get("Team"))
        for e in enemies:
            epos = e.getPosition()
            esize = e.getSize()
            if (epos - pos).magnitude_squared() <= (aggroRange + esize)**2:
                attr.set("Target", e.id)
                if (epos - pos).magnitude_squared() <= (attackRange + esize)**2:
                    mover.stop()
                    attr.set("Status", "Combat")
                    fsm.setState("Combat")
                    if attr.get("Attack ready"):
                        eventIO.receiveEvent("Attack first")
                    if not timer.hasTimer("Combat timer"):
                        timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
                else:
                    mover.setDestination(epos)
                    attr.set("Status", "Moving")
                    fsm.setState("Moving")
                return
        attr.set("Target", Enums.NULL_ID)
        attr.set("Status", "Moving")
        fsm.setState("Moving")
        mover.setDestination(heroPos + heroDir*2.5 + attr.get("Offset"))



def celestialWolfExplodeCheck(entity, world):
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)

    pos = entity.getPosition()

    hero = world.getEntityByID(attr.get("Originator"))
    enemies = world.getEnemyUnitsForTeam(attr.get("Team"))

    radius = attr.get( "Damage radius" )
    didExplode = False
    willExplode = False

    targeted = []

    for e in enemies:
        epos = e.getPosition()
        esize = e.getSize()
        if (epos - pos).magnitude_squared() <= (radius + esize)**2:
            if e.hasTag( "Hero" ) or e.hasTag( "Creep" ):
                willExplode = True

    if willExplode:
        targeted = []
        candidates = world.getUnitsForTeam( 1 ) + world.getUnitsForTeam( 2 )
        for t in candidates:
            epos = t.getPosition()
            esize = t.getSize()
            if (epos - pos).magnitude_squared() <= (radius + esize)**2:
                if t.hasTag( "Hero" ) or t.hasTag( "Creep" ):
                    targeted.append( t )

        didExplode = True
        dmgMin = attr.get( "Explode damage minimum" )
        dmgMax = attr.get( "Explode damage maximum" )
        dmg = random.randint( dmgMin, dmgMax )
        dmg /= len(targeted)
        dmgType = "Melee"
        pierceAmount = 0.25
        for dmg_e in targeted:
            # dmg_attr = dmg_e.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
            world.logInfo( "Will explode %s with radius %4.2f dealing %d damage (min %d max %d) to entity %s" % (entity.getName(), radius, dmg, dmgMin, dmgMax, dmg_e.getName()))
            eventIO.receiveEvent("Damage inflict", (dmg, dmg, dmgType, pierceAmount, dmg_e.id))

    if didExplode:
        timer = entity.getComponent( Enums.COMP_TYPE_TIMER )
        fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
        fsm.setState( "Exploded" )
        attr.set( "Status", "Exploded" )
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Explode", 0, entity.id, Vector3( 0, 0, 0 )), entity )
        timer.addAnonymousTimer( "Death", Enums.TIMER_ONCE, 0 )


def celestialWolfIdleUpdate(entity, world, args):
    wolfIdleUpdate( entity, world, args )
    #celestialWolfExplodeCheck(entity, world)

def celestialWolfMovingUpdate(entity, world, args):
    wolfMovingUpdate( entity, world, args )
    #celestialWolfExplodeCheck(entity, world)

def celestialWolfCombatUpdate(entity, world, args):
    #wolfCombatUpdate( entity, world, args )
    celestialWolfExplodeCheck(entity, world)

