import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector, findFirstUnitWithinRadius


def beaverHeroAI(entity, world, args):
    """
    beaverHeroAI

    Custom AI behavior for the beaver hero

    Requires: Sensor, Effect, Timer, Mover, Attributes
    """
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")

    if status == "Idle":
        if attr.get("Target selected") is not Enums.NULL_ID:
            attr.set("Status", "Target")
        elif mover.isMoving():
            attr.set("Status", "Moving")
        else:
            physicals = sensor.queryPhysicals(
                "Attack",
                world,
                lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                          p.entity.getAttribute("Status") != "Dead" and
                          p.entity.hasAllOfTags(attr.get("Target tags")) and
                          p.entity.hasNoneOfTags(attr.get("Ignore tags")))
            if len(physicals) > 0:
                target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
                attr.setMultiple((
                    ("Status", "Combat"),
                    ("Target", target.id),
                ))
                if attr.get("Attack ready"):
                    entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
                if not timer.hasTimer("Combat timer"):
                    timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")

    elif status == "Moving":
        if not mover.isMoving():
            attr.set("Status", "Idle")

    elif status == "Target":
        target = world.getEntityByID(attr.get("Target selected"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
            attr.setMultiple((
                ("Status", "Idle"),
                ("Target selected", Enums.NULL_ID),
            ))
        elif sensor.intersectsEntity("Attack", target):
            mover.stop()
            attr.setMultiple((
                ("Status", "Combat"),
                ("Target", target.id),
            ))
            if attr.get("Attack ready"):
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        else:
            if not mover.hasDestination() or (mover.destination - target.getPosition()).magnitude_squared() > 1.0:
                mover.setDestination(target.getPosition())

    elif status == "Combat":
        target = world.getEntityByID(attr.get("Target"))
        if mover.isMoving():
            attr.setMultiple((
                ("Status", "Moving"),
                ("Target", Enums.NULL_ID),
            ))
        elif attr.get( "Target selected") != attr.get("Target" ) and attr.get( "Target selected" ) != Enums.NULL_ID:
            #make sure we change targets properly even in combat
            attr.set( "Status", "Idle" )
        elif target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
            attr.setMultiple((
                ("Status", "Idle"),
                ("Target", Enums.NULL_ID),
            ))
        else:
            return

    elif status == "Dead":
        pass

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    else:
        attr.set("Status", "Idle")


def beaverTargetHandler(entity, world, targetID):
    if targetID is Enums.NULL_ID:
        return
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    waypointMover.clearWaypoints()
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    target = world.getEntityByID(targetID)
    if target and target.getAttribute("Subtype") == "Amplifier pylon":
        attr.set("Target selected", targetID)
        if attr.get("Status") == "Combat":
            attr.set("Target", targetID)
    elif target and target.getAttribute("Team") is not attr.get("Team") and target.hasAllOfTags(attr.get("Target tags")) and target.hasNoneOfTags(attr.get("Ignore tags")):
        attr.set("Target selected", targetID)
        if attr.get("Status") == "Combat":
            attr.set("Target", targetID)


def beaverHeroAttackFirst( entity, world, args ):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        attr.set("Attack ready", False)
        attr.set("Attack victims", (Enums.NULL_ID,) )
        timer.addTimer("Attack start timer", "Attack", Enums.TIMER_ONCE, "Attack time", target.id)
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def beaverHeroAttackHandler( entity, world, args ):
    # casts the beaver hero initial bolt and sets up the successive bolts
    # beaver main bolt dmg: basedmg
    # beaver sub bolt dmg: int( basedmg / 4.0 ) * (debuff_count * 1.45)
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)

    extra_bolt_time = (attr.get("Attack period") - attr.get("Attack time")) / 4.0
    extra_bolt_time_dec = extra_bolt_time / 2.0

    # main bolt to primary target
    target = world.getEntityByID(attr.get("Target"))
    if target is None:
        attr.set("Target", Enums.NULL_ID)
        return
    if target.getAttribute("Subtype") == "Amplifier pylon":
        dmgInc = target.getAttribute("Damage increase")
        dmgType = attr.get("Damage type")
        pierceAmount = attr.get("Pierce amount")
        eventIO.receiveImmediateEvent("Damage inflict", world, (0, 0, dmgType, pierceAmount, target.id))
        world.createGameEntityForUser(
            "Beaver bolt",
            target.getPosition(),
            (target.getPosition() - entity.getPosition()).normalized(),
            world.getUserForUnit(entity),
            (
                ("Generation", 0),
                ("Amplified", True),
                ("TTL", attr.get("Attack extra bolts") + 1),
                ("Team", attr.get("Team")),
                ("Originator", entity.id),
                ("Source", entity.id),
                ("Target", target.id),
                ("Attack range", attr.get("Bolt range")),
                ("Damage minimum", attr.get("Damage minimum") + dmgInc),
                ("Damage maximum", attr.get("Damage maximum") + dmgInc),
                ("Victims", [target.id]),
            )
        )
    else:
        dmgMin = attr.get("Damage minimum")
        dmgMax = attr.get("Damage maximum")
        dmgType = attr.get("Damage type")
        pierceAmount = attr.get("Pierce amount")
        eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, target.id))
        world.createGameEntityForUser(
            "Beaver bolt",
            target.getPosition(),
            (target.getPosition() - entity.getPosition()).normalized(),
            world.getUserForUnit(entity),
            (
                ("Generation", 1),
                ("TTL", attr.get("Attack extra bolts") + 1),
                ("Team", attr.get("Team")),
                ("Originator", entity.id),
                ("Source", entity.id),
                ("Target", target.id),
                ("Attack range", attr.get("Bolt range")),
                ("Damage minimum", dmgMin),
                ("Damage maximum", dmgMax),
                ("Victims", [target.id]),
            )
        )


