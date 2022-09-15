import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector, findFirstUnitWithinRadius
import copy


def fyresteinIdleUpdate(entity, world, args):
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


def fyresteinMovingUpdate(entity, world, args):
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


def fyresteinCombatUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
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
        if not timer.hasTimer("Combat timer"):
            if attr.get("Attack ready"):
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")


## Targeting

def fyresteinTargetUpdate(entity, world, args):
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


## Abilities

def fyresteinChargeUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    range = attr.get(("Abilities", "Charge", "Range"))
    radius = attr.get(("Abilities", "Charge", "Radius"))
    dir = attr.get(("Abilities", "Charge", "Direction"))
    power = attr.get(("Abilities", "Charge", "Power"))
    dmgMin = attr.get(("Abilities", "Charge", "Damage minimum"))
    dmgMax = attr.get(("Abilities", "Charge", "Damage maximum"))
    flameTime = attr.get(("Abilities", "Charge", "Flame lifetime"))
    pos = entity.getPosition()
    randomPos = pos + (dir*power*range) + (angleToUnitVector3(random.random()*360)*radius*random.random())
    eventIO.receiveEvent("Fyre emit", (randomPos, dmgMin, dmgMax, flameTime))


def fyresteinCharge(entity, world, (dir, power)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    status = attr.get("Status")
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat" and status != "Casting Charge":
        return
    cost = attr.get(("Abilities", "Charge", "Cost"))
    mana = attr.get("Mana")
    if status != "Dead" and attr.get(("Abilities", "Charge", "Ready")) and cost <= mana:
        if status == "Casting Charge":
            world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Charge", entity)
        attr.set(("Abilities", "Charge", "Ready"), False)
        mover.stop()
        waypointMover.clearWaypoints()
        attr.set("Status", "Charge")
        attr.set(("Abilities", "Charge", "Direction"), dir.copy())
        attr.set(("Abilities", "Charge", "Power"), power)
        fsm.setUpdatePeriod(attr.get(("Abilities", "Charge", "Emit period")))
        fsm.setState("Charge")
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        timer.addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        attr.set(("Abilities", "Charge", "Ready"), False)
        attr.inc("Mana", -cost)
        chargeTime = attr.get(("Abilities", "Charge", "Time"))
        timer.addTimer("Charge timer", "Charge end", 1, chargeTime)
        world.networkAbilityImmediateSuccess( "Charge", entity )
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Charge", chargeTime, -1, Vector3( 0, 0, 0 )), entity )
        #world.networkCommand( Enums.WORLD_EVENT_CHARGE, None, entity )


def fyresteinChargeEnd(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if attr.get("Status") != "Dead":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
    entity.getComponent(Enums.COMP_TYPE_MOVER).stop()
    fsm.setUpdatePeriod(0)


def concussionBombAbility(entity, world, pos):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    user = world.getUserForUnit(entity)
    destVec = (pos - entity.getPosition())
    bomb = world.createGameEntityForUser(
        "Concussion bomb",
        entity.getPosition(),
        destVec.normalized(),
        user,
        (
            ("Destination", pos.copy()),
            ("Stun time", attr.get(("Abilities", "Concussion bomb", "Stun time"))),
            ("Damage", attr.get(("Abilities", "Concussion bomb", "Damage"))),
            ("Radius", attr.get(("Abilities", "Concussion bomb", "Radius"))),
            ("Speed", attr.get(("Abilities", "Concussion bomb", "Speed"))),
        )
    )
    bombMover = bomb.getComponent(Enums.COMP_TYPE_MOVER)
    bombAttr = bomb.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    bombTimer = bomb.getComponent(Enums.COMP_TYPE_TIMER)  # a bomb that has a timer is basically a timebomb
    bombSpeed = bombAttr.get("Speed")
    travelTime = destVec.magnitude()/bombSpeed
    bombTimer.addTimer("Explode timer", "Explode", 1, travelTime)
    bombMover.setDestination(pos)
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Concussion bomb", 0.0, -1, pos), entity )


def concussionBombUpgrade(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Concussion bomb", "Level"), 1)
    attr.inc(("Abilities", "Concussion bomb", "Stun time"), 1)
    attr.inc(("Abilities", "Concussion bomb", "Damage"), 5)


def concussionBombExplode(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)

    radius = attr.get("Radius")
    dmgMin = attr.get("Damage minimum")
    dmgMax = attr.get("Damage maximum")
    dmgType = attr.get("Damage type")
    pierceAmount = attr.get("Pierce amount")
    stunTime = attr.get("Stun time")
    enemies = world.getEnemyCreepsForTeam(attr.get("Team")) + filter(lambda h: h.getAttribute("Team") is not attr.get("Team"), world.getHeroes())
    for e in enemies:
        if (e.getPosition() - entity.getPosition()).magnitude_squared() < (radius + e.getSize())**2:
            enemyEventIO = e.getComponent(Enums.COMP_TYPE_EVENTIO)
            enemyEventIO.receiveEvent("Stun", stunTime)
            eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, e.id))
    eventIO.receiveEvent("_destroy")


def fumesHandler(entity, world, pos):
    attr = entity.getAttributes()
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    heroes = copy.copy(world.getHeroes())
    heroes.remove(entity)
    creeps = world.getCreeps()
    units = heroes + creeps
    radius = attr.get("Abilities.Fumes.Radius")
    slowPercentage = attr.get("Abilities.Fumes.Slow percentage")
    slowDuration = attr.get("Abilities.Fumes.Slow duration")
    if status == "Casting Fumes":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Fumes", entity)

    for u in units:
        upos = u.getPosition()
        usize = u.getSize()
        if (upos - pos).magnitude_squared() <= (radius + usize)**2:
            u.receiveEvent("Buff", ("Speed", slowPercentage, Enums.ATTR_MUL, "Temporary", slowDuration))
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Fumes", 0.0, -1, pos), entity )


def rocketEscapeHandler(entity, world, pos):
    attr = entity.getAttributes()
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    if status == "Casting Rocket escape":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Rocket escape", entity)

    attr.set("Status", "Rocket escape casting")
    fsm.setState("Rocket escape casting")
    duration = attr.get("Abilities.Rocket escape.Duration")
    cast_time = attr.get("Abilities.Rocket escape.Casting time")
    timer.addTimer("Rocket escape casting timer", "Rocket escape start", 1, cast_time, (pos - entity.getPosition()).normalized())
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Rocket escape", duration, entity.id, Vector3( 0, 0, 0 )), entity )


def rocketEscapeStart(entity, world, dir):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)

    attr.set("Status", "Rocket escape")
    fsm.setState("Rocket escape")
    fsm.setUpdatePeriod(attr.get("Abilities.Rocket escape.Period"))
    speedToken = attr.addModifier("Speed", attr.get("Abilities.Rocket escape.Speed"), Enums.MOD_TYPE_SET_OVERRIDE)
    mover.setDirectionAndMove(dir)
    timer.addTimer("Rocket escape timer", "Rocket escape end", 1, "Abilities.Rocket escape.Duration", speedToken)


