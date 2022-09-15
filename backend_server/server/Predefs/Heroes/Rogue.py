import Enums
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector, findFirstUnitWithinRadius


def rogueIdleUpdate(entity, world, args):
    attr = entity.getAttributes()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if attr.get("Attack haste period") != attr.get("Attack period"):
        attr.set("Attack haste period", attr.get("Attack period"))

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
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack haste period")
            attr.inc("Attack haste period", -attr.get(("Abilities", "Haste", "Attack period decrease")))


def rogueMovingUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)

    if attr.get("Attack haste period") != attr.get("Attack period"):
        attr.set("Attack haste period", attr.get("Attack period"))

    if attr.get("Target selected") is not Enums.NULL_ID:
        attr.set("Status", "Target")
        fsm.setState("Target")
    elif not mover.isMoving():
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        attr.set("Target selected", Enums.NULL_ID)
        fsm.setState("Idle")


def rogueTargetUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if attr.get("Attack haste period") != attr.get("Attack period"):
        attr.set("Attack haste period", attr.get("Attack period"))

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
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack haste period")
        attr.inc("Attack haste period", -attr.get(("Abilities", "Haste", "Attack period decrease")))
    else:
        if not mover.hasDestination() or (mover.destination - target.getPosition()).magnitude_squared() > 1.0:
            mover.setDestination(target.getPosition())


def rogueCombatUpdate(entity, world, args):
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
    else:
        return