def beaverBoltLifetimeEnd(entity, world, args):
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    hero = world.getEntityByID(attr.get("Originator"))
    generation = attr.get("Generation")
    ttl = attr.get("TTL")
    if hero and (generation < ttl):
        heroAttr = hero.getAttributes()
        teamID = attr.get("Team")
        victims = attr.get("Victims")
        amplified = attr.get("Amplified")
        target = None
        if amplified:
            pylons = filter(lambda w: w.getAttribute("Subtype") == "Amplifier pylon" and w.id not in victims, world.getWards())
            if len(pylons) > 0:
                target = findClosestEntity(entity.getPosition(), pylons)
                if (target.getPosition() - entity.getPosition()).magnitude_squared() > attr.get("Attack range")**2:
                    target = None
            else:
                target = None
        if target is None:
            targetTags = heroAttr.get("Target tags")
            ignoreTags = heroAttr.get("Ignore tags")
            unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                                    e.hasAllOfTags(targetTags) and
                                    e.hasNoneOfTags(ignoreTags) and
                                    e.id not in victims)
            target = findFirstUnitWithinRadius(entity.getPosition(), attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))
        if target:
            victims.append(target.id)
            attr.set("Victims", victims)
            if target.getAttribute("Subtype") == "Amplifier pylon":
                dmgInc = target.getAttribute("Damage increase")
                eventIO.receiveImmediateEvent("Damage inflict", world, (0, 0, "Magical", 0.0, target.id))
                world.createGameEntityForUser(
                    "Beaver bolt",
                    target.getPosition(),
                    (target.getPosition() - entity.getPosition()).normalized(),
                    world.getUserForUnit(entity),
                    (
                        ("Generation", generation),
                        ("Amplified", True),
                        ("TTL", ttl),
                        ("Team", attr.get("Team")),
                        ("Originator", hero.id),
                        ("Source", attr.get("Target")),
                        ("Target", target.id),
                        ("Damage minimum", attr.get("Damage minimum") + dmgInc),
                        ("Damage maximum", attr.get("Damage maximum") + dmgInc),
                        ("Victims", list(victims)),
                    )
                )
            else:
                dmgMin = attr.get("Damage minimum") if amplified else attr.get("Damage minimum")*.5
                dmgMax = attr.get("Damage maximum") if amplified else attr.get("Damage maximum")*.5
                dmgType = attr.get("Damage type")
                pierceAmount = attr.get("Pierce amount")
                eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, target.id))
                world.createGameEntityForUser(
                    "Beaver bolt",
                    target.getPosition(),
                    (target.getPosition() - entity.getPosition()).normalized(),
                    world.getUserForUnit(entity),
                    (
                        ("Generation", generation + 1),
                        ("TTL", ttl),
                        ("Team", attr.get("Team")),
                        ("Originator", hero.id),
                        ("Source", attr.get("Target")),
                        ("Target", target.id),
                        ("Damage minimum", dmgMin),
                        ("Damage maximum", dmgMax),
                        ("Victims", list(victims)),
                    )
                )

    eventIO.receiveEvent("_destroy")