def rocketEscapeUpdate(entity, world, args):
    attr = entity.getAttributes()
    user = world.getUserForUnit(entity)
    dmgMin = attr.get("Abilities.Rocket escape.Damage minimum")
    dmgMax = attr.get("Abilities.Rocket escape.Damage maximum")
    dmgType = attr.get("Abilities.Rocket escape.Damage type")
    pierceAmount = attr.get("Abilities.Rocket escape.Pierce amount")

    world.createGameEntityForUser("Fyre area", entity.getPosition(), Vector3(1, 0, 0), user,
        (
            ("Team", attr.get("Team")),
            ("Damage minimum", dmgMin),
            ("Damage maximum", dmgMax),
            ("Damage type", dmgType),
            ("Pierce amount", pierceAmount),
            ("Originator", entity.id)
        )
    )


def rocketEscapeEnd(entity, world, speedToken):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)

    mover.stop()
    attr.removeModifier(speedToken)
    fsm.setUpdatePeriod(0.0)

    if attr.get("Status") != "Dead":
        attr.set("Status", "Idle")
        fsm.setState("Idle")


def selfDestructHandler(entity, world, args):
    attr = entity.getAttributes()
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    if status == "Casting Self destruct":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Self destruct", entity)

    attr.set("Status", "Self destruct")
    fsm.setState("Self destruct")
    fsm.setUpdatePeriod(1.0)
    time = attr.get("Abilities.Self destruct.Time")
    attr.set("Abilities.Self destruct.Counter", time)
    timer.addTimer("Self destruct timer", "Self destruct end", 1, time)
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Self destruct", time, entity.id, Vector3( 0, 0, 0 )), entity )


def selfDestructUpdate(entity, world, args):
    attr = entity.getAttributes()
    attr.inc("Abilities.Self destruct.Counter", -1)


