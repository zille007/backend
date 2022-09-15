import Enums
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector, findFirstUnitWithinRadius


def stoneElementalIdleUpdate(entity, world, args):
    attr = entity.getAttributes()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if attr.get("Target selected") is not Enums.NULL_ID:
        attr.set("Status", "Target")
        fsm.setState("Target")
    elif mover.isMoving():
        attr.set("Status", "Moving")
        fsm.setState("Moving")
    else:
        teamID = attr.get("Team")
        targetTags = attr.get("Target tags")
        ignoreTags = attr.get("Ignore tags")
        unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                                e.hasAllOfTags(targetTags) and
                                e.hasNoneOfTags(ignoreTags))
        target = findFirstUnitWithinRadius(entity.getPosition(), attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

        if target:
            attr.set("Status", "Combat")
            attr.set("Target", target.id)
            fsm.setState("Combat")
            if attr.get("Attack ready"):
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")


def stoneElementalMovingUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)

    if attr.get("Target selected") is not Enums.NULL_ID:
        attr.set("Status", "Target")
        fsm.setState("Target")
    elif not mover.isMoving():
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        attr.set("Target selected", Enums.NULL_ID)
        fsm.setState("Idle")


def stoneElementalTargetUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    target = world.getEntityByID(attr.get("Target selected"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
        attr.set("Status", "Idle")
        attr.set("Target selected", Enums.NULL_ID)
        fsm.setState("Idle")
    elif sensor.intersectsEntity("Attack", target):
        mover.stop()
        fsm.setState("Combat")
        attr.set("Status", "Combat")
        attr.set("Target", target.id)
        if attr.get("Attack ready"):
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
    else:
        if not mover.hasDestination() or (mover.destination - target.getPosition()).magnitude_squared() > 1.0:
            mover.setDestination(target.getPosition())


def stoneElementalCombatUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    target = world.getEntityByID(attr.get("Target"))
    if mover.isMoving():
        attr.set("Status", "Moving")
        attr.set("Target", Enums.NULL_ID)
        attr.set("Target selected", Enums.NULL_ID)
        fsm.setState("Moving")
    elif target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        attr.set("Target selected", Enums.NULL_ID)
        fsm.setState("Idle")
    elif not sensor.intersectsEntity("Attack", target):
        if attr.get("Target selected") is not Enums.NULL_ID:
            attr.set("Status", "Target")
            fsm.setState("Target")
        else:
            attr.set("Status", "Idle")
            attr.set("Target", Enums.NULL_ID)
            fsm.setState("Idle")


def stoneElementalChargeUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    teamID = attr.get("Team")

    targets = world.queryEnemyUnitsByCircle(
        teamID,
        entity.getPosition(),
        attr.get(("Abilities", "Charge", "Range")),
        lambda e: e.getAttribute("Status") != "Dead" and
                  e.hasTag("Targetable")
    )
    victims = entity.getAttribute(("Abilities", "Charge", "Victims"))
    targets = [t for t in targets if t not in victims]
    for t in targets:
        victims.append(t)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    dmgMin = attr.get(("Abilities", "Charge", "Damage minimum"))
    dmgMax = attr.get(("Abilities", "Charge", "Damage maximum"))
    dmgType = attr.get(("Abilities", "Charge", "Damage type"))
    pierceAmount = attr.get(("Abilities", "Charge", "Pierce amount"))
    for t in targets:
        target = t
        eventIO.sendEvent(target, "Knockback", (5, t.getPosition() - entity.getPosition(), .4, 1.0))
        eventIO.receiveEvent("Damage inflict", (dmgMin, dmgMax, dmgType, pierceAmount, t.id))


def stoneElementalCharge(entity, world, (dir, power)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat" and status != "Casting Charge":
        return
    dir = dir.normalized()
    cost = attr.get(("Abilities", "Charge", "Cost"))
    mana = attr.get("Mana")
    if attr.get("Status") is not "Dead" and attr.get(("Abilities", "Charge", "Ready")) and cost <= mana:
        if status == "Casting Charge":
            world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Charge", entity)
        attr.set("Status", "Charge")
        entity.getComponent(Enums.COMP_TYPE_FSM).setState("Charge")
        attr.set("Target selected", Enums.NULL_ID)
        attr.set(("Abilities", "Charge", "Ready"), False)
        attr.inc("Mana", -cost)
        speedIncrease = attr.get(("Abilities", "Charge", "Speed increase"))*power
        chargeTime = attr.get( ("Abilities", "Charge", "Time") )
        token = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES).addModifier("Speed", speedIncrease, Enums.MOD_TYPE_ADD)
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge timer", "Charge end", Enums.TIMER_ONCE, chargeTime, token)
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        entity.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(dir)

        world.networkAbilityImmediateSuccess( "Charge", entity )
        #world.networkCommand(Enums.WORLD_EVENT_CHARGE, None, entity)
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Charge", chargeTime, -1, Vector3( 0, 0, 0 )), entity )



def leapHandler(entity, world, pos):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    tags.remove("Ground")
    tags.add("Air")

    if status == "Casting Leap":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Leap", entity)

    if waypointMover:
        waypointMover.clearWaypoints()
    attr.set("Status", "Leap")
    if fsm:
        fsm.setState("Leap")
    prevSpeed = attr.get("Speed")
    speed = attr.get(("Abilities", "Leap", "Speed"))
    attr.set("Speed", speed)
    time = (pos - entity.getPosition()).magnitude()/speed
    timer.addTimer("Leap timer", "Leap end", Enums.TIMER_ONCE, time, prevSpeed)
    mover.setDestination(pos)
    #world.networkCommand(Enums.WORLD_EVENT_LEAP, time, entity)
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Leap", time, -1, pos), entity )


def leapEnd(entity, world, prevSpeed):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    teamID = attr.get("Team")
    tags.add("Ground")
    tags.remove("Air")

    attr.set("Status", "Idle")
    if fsm:
        fsm.setState("Idle")
    attr.set("Speed", prevSpeed)
    mover.stop()
    targets = world.queryEnemyUnitsByCircle(teamID, entity.getPosition(), attr.get(("Abilities", "Leap", "Stun radius")))
    for t in targets:
        eventIO = t.getComponent(Enums.COMP_TYPE_EVENTIO)
        if eventIO:
            eventIO.receiveEvent("Stun", attr.get(("Abilities", "Leap", "Stun time")))


def birdCarryHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    tags.add("Air")
    tags.remove("Ground")
    attr.set("Status", "Carry")
    if fsm:
        fsm.setState("Carry")
    prevSpeed = attr.get("Speed")
    speed = attr.get(("Abilities", "Bird carry", "Speed"))
    attr.set("Speed", speed)
    time = attr.get(("Abilities", "Bird carry", "Time"))
    timer.addTimer("Bird carry timer", "Bird carry end", Enums.TIMER_ONCE, time, prevSpeed)
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Bird carry", time, -1, Vector3( 0, 0, 0 )), entity )


def birdCarryEnd(entity, world, prevSpeed):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    tags.remove("Air")
    tags.add("Ground")
    attr.set("Status", "Idle")
    if fsm:
        fsm.setState("Idle")
    attr.set("Speed", prevSpeed)


def birdHealHandler(entity, world, args):
    attr = entity.getAttributes()
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)

    if status == "Casting Bird heal":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Bird heal", entity)

    mover.stop()
    waypointMover.clearWaypoints()
    attr.set("Status", "Bird heal")
    fsm.setState("Bird heal")
    fsm.setUpdatePeriod(attr.get("Abilities.Bird heal.Period"))
    timer.addTimer("Bird heal timer", "Bird heal end", 1, "Abilities.Bird heal.Duration")
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Bird heal", 0.0, entity.id, Vector3( 0, 0, 0 )), entity )


def birdHealUpdate(entity, world, args):
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    amount = attr.get("Abilities.Bird heal.Heal amount")
    eventIO.receiveEvent("Heal", (amount, entity.id))


def birdHealEnd(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    attr.set("Status", "Idle")
    fsm.setState("Idle")
    fsm.setUpdatePeriod(0.0)


def earthquakeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    teamID = attr.get("Team")

    if status == "Casting Earthquake":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Earthquake", entity)

    targets = world.getEnemyUnitsForTeam(teamID)
    dmgMin = combatAttr.get(("Abilities", "Earthquake", "Damage minimum"))
    dmgMax = combatAttr.get(("Abilities", "Earthquake", "Damage maximum"))
    dmgType = attr.get(("Abilities", "Earthquake", "Damage type"))
    pierceAmount = combatAttr.get(("Abilities", "Earthquake", "Pierce amount"))
    for t in targets:
        eventIO = t.getComponent(Enums.COMP_TYPE_EVENTIO)
        if eventIO:
            eventIO.receiveEvent("Stun", attr.get(("Abilities", "Earthquake", "Stun time")))
            eventIO.receiveEvent("Damage inflict", (dmgMin, dmgMax, dmgType, pierceAmount, t.id))
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Earthquake", 0.0, -1, Vector3( 0, 0, 0 )), entity )


def earthquakeUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Earthquake", "Level"), 1)
    attr.inc(("Abilities", "Earthquake", "Cooldown"), -5)
    attr.inc(("Abilities", "Earthquake", "Stun"), 2)
    attr.inc(("Abilities", "Earthquake", "Damage minimum"), 5)
    attr.inc(("Abilities", "Earthquake", "Damage maximum"), 10)


def leapUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Leap", "Level"), 1)
    attr.inc(("Abilities", "Leap", "Range"), 2)
    attr.inc(("Abilities", "Leap", "Stun radius"), .25)
    attr.inc(("Abilities", "Leap", "Stun time"), .5)


def birdCarryUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Bird carry", "Level"), 1)
    attr.inc(("Abilities", "Bird carry", "Time"), 2)
    attr.inc(("Abilities", "Bird carry", "Speed"), .25)


def stoneElementalChargeUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Charge", "Level"), 1)
    attr.inc(("Abilities", "Charge", "Damage minimum"), 10)
    attr.inc(("Abilities", "Charge", "Damage maximum"), 20)
    attr.inc(("Abilities", "Charge", "Time"), .05)
    attr.inc(("Abilities", "Charge", "Stun time"), .25)