def beaverHeroExtraBolt(entity, world, (targetID, boltNumber)):
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    target = world.getEntityByID(targetID)

    if target is not None and not target.isDestroyed():
        if boltNumber == 0:
            # main bolt, do base damage
            dmg_mult = 1.0
            pass
        else:
            dmg_mult = 1.0 - (0.15 * boltNumber)
            pass

        if eventIO:
            dmgMin = attr.get("Damage minimum")*dmg_mult
            dmgMax = attr.get("Damage maximum")*dmg_mult
            dmgType = attr.get("Damage type")
            pierceAmount = attr.get("Pierce amount")
            eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, targetID))
            # TODO: run channeling fx


def beaverHeroBoltAttack(entity, world, (targetID, boltNumber)):
    attr = entity.getAttributes()
    target = world.getEntityByID(targetID)
    eventIO = target.getComponent(Enums.COMP_TYPE_EVENTIO)

    dmg_mult = 0.0

    if boltNumber == 0:
        # main bolt, do base damage
        dmg_mult = 1.0
        pass
    else:
        dmg_mult = 1.0 - (0.15 * boltNumber)
        pass

    if eventIO:
        dmgMin = attr.get("Damage minimum")
        dmgMax = attr.get("Damage maximum")
        dmgType = attr.get("Damage type")
        pierceAmount = attr.get("Pierce amount")
        eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, targetID))
        # TODO: run channeling fx


def amplifierPylonHandler(entity, world, pos):
    attr = entity.getAttributes()
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    user = world.getUserForUnit(entity)

    if status == "Casting Amplifier pylon":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Amplifier pylon", entity)

    hitpoints = attr.get("Abilities.Amplifier pylon.Hitpoints")
    lifetime = attr.get("Abilities.Amplifier pylon.Lifetime")
    dmgInc = attr.get("Abilities.Amplifier pylon.Damage increase")
    pylon = world.createGameEntityForUser(
        "Amplifier pylon",
        pos,
        Vector3(1, 0, 0),
        user,
        (
            ("Hitpoints", hitpoints),
            ("Hitpoints maximum", hitpoints),
            ("Lifetime", lifetime),
            ("Damage increase", dmgInc),
            ("Team", attr.get("Team")),
        )
    )
    pylonTimer = pylon.getComponent(Enums.COMP_TYPE_TIMER)
    pylonTimer.addTimer("Lifetime timer", "_destroy", 1, "Lifetime")
    world.networkCommand(Enums.WORLD_EVENT_ABILITY_USED, ("Amplifier pylon", 0.0, -1, pos), entity)