def rogueAttackStart(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr.set("Attack ready", True)
    if attr.get("Status") != "Combat":
        timer.removeTimer("Combat timer")
        return
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        period = attr.get("Attack haste period")
        periodMinimum = attr.get(("Abilities", "Haste", "Attack period minimum"))
        hasteLevel = attr.get(("Abilities", "Haste", "Level"))
        if attr.get("Status") == "Combat" and period > periodMinimum and hasteLevel > 0:
            periodDecrease = attr.get(("Abilities", "Haste", "Attack period decrease"))
            if (period - periodDecrease) < periodMinimum:
                attr.set("Attack haste period", periodMinimum)
            else:
                attr.inc("Attack haste period", -periodDecrease)
        attr.set("Attack ready", False)
        timer.addTimer("Attack start timer", "Attack", Enums.TIMER_ONCE, "Attack time", target.id)
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def rogueAttackFirst(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        period = attr.get("Attack haste period")
        periodMinimum = attr.get(("Abilities", "Haste", "Attack period minimum"))
        hasteLevel = attr.get(("Abilities", "Haste", "Level"))
        if attr.get("Status") == "Combat" and period > periodMinimum and hasteLevel > 0:
            periodDecrease = attr.get(("Abilities", "Haste", "Attack period decrease"))
            if (period - periodDecrease) < periodMinimum:
                attr.set("Attack haste period", periodMinimum)
            else:
                attr.inc("Attack haste period", -periodDecrease)
        attr.set("Attack ready", False)
        timer.addTimer("Attack start timer", "Attack", Enums.TIMER_ONCE, "Attack time", target.id)
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def rogueCharge(entity, world, (dir, power)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat" and status != "Casting Charge":
        return
    dir = dir.normalized()
    cost = attr.get(("Abilities", "Charge", "Cost"))
    mana = attr.get("Mana")
    if attr.get("Status") is not "Dead" and attr.get(("Abilities", "Charge", "Ready")) and cost <= mana:
        if status == "Casting Charge":
            attr.set("Status", "Idle")
            fsm.setState("Idle")
            world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Charge", entity)
        mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
        waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
        if waypointMover:
            waypointMover.clearWaypoints()
        mover.stop()
        attr.set(("Abilities", "Charge", "Ready"), False)
        attr.inc("Mana", -cost)
        calcDir = angleToUnitVector3(-15, dir)
        projectile = world.createGameEntityForUser(
            "Rogue arrow",
            entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
            calcDir.copy(),
            attr.get( "OwnerId" ),
            (
                ("Home", entity.id),
                ("Team", attr.get("Team")),
                ("Originator", entity.id),
                ("Damage minimum", attr.get("Abilities.Charge.Damage minimum")),
                ("Damage maximum", attr.get("Abilities.Charge.Damage maximum")),
            )
        )
        if projectile is None:
            return
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        lifetime = attr.get(("Abilities", "Charge", "Time"))
        projectile.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Lifetime timer", "Lifetime end", Enums.TIMER_ONCE, lifetime)
        projectile.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(calcDir.copy())

        calcDir = dir.copy()
        projectile = world.createGameEntityForUser(
            "Rogue arrow",
            entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
            calcDir.copy(),
            attr.get( "OwnerId" ),
            (
                ("Home", entity.id),
                ("Team", attr.get("Team")),
                ("Level", attr.get(("Stats", "Level"))),
                ("Originator", entity.id),
                ("Damage minimum", attr.get("Abilities.Charge.Damage minimum")),
                ("Damage maximum", attr.get("Abilities.Charge.Damage maximum")),
            )
        )
        if projectile is None:
            return
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        lifetime = attr.get(("Abilities", "Charge", "Time"))
        projectile.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Lifetime timer", "Lifetime end", Enums.TIMER_ONCE, lifetime)
        projectile.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(calcDir.copy())

        calcDir = angleToUnitVector3(15, dir)
        projectile = world.createGameEntityForUser(
            "Rogue arrow",
            entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
            calcDir.copy(),
            attr.get( "OwnerId" ),
            (
                ("Home", entity.id),
                ("Team", attr.get("Team")),
                ("Level", attr.get(("Stats", "Level"))),
                ("Originator", entity.id),
                ("Damage minimum", attr.get("Abilities.Charge.Damage minimum")),
                ("Damage maximum", attr.get("Abilities.Charge.Damage maximum")),
            )
        )
        if projectile is None:
            return
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        lifetime = attr.get(("Abilities", "Charge", "Time"))
        projectile.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Lifetime timer", "Lifetime end", Enums.TIMER_ONCE, lifetime)
        projectile.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(calcDir.copy())

        world.networkAbilityImmediateSuccess( "Charge", entity )
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Charge", 0.0, -1, Vector3( 0, 0, 0 )), entity )


def paralyzeHandler(entity, world, targetID):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    status = attr.get("Status")
    if status == "Casting Paralyze":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Paralyze", entity)
    target = world.getEntityByID(targetID)
    if target:
        time = attr.get(("Abilities", "Paralyze", "Time"))
        target.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Stun", time)
        world.networkCommand(Enums.WORLD_EVENT_ABILITY_USED, ("Paralyze", 0.0, targetID, Vector3(0, 0, 0)), entity)


def paralyzeUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Paralyze", "Level"), 1)
    attr.inc(("Abilities", "Paralyze", "Time"), 1)


def rogueChargeUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Charge", "Level"), 1)
    attr.inc(("Abilities", "Charge", "Damage"), 40)
    attr.inc(("Abilities", "Charge", "Cooldown"), -1)


def summonDecoyHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    # set despawn timer

    if status == "Casting Summon":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Summon", entity)

    dmgMin = attr.get(("Abilities.Summon.Damage minimum"))
    dmgMax = attr.get(("Abilities.Summon.Damage maximum"))
    summon_time = attr.get(("Abilities", "Summon", "Time"))
    summon_prefab = attr.get(("Abilities", "Summon", "Summon unit"))
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
        attr.get( "OwnerId"),
        tuple(a)
    )
    # set home as self on the summon unit so aggression can work properly
    summon.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Home", summon.id)
    summon.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Despawn timer", "Summon despawn", Enums.TIMER_ONCE, summon_time)
    world.networkCommand(Enums.WORLD_EVENT_ABILITY_USED, ("Summon", 0.0, -1, Vector3(0, 0, 0)), entity)