import Enums
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector


def bearChargeAttack(entity, world, targets):
    if targets is None:
        return

    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    if isinstance(targets, list):
        for t in targets:
            if attributes and eventIO:
                damage = attributes.get(("Abilities", "Charge", "Damage"))
                target = t
                eventIO.sendEvent(target, "Damage", (damage, "Melee", 0.0, entity.id))
        return
    else:
        if attributes and eventIO:
            damage = attributes.get(("Abilities", "Charge", "Damage"))
            target = targets
            eventIO.sendEvent(target, "Damage", (damage, "Melee", 0.0, entity.id))


def bearCharge(entity, world, (dir, power)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    status = attr.get("Status")
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat" and status != "Casting Charge":
        return
    if status == "Casting Charge":
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Charge", entity)
    dir = dir.normalized()
    cost = attr.get(("Abilities", "Charge", "Cost"))
    mana = attr.get("Mana")
    if attr.get("Status") is not "Dead" and attr.get(("Abilities", "Charge", "Ready")) and cost <= mana:
        fsm.setState("Charge")
        attr.set("Status", "Charge")
        attr.set("Target selected", Enums.NULL_ID)
        attr.set(("Abilities", "Charge", "Ready"), False)
        attr.inc("Mana", -cost)
        speedIncrease = attr.get(("Abilities", "Charge", "Speed increase"))*power
        token = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES).addModifier("Speed", speedIncrease, Enums.MOD_TYPE_ADD)
        time = attr.get( ("Abilities", "Charge", "Time") )
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge timer", "Charge end", Enums.TIMER_ONCE, time, token)
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        entity.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(dir)

        world.networkAbilityImmediateSuccess( "Charge", entity )
        #world.networkCommand(Enums.WORLD_EVENT_TIMED_CHARGE, time, entity)
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Charge", time, -1, Vector3( 0, 0, 0 ) ), entity )


def bearChargeUpdate(entity, world, args):
    attr = entity.getAttributes()
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    physicals = sensor.queryPhysicals(
        "Charge",
        world,
        lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.hasTag("Targetable") and not p.entity.hasTag( "Ethereal") )   # cannot charge against ethereal things; e.g. amplifier pylons
    targets = map(lambda p: p.entity, physicals)
    victims = attr.get(("Abilities", "Charge", "Victims"))
    targets = [t for t in targets if t not in victims]
    if len(targets) is 0:
        return
    stun_time = attr.get(("Abilities", "Charge", "Stun time"))
    dmgMin = attr.get(("Abilities", "Charge", "Damage minimum"))
    dmgMax = attr.get(("Abilities", "Charge", "Damage maximum"))
    dmgType = attr.get(("Abilities", "Charge", "Damage type"))
    pierceAmt = attr.get(("Abilities", "Charge", "Pierce amount"))
    for t in targets:
        victims.append(t)
        t.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Stun", stun_time)
        eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmt, t.id))

    # if targets found, end charge immediately; we need the charge speed increase token from the timer first
    t = timer.getTimer("Charge timer")

    if t:
        eventIO.receiveEvent("Charge end", t[Enums.TIMER_DATA])
        timer.removeTimer("Charge timer")
        for t in targets:
            if t.hasTag("Hero"):
                eventIO.receiveEvent("Target", t.id)
                return
        if len(targets) > 0:
            eventIO.receiveEvent("Target", targets[0].id)


def heroHealReady( entity, world, args ):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set(("Abilities", "Hero heal", "Ready"), True)


def heroHealTickHandler( entity, world, heal_amount ):
    eventIO = entity.getComponent( Enums.COMP_TYPE_EVENTIO )
    eventIO.receiveEvent( "Heal", (heal_amount, entity.id))
    # TODO: tick fx?


def heroHealAbilityHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    status = attr.get("Status")
    if status == "Casting Hero heal":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Hero heal", entity)

    duration = attr.get( ("Abilities", "Hero heal", "Duration") )
    tick_interval = attr.get( ("Abilities", "Hero heal", "Tick interval" ) )
    tick_count = (duration / tick_interval) - 1   # we send the first tick immediately
    heal_pct = attr.get( ("Abilities", "Hero heal", "Heal percentage") )
    heal_total = heal_pct * attr.get( "Hitpoints maximum" )
    heal_per_tick = int( heal_total / tick_count )
    if heal_per_tick <= 0:
        heal_per_tick = 1   # always guarantee at least some healing

    cooldown = attr.get( ("Abilities", "Hero heal", "Cooldown"))

    # do the first tick instantly for some feedback
    entity.getComponent( Enums.COMP_TYPE_EVENTIO ).receiveEvent( "Hero heal tick", heal_per_tick )

    timer.addTimer( "Hero heal timer", "Hero heal tick", tick_count, tick_interval, int(heal_per_tick) )
    world.networkAbilityImmediateSuccess( "Hero heal", entity )
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Hero heal", 0.0, -1, Vector3(0,0,0)), entity )


def rageAbilityHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    status = attr.get("Status")
    if entity.isDestroyed() or status == "Dead" or status == "Charge":
        return
    if status == "Casting Rage":
        attr.set("Status", "Combat")
        fsm.setState("Combat")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Rage", entity)
    #mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    #waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    #waypointMover.clearWaypoints()
    #mover.stop()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    tokens = []
    timer.addTimer("Rage timer", "Rage end", 1, ("Abilities", "Rage", "Time"), tokens)
    attackPeriodInc = attr.get(("Abilities", "Rage", "Attack period increase"))
    attackTimeInc = attr.get(("Abilities", "Rage", "Attack time increase"))
    damageInc = attr.get(("Abilities", "Rage", "Damage increase"))
    speedInc = attr.get(("Abilities", "Rage", "Speed increase"))
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    tokens.append(combatAttr.addModifier("Attack period", attackPeriodInc, Enums.MOD_TYPE_ADD))
    tokens.append(combatAttr.addModifier("Attack time", attackTimeInc, Enums.MOD_TYPE_ADD))
    tokens.append(combatAttr.addModifier("Damage minimum", damageInc, Enums.MOD_TYPE_ADD))
    tokens.append(combatAttr.addModifier("Damage maximum", damageInc, Enums.MOD_TYPE_ADD))
    tokens.append(combatAttr.addModifier("Speed", speedInc, Enums.MOD_TYPE_ADD))
    world.networkAbilityImmediateSuccess( "Rage", entity )
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Rage", 0.0, entity.id, Vector3( 0, 0, 0 )), entity )


def rageEnd(entity, world, tokens):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    for t in tokens:
        combatAttr.removeModifier(t)


def rageUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)


def heroHealUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Hero heal", "Level"), 1)
    attr.inc(("Abilities", "Hero heal", "Cooldown"), -1)
    attr.inc(("Abilities", "Hero heal", "Duration"), -1.0)
    attr.inc(("Abilities", "Hero heal", "Tick interval"), 0.05 )
    pct = attr.get(("Abilities", "Hero heal", "Heal percentage"))
    pct = min(pct + 0.1, 1.0)
    attr.set(("Abilities", "Hero heal", "Heal percentage"), pct)


def bearChargeUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Charge", "Level"), 1)
    attr.inc(("Abilities", "Charge", "Damage"), 30)
    attr.inc(("Abilities", "Charge", "Cooldown"), -1)
    attr.inc(("Abilities", "Charge", "Time"), .1)
    attr.inc(("Abilities", "Charge", "Range"), .05)


def bearLevelUpHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Stats", "Level"), 1)
    attr.inc(("Stats", "Skill points"), 1)
    strengthIncrease = attr.get(("Stats", "Strength increase"))
    dexterityIncrease = attr.get(("Stats", "Dexterity increase"))
    intelligenceIncrease = attr.get(("Stats", "Intelligence increase"))
    hitpointIncrease = attr.get(("Stats", "Hitpoint increase"))
    if hitpointIncrease:
        attr.inc("Hitpoints", hitpointIncrease)
        attr.inc("Hitpoints maximum", hitpointIncrease)
    if strengthIncrease:
        attr.inc(("Stats", "Strength"), strengthIncrease)
    if dexterityIncrease:
        attr.inc(("Stats", "Dexterity"), dexterityIncrease)
    if intelligenceIncrease:
        attr.inc(("Stats", "Intelligence"), intelligenceIncrease)
    if attr.get(("Stats", "Level")) is 3:
        attr.inc(("Stats", "Armor"), 10)
    if attr.get(("Stats", "Level")) is 6:
        attr.inc(("Stats", "Armor"), 15)
    if attr.get(("Stats", "Level")) is 10:
        attr.inc(("Stats", "Armor"), 20)
    user = world.getUserEntity(attr.get("Username")).getAttribute("User instance")
    heroLevel = attr.get(("Stats", "Level"))
    increases = world.getItemIncreasesForUser(user, heroLevel, heroLevel)
    if increases:
        world.addIncreasesToHero(entity, increases)
        #world.addIncreasesToBuilding()


def summonDuckHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    status = attr.get("Status")
    if status == "Casting Summon":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Summon", entity)
    # set despawn timer
    dmgMin = attr.get("Abilities.Summon.Damage minimum")
    dmgMax = attr.get("Abilities.Summon.Damage maximum")
    summon_time = attr.get("Abilities.Summon.Time")
    summon_prefab = attr.get("Abilities.Summon.Summon unit")

    # fall back to summoning wolf if celestial item is equipped on standard bear
    if summon_prefab == "Celestial wolf" and attr.get( "Subtype") == "Bear":
        summon_prefab = "Wolf"


    world.logDebug("Summoning %s with time %4.2f..." % (summon_prefab, summon_time))
    attribs = [
        ("Originator", entity.id),
        ("Team", attr.get("Team")),
        ("Rally point", entity.getPosition() + entity.getDirection()),
    ]
    summon_speed = attr.get("Abilities.Summon.Summon speed")
    if summon_speed:
        attribs.append(("Speed", summon_speed))
    aggro_range = attr.get("Abilities.Summon.Aggro range")
    if aggro_range:
        attribs.append(("Aggro range", aggro_range))
    if dmgMin and dmgMax:
        attribs.append(("Damage minimum", dmgMin))
        attribs.append(("Damage maximum", dmgMax))
    if attr.get("Subtype") == "Rogue":
        attribs.append(("Username", attr.get("Username") + " "))
        attribs.append(("Stats.Level", attr.get("Stats.Level")))
        attribs.append(("Mana", attr.get("Mana")))
        attribs.append(("Mana maximum", attr.get("Mana maximum")))

    a = list(attribs)
    a.append(("Offset", Vector3(0, 0, 0)))
    summon = world.createGameEntityForUser(
        summon_prefab,
        entity.getPosition() + entity.getDirection(),
        Vector3(1, 0, 0),
        attr.get("OwnerId"),
        tuple(a)
    )
    # set home as self on the summon unit so aggression can work properly
    summon.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Home", summon.id)
    summon.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Despawn timer", "Summon despawn", Enums.TIMER_ONCE, summon_time)
    world.networkCommand(Enums.WORLD_EVENT_ABILITY_USED, ("Summon", 0.0, -1, Vector3(0, 0, 0)), entity)