def beaverCharge(entity, world, (direction, power)):
    attr = entity.getAttributes()
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    cost = attr.get(("Abilities", "Charge", "Cost"))
    mana = attr.get("Mana")

    if status is not "Dead" and attr.get("Abilities.Charge.Ready") and cost <= mana:
        if status == "Casting Charge":
            attr.set("Status", "Idle")
            fsm.setState("Idle")
            world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Charge", entity)

        attr.inc("Mana", -cost)
        attr.set(("Abilities", "Charge", "Ready"), False)

        mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
        if mover.isMoving():
            mover.stop()

        timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

        bolts = attr.get(("Abilities", "Charge", "Bolts"))
        ability_range = attr.get(("Abilities", "Charge", "Range")) * power
        castdelay = attr.get(("Abilities", "Charge", "Time"))

        single_bolt_delay = attr.get(("Abilities", "Charge", "Bolt delay"))
        single_bolt_dist = ability_range / bolts


        bolt_delay = 0.0
        bolt_dist = single_bolt_dist
        for i in xrange(0, bolts):
            timer.addAnonymousTimer("Charge single bolt", Enums.TIMER_ONCE, castdelay + bolt_delay, entity.getPosition() + (direction * bolt_dist))
            bolt_delay += single_bolt_delay
            bolt_dist += single_bolt_dist
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, attr.get(("Abilities", "Charge", "Cooldown")))

        world.networkAbilityImmediateSuccess( "Charge", entity )
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Charge", single_bolt_delay * bolts, -1, Vector3( 0, 0, 0 ) ), entity )


def beaverChargeSingleBolt(entity, world, position):
    attr = entity.getAttributes()
    dmgMin = attr.get("Abilities.Charge.Damage minimum")
    dmgMax = attr.get("Abilities.Charge.Damage maximum")

    #caster_int = attr.get(("Stats", "Intelligence"))

    # each point of intelligence adds 10% of base damage up to 100% increase
    #caster_int = min(caster_int, 10)
    #basedmg += (caster_int * 0.10) * basedmg

    # fudge the values a bit for a decent range
    #min_dmg = int(basedmg * 0.95)
    #max_dmg = basedmg

    bolt = world.createGameEntity("Lightning strike", position, Vector3(1, 0, 0), (
        ("Team", attr.get("Team")),
        ("Radius", attr.get(("Abilities", "Charge", "Bolt damage radius"))),
        ("Damage minimum", dmgMin),
        ("Damage maximum", dmgMax),
        ("Originator", entity.id)
    ))
    bolt.getComponent(Enums.COMP_TYPE_TIMER).addAnonymousTimer("Lightning damage", Enums.TIMER_ONCE, bolt.getAttribute("Lifetime"), None)


def beaverChargeBoltDamage(entity, world, args):
    # deal damage in despawn to give victims a bit more time to get out of the way
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)

    dmgMin = attr.get("Damage minimum")
    dmgMax = attr.get("Damage maximum")
    dmgType = attr.get("Damage type")
    pierceAmount = attr.get("Pierce amount")

    victims = sensor.queryPhysicals(
        "Area",
        world,
        lambda p: p.entity.getAttribute("Status") != "Dead" and p.entity.getAttribute("Team") != attr.get("Team") and
                  p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")))

    victims = map(lambda p: p.entity, victims)

    if len(victims) > 0:
        for v in victims:
            eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, v.id))

    eventIO.receiveEvent("_destroy")


def healWardAbilityHandler(entity, world, pos):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if status == "Casting Healing ward":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Healing ward", entity)

    duration = attr.get( ("Abilities", "Healing ward", "Duration" ))
    tick_interval = attr.get( ("Abilities", "Healing ward", "Tick interval" ) )
    ward_ticks = duration / tick_interval
    ward = world.createGameEntity( "Healing ward", pos, Vector3( 1,0,0),
        (
            ("Team", attr.get("Team")),
            ("Ticks left", ward_ticks),
            ("Heal per tick", attr.get( ("Abilities", "Healing ward", "Heal per tick") )),
            ("Duration", duration),
            ("Tick interval", tick_interval),
            ("Originator", entity.id),
            ("Heal radius", attr.get( ("Abilities", "Healing ward", "Range") ))
        ))
    # wards have a built-in despawn timer, but it needs to be primed properly
    timer_comp = ward.getComponent( Enums.COMP_TYPE_TIMER )
    timer = timer_comp.getTimer( "Healing tick timer" )
    timer[Enums.TIMER_TRIGGER_LIMIT] = ward_ticks
    timer_comp.addTimer( timer[Enums.TIMER_NAME], timer[Enums.TIMER_EVENT],
                         timer[Enums.TIMER_TRIGGER_LIMIT], timer[Enums.TIMER_COUNTDOWN_START], timer[Enums.TIMER_DATA] )
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Healing ward", 0.0, -1, pos), entity )


def healingWardTickHandler( entity, world, pos ):
    attr = entity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    sensor = entity.getComponent( Enums.COMP_TYPE_SENSOR )
    eventIO = entity.getComponent( Enums.COMP_TYPE_EVENTIO )
    physicals = sensor.queryPhysicals(
        "Sight",
        world,
        lambda p: p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")) and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.getAttribute("Hitpoints") < p.entity.getAttribute("Hitpoints maximum") and
                  p.entity.getAttribute("Team") is attr.get("Team") )
    if len(physicals) > 0:
        single_heal = attr.get( "Heal per tick") / len(physicals)
        for p in physicals:
            eventIO.sendEvent(p.entity, "Heal", (single_heal, entity.id))
    ticksleft = attr.get("Ticks left")
    ticksleft -= 1
    attr.set("Ticks left", ticksleft)
    if ticksleft == 0:
        eventIO.receiveEvent("Death", None)


def damageShieldEnd(entity, world, args):
    attr = entity.getAttributes()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)

    if not tags.has("Damage shielded"):
        return

    timer.removeTimer("Damage shield timer")
    tags.remove("Damage shielded")
    damageAbsorbed = attr.get("Abilities.Damage shield.Damage absorbed")
    damageFactor = attr.get("Abilities.Damage shield.Damage factor")
    damageRadius = attr.get("Abilities.Damage shield.Damage radius")
    dmg = damageAbsorbed*damageFactor
    dmgType = attr.get("Abilities.Damage shield.Damage type")
    pierceAmount = attr.get("Abilities.Damage shield.Pierce amount")
    attr.set("Abilities.Damage shield.Damage absorbed", 0)

    enemies = world.getEnemyUnitsForTeam(attr.get("Team"))
    pos = entity.getPosition()
    for e in enemies:
        epos = e.getPosition()
        esize = e.getSize()
        if (epos - pos).magnitude_squared() <= (damageRadius + esize)**2:
            eventIO.receiveEvent("Damage inflict", (dmg, dmg, dmgType, pierceAmount, e.id))
    world.networkCommand(Enums.WORLD_EVENT_ABILITY_ENDED, "Damage shield", entity)


def damageShieldTickHandler( entity, world, args ):
    attr = entity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    mana_per_tick = entity.getAttribute( ("Abilities", "Damage shield", "Mana cost per tick") )
    mana = entity.getAttribute( "Mana" )
    if mana < mana_per_tick:
        entity.getComponent( Enums.COMP_TYPE_EVENTIO ).receiveEvent( "Damage shield expire" )
    else:
        attr.inc( "Mana", -mana_per_tick )


def damageShieldAbilityHandler(entity, world, args):
    attr = entity.getAttributes()
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    if status == "Casting Damage shield":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Damage shield", entity)

    duration = attr.get("Abilities.Damage shield.Duration")
    tags.add("Damage shielded")
    timer.addTimer("Damage shield timer", "Damage shield end", Enums.TIMER_ONCE, duration)
    world.networkCommand(Enums.WORLD_EVENT_ABILITY_USED, ("Damage shield", duration, entity.id, Vector3(0, 0, 0)), entity)


def beaverChargeUpgradeHandler( entity, world, args ):
    pass


def healingWardUpgradeHandler( entity, world, args ):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Healing ward", "Level"), 1)
    attr.inc(("Abilities", "Healing ward", "Cooldown"), -1)
    attr.inc(("Abilities", "Healing ward", "Heal per tick"), 5)
    attr.inc(("Abilities", "Healing ward", "Duration"), 2)
    attr.inc(("Abilities", "Healing ward", "Range"), 0.5)


def damageShieldUpgradeHandler( entity, world, args ):
    pass
