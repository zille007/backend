import Enums
import random


def procOnAttack(entity, world, args):
    attr = entity.getAttributes()
    level = attr.get("Stats.Level")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    procs = attr.get("Procs.On attack")
    for p in procs:
        rnd = random.random()
        if procs is not None and len(procs) > 0:
            #world.logInfo( "On attack proc on %s: rolled %4.2f needed %4.2f" % (entity.getName(), rnd, p[1]))
            pass
        if level >= p[0] and rnd < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, None))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On attack", p[2], p[3], None), entity)


def procOnLastHit(entity, world, targetMaxHP):
    attr = entity.getAttributes()
    level = attr.get("Stats.Level")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    procs = attr.get("Procs.On last hit")
    for p in procs:
        rnd = random.random()
        if procs is not None and len(procs) > 0:
            #world.logInfo( "On last hit proc on %s: rolled %4.2f needed %4.2f maxhp %d" % (entity.getName(), rnd, p[1], targetMaxHP))
            pass
        if level >= p[0] and random.random() < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, targetMaxHP))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On last hit", p[2], p[3], targetMaxHP), entity)


def procOnMove(entity, world, args):
    attr = entity.getAttributes()
    level = attr.get("Stats.Level")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    procs = attr.get("Procs.On move")
    for p in procs:
        if level >= p[0] and random.random() < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, None))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On move", p[2], p[3], None), entity)


def procOnDamage(entity, world, (dmg, pierceAmount, origID, origCreatID)):
    attr = entity.getAttributes()
    level = attr.get("Stats.Level")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    procs = attr.get("Procs.On damage")
    for p in procs:
        if level >= p[0] and random.random() < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, dmg))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On damage", p[2], p[3], dmg), entity)


def procOnDeath(entity, world, args):
    attr = entity.getAttributes()
    level = attr.get("Stats.Level")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    procs = attr.get("Procs.On death")
    for p in procs:
        if level >= p[0] and random.random() < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, None))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On death", p[2], p[3], None), entity)


def procOnHeal(entity, world, args):
    return
    #attr = entity.getAttributes()
    #level = attr.get("Stats.Level")
    #eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    #procs = attr.get("Procs.On heal")
    #for p in procs:
    #    if level >= p[0] and random.random() < p[1]:
    #        eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, heal))
    #        world.networkCommand(Enums.WORLD_EVENT_PROC, ("On heal", p[2], p[3], heal), entity)


def procOnAbility(entity, world, (name, pos, targetID)):
    attr = entity.getAttributes()
    level = attr.get("Stats.Level")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    procs = attr.get("Procs.On ability")
    for p in procs:
        #world.logInfo( "On ability proc on %s req level %d chance %4.2f (proc def is %s)" % (entity.getName(),p[0],p[1], str(p) ))
        if level >= p[0] and random.random() < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, name))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On ability", p[2], p[3], name), entity)


def procOnBuff(entity, world, (attribute, modValue, modType, effectType, time)):
    attr = entity.getAttributes()
    level = attr.get("Stats.Level")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    procs = attr.get("Procs.On buff")
    for p in procs:
        if level >= p[0] and random.random() < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, None))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On buff", p[2], p[3], None), entity)


def procOnCapture(entity, world, args):
    #world.logInfo( "Capture proc on %s" % (entity.getName(),))
    attr = entity.getAttributes()
    level = attr.get( "Stats.Level" )
    eventIO = entity.getComponent( Enums.COMP_TYPE_EVENTIO )
    procs = attr.get("Procs.On capture")
    for p in procs:
        if level >= p[0] and random.random() < p[1]:
            eventIO.receiveImmediateEvent(p[2], world, (p[3] if len(p) > 2 else None, None))
            world.networkCommand(Enums.WORLD_EVENT_PROC, ("On capture", p[2], p[3], None), entity)


###
# Proc effect handlers
#
# Parameters:
# The first one, whatever it may be, is always the set of values read from db.
# The second one is whatever the proc event passes on to the effect.
###


def damageTokenHandler(entity, world, (multiplier, args)):
    #world.logInfo( "Damage proc effect on %s" % (entity.getName(),))
    attr = entity.getAttributes()
    if multiplier is None:
        multiplier = 2
    tokens = attr.get("Damage tokens")
    tokens.append(multiplier)
    attr.set("Damage tokens", tokens)


def abilityCostlessHandler(entity, world, (args, abilityName)):
    #world.logInfo( "No ability cost proc effect on %s" % (entity.getName(),))
    attr = entity.getAttributes()
    attr.set("Abilities." + abilityName + ".Costless", True)


def armorBoostHandler(entity, world, ((armorBoost, time), args)):
    #world.logInfo( "Armor boost proc effect on %s" % (entity.getName(),))
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    eventIO.receiveEvent("Buff", ("Stats.Armor", armorBoost, Enums.ATTR_INC, "Temporary", time))


def recoverManaHandler(entity, world, (percentage, args)):
    world.logInfo( "Mana recovery proc effect on %s" % (entity.getName(),))
    maxmana = float( entity.getAttribute( "Mana maximum" ) )
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    eventIO.receiveEvent("Mana", maxmana * percentage )


def recoverHealthHandler(entity, world, (percentage, args)):
    maxhp = float( entity.getAttribute( "Hitpoints maximum" ) )
    #world.logInfo( "Health recovery proc effect on %s percentage %4.2f result %4.2f" % (entity.getName(), percentage, maxhp*percentage))
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    eventIO.receiveEvent("Heal", (maxhp * percentage, entity.id) )


def speedBoostHandler(entity, world, (percentage, args)):
    duration = 3.0
    world.logInfo( "Speed boost proc effect on %s with percentage %4.2f time %4.2f" % (entity.getName(), percentage, duration))
    eventIO = entity.getComponent( Enums.COMP_TYPE_EVENTIO )
    eventIO.receiveEvent("Buff", ("Speed", percentage, Enums.ATTR_MUL, "Temporary", duration))