def selfDestructEnd(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    attr.set("Abilities.Self destruct.Counter", 0)

    if attr.get("Status") == "Dead":
        return

    attr.set("Status", "Idle")
    fsm.setState("Idle")
    fsm.setUpdatePeriod(0.0)
    pos = entity.getPosition()
    radius = attr.get("Abilities.Self destruct.Radius")
    enemies = world.getEnemyUnitsForTeam(attr.get("Team"))
    dmgMin = attr.get("Abilities.Self destruct.Damage minimum")
    dmgMax = attr.get("Abilities.Self destruct.Damage maximum")
    dmgType = attr.get("Abilities.Self destruct.Damage type")
    pierceAmount = attr.get("Abilities.Self destruct.Pierce amount")
    for e in enemies:
        epos = e.getPosition()
        esize = e.getSize()
        if (epos - pos).magnitude_squared() <= (radius + esize)**2:
            eventIO.receiveEvent("Damage inflict", (dmgMin, dmgMax, dmgType, pierceAmount, e.id))
    eventIO.receiveEvent("Death")


def fyreEmit(entity, world, (pos, dmgMin, dmgMax, flameTime)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    user = world.getUserForUnit(entity)
    fyreFlame = world.createGameEntityForUser(
        "Fyre flame",
        entity.getPosition(),
        (entity.getPosition() - pos).normalized(),
        user,
        (
            ("Team", attr.get("Team")),
            ("Destination", pos),
            ("Damage minimum", dmgMin),
            ("Damage maximum", dmgMax),
            ("Lifetime", flameTime),
            ("Originator", entity.id),
        )
    )
    timer = fyreFlame.getComponent(Enums.COMP_TYPE_TIMER)
    timer.resetTimer("Lifetime timer")
    fyreMover = fyreFlame.getComponent(Enums.COMP_TYPE_MOVER)
    fyreMover.setDestination(pos)


def fyreFlameAtDestination(entity, world, args):
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    user = world.getUserForUnit(entity)
    originator = attr.get("Originator")
    dmgMin = attr.get("Damage minimum")
    dmgMax = attr.get("Damage maximum")
    dmgType = attr.get("Damage type")
    pierceAmount = attr.get("Pierce amount")
    world.createGameEntityForUser("Fyre area", entity.getPosition(), Vector3(1, 0, 0), user,
        (
            ("Team", attr.get("Team")),
            ("Damage minimum", dmgMin),
            ("Damage maximum", dmgMax),
            ("Damage type", dmgType),
            ("Pierce amount", pierceAmount),
            ("Originator", originator)
        )
    )
    eventIO.receiveImmediateEvent("_destroy", world)


def fyresteinAttackHandler(entity, world, targetID):
    if entity.isDestroyed():
        return
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status == "Stunned" or status == "Dead":
        return
    target = world.getEntityByID(targetID)
    if target is not None and not target.isDestroyed() and target.hasTag("Targetable"):
        user = world.getUserForUnit(entity)
        pos = target.getPosition()
        dir = (pos - entity.getPosition()).normalized()
        combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
        dmgMin = combatAttr.queryEffectiveAttribute("Damage minimum")
        dmgMax = combatAttr.queryEffectiveAttribute("Damage maximum")
        dmgType = attr.get("Damage type")
        pierceAmount = combatAttr.queryEffectiveAttribute("Pierce amount")
        fyreFlame = world.createGameEntityForUser(
            "Fyre flame",
            entity.getPosition(),
            dir,
            user,
            (
                ("Team", attr.get("Team")),
                ("Destination", pos),
                ("Damage minimum", dmgMin),
                ("Damage maximum", dmgMax),
                ("Damage type", dmgType),
                ("Pierce amount", pierceAmount),
                ("Originator", entity.id),
            )
        )
        if fyreFlame:
            fyreMover = fyreFlame.getComponent(Enums.COMP_TYPE_MOVER)
            fyreMover.setDestination(pos)
    else:
        attr.set("Target", Enums.NULL_ID)


def fyreFlameDamage(entity, world, args):
    if entity.isDestroyed():
        return
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)

    dmgMin = attr.get("Damage minimum")
    dmgMax = attr.get("Damage maximum")
    dmgType = attr.get("Damage type")
    pierceAmount = attr.get("Pierce amount")

    enemies = world.getEnemyUnitsForTeam(attr.get("Team"))
    for e in enemies:
        if e.hasTag("Targetable") and e.hasTag("Ground"):
            if (e.getPosition() - entity.getPosition()).magnitude_squared() <= (attr.get("Damage radius") + e.getSize())**2:
                eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, e.id))


def fyresteinLevelUpHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Stats", "Level"), 1)
    attr.inc(("Stats", "Skill points"), 1)
    strengthIncrease = attr.get(("Stats", "Strength increase"))
    dexterityIncrease = attr.get(("Stats", "Dexterity increase"))
    intelligenceIncrease = attr.get(("Stats", "Intelligence increase"))
    hitpointIncrease = attr.get(("Stats", "Hitpoint increase"))
    attr.inc("Damage maximum", 5)
    if hitpointIncrease:
        attr.inc("Hitpoints", hitpointIncrease)
        attr.inc("Hitpoints maximum", hitpointIncrease)
    if strengthIncrease:
        attr.inc(("Stats", "Strength"), strengthIncrease)
    if dexterityIncrease:
        attr.inc(("Stats", "Dexterity"), dexterityIncrease)
    if intelligenceIncrease:
        attr.inc(("Stats", "Intelligence"), intelligenceIncrease)
    if attr.get(("Stats", "Level")) is 4:
        attr.inc(("Stats", "Armor"), 5)
    if attr.get(("Stats", "Level")) is 8:
        attr.inc(("Stats", "Armor"), 10)
    user = world.getUserEntity(attr.get("Username")).getAttribute("User instance")
    heroLevel = attr.get(("Stats", "Level"))
    increases = world.getItemIncreasesForUser(user, heroLevel, heroLevel)
    if increases:
        world.addIncreasesToHero(entity, increases)


def fyresteinChargeUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Charge", "Level"), 1)
    attr.inc(("Abilities", "Charge", "Flame lifetime"), .42)
    attr.inc(("Abilities", "Charge", "Time"), .25)
    attr.inc(("Abilities", "Charge", "Emit period"), -.025)
    attr.inc(("Abilities", "Charge", "Damage"), 10)

