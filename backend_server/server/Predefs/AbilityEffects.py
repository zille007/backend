import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector


def abilityReady(entity, world, name):
    entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set(("Abilities", name, "Ready"), True)


def chargeReady(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set(("Abilities", "Charge", "Ready"), True)


def chargeEnd(entity, world, modToken):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    if attr.get("Status") != "Dead":
        attr.set("Status", "Idle")
    if attr.get(("Abilities", "Charge", "Victims")) is not None:
        attr.set(("Abilities", "Charge", "Victims"), [])
    combatAttr.removeModifier(modToken)
    entity.getComponent(Enums.COMP_TYPE_MOVER).stop()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Idle")
    world.networkCommand(Enums.WORLD_EVENT_ABILITY_ENDED, "Charge", entity)


def particleEnd(entity, world, token):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set("Status", "Ended")
    world.destroyEntity(entity)


def basicAttack(entity, world, targets):
    if targets is None:
        return

    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    if isinstance(targets, list):
        for t in targets:
            if combatAttr and eventIO:
                minDmg = combatAttr.queryEffectiveAttribute("Damage minimum")
                maxDmg = max(combatAttr.queryEffectiveAttribute("Damage maximum"), minDmg)
                dmgType = attr.get("Damage type")
                if dmgType is None:
                    dmgType = "Melee"
                armorPierce = attr.get("Armor pierce")
                if armorPierce is None:
                    armorPierce = 0.0
                strength = combatAttr.queryEffectiveAttribute(("Stats", "Strength"))
                damage = random.randint(minDmg, maxDmg) + (strength if strength else 0)
                target = t
                eventIO.sendEvent(target, "Damage", (damage, dmgType, armorPierce, entity.id))
        return
    else:
        if combatAttr and eventIO:
            minDmg = combatAttr.queryEffectiveAttribute("Damage minimum")
            maxDmg = max(combatAttr.queryEffectiveAttribute("Damage maximum"), minDmg)
            dmgType = attr.get("Damage type")
            if dmgType is None:
                dmgType = "Melee"
            armorPierce = attr.get("Armor pierce")
            if armorPierce is None:
                armorPierce = 0.0
            strength = combatAttr.queryEffectiveAttribute(("Stats", "Strength"))
            damage = random.randint(minDmg, maxDmg) + (strength if strength else 0)
            target = targets
            eventIO.sendEvent(target, "Damage", (damage, dmgType, armorPierce, entity.id))


def basicHeal(entity, world, targets):
    if targets is None:
        return

    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    if isinstance(targets, list):
        for t in targets:
            if attributes and eventIO:
                minHeal = attributes.get("Heal minimum")
                maxHeal = max(attributes.get("Heal maximum"), minHeal)
                heal = random.randint(minHeal, maxHeal)
                target = t
                eventIO.sendEvent(target, "Heal", (heal, entity.id))
        return
    else:
        if attributes and eventIO:
            minHeal = attributes.get("Heal minimum")
            maxHeal = max(attributes.get("Heal maximum"), minHeal)
            heal = random.randint(minHeal, maxHeal)
            target = targets
            eventIO.sendEvent(target, "Heal", (heal, entity.id))


def berserkHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    cost = attr.get(("Abilities", "Berserk", "Cost"))
    teamEntity = world.getTeamEntity(attr.get("Team"))
    teamAttr = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    honor = teamAttr.get(("Resources", "Honor"))
    if attr.get("Status") is not "Dead" and attr.get(("Abilities", "Berserk", "Ready")) and honor >= cost:
        teamAttr.inc(("Resources", "Honor"), -cost)
        attr.set(("Abilities", "Berserk", "Ready"), False)
        speedIncrease = attr.get(("Abilities", "Berserk", "Speed increase"))
        damageMinimumIncrease = attr.get(("Abilities", "Berserk", "Damage minimum increase"))
        damageMaximumIncrease = attr.get(("Abilities", "Berserk", "Damage maximum increase"))
        time = attr.get(("Abilities", "Berserk", "Time"))

        eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
        eventIO.receiveEvent("Buff", ("Speed", speedIncrease, Enums.ATTR_INC, "Temporary", time))
        eventIO.receiveEvent("Buff", ("Damage minimum", damageMinimumIncrease, Enums.ATTR_INC, "Temporary", time))
        eventIO.receiveEvent("Buff", ("Damage maximum", damageMaximumIncrease, Enums.ATTR_INC, "Temporary", time))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Berserk timer", "Berserk end", Enums.TIMER_ONCE, time)


def berserkEnd(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set(("Abilities", "Berserk", "Ready"), True)


def summonHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    # set despawn timer
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


def summonDespawnHandler(entity, world, pos):
    world.logDebug( "Despawning summoned entity %d..." % (entity.id,))
    # TODO: create despawning effect entity here
    world.destroyEntity( entity )


def summonUpgradeHandler(entity, world, args):
    world.logDebug("Upgrading summon")
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Summon", "Level"), 1)
    attr.inc(("Abilities", "Summon", "Cooldown"), -5)
    attr.inc(("Abilities", "Summon", "Time"), 5)


def buffHandler(entity, world, (attribute, modValue, modType, effectType, time)):
    token = -1
    if effectType == "Temporary":
        combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
        token = combatAttr.addModifier(attribute, modValue, Enums.MOD_TYPE_ADD if modType is Enums.ATTR_INC else Enums.MOD_TYPE_MUL)
        if time is not None:
            timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
            timer.addAnonymousTimer("Buff end", Enums.TIMER_ONCE, time, token)
    elif effectType == "Permanent":
        attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if modType is Enums.ATTR_SET:
            if isinstance(modValue, str) or isinstance(modValue, tuple):
                attr.set(attribute, attr.get(modValue))
        elif modType is Enums.ATTR_INC:
            attr.inc(attribute, modValue)
        elif modType is Enums.ATTR_MUL:
            attr.mul(attribute, modValue)
    entity.receiveEvent("Damage recalculate")
    world.networkCommand(Enums.WORLD_EVENT_BUFF, (time if time else 0, str(attribute), token), entity)


def buffEnd(entity, world, token):
    #world.logInfo( "Buff end for buff with token %d" % (token,))
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    attribute = combatAttr.removeModifier(token)
    entity.receiveEvent("Damage recalculate")
    world.networkCommand(Enums.WORLD_EVENT_BUFF_EXPIRED, (token, attribute), entity)


def stunHandler(entity, world, stunTime):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status == "Dead" or status == "Charge":
        return
    attr.set("Status", "Stunned")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Stunned")
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    timer.addTimer("Stun timer", "Stun end", 1, stunTime)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    if waypointMover:
        waypointMover.pause()
        if mover.isMoving():
            mover.stop()
    elif mover:
        mover.stop()


def stunEnd(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set("Status", "Idle")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Idle")
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    if waypointMover:
        waypointMover.unpause()


def freezeHandler(entity, world, freezeTime):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status != "Idle":
        return
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    timer.addTimer("Freeze timer", "Freeze end", 1, freezeTime)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Freeze")
    attr.set("Status", "Freeze")


def freezeEnd(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.set("Status", "Idle")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Idle")
    if entity.hasTag("Defender"):
        entity.receiveEvent("Spawn")


def knockbackHandler(entity, world, (speed, dir, time, stunTime)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status == "Dead" or status == "Charge":
        return
    attr.set("Status", "Knockback")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Knockback")
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    if waypointMover:
        waypointMover.pause()
        prevSpeed = attr.get("Speed")
        attr.set("Speed", speed)
        timer.addTimer("Knockback timer", "Knockback end", 1, time, (prevSpeed, stunTime))
        mover.setDirectionAndMove(dir.normalized())
    else:
        prevSpeed = attr.get("Speed")
        attr.set("Speed", speed)
        timer.addTimer("Knockback timer", "Knockback end", 1, time, (prevSpeed, stunTime))
        mover.setDirectionAndMove(dir.normalized())


def knockbackEnd(entity, world, (prevSpeed, stunTime)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr.set("Status", "Idle")
    attr.set("Speed", prevSpeed)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Idle")
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    if stunTime > 0.0 and eventIO:
        eventIO.receiveEvent("Stun", stunTime)
    else:
        if mover:
            mover.stop()
            if waypointMover:
                waypointMover.unpause()



def healTargetHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    target = world.getEntityByID(attr.get("Target"))

    if target:
        effect = entity.getComponent(Enums.COMP_TYPE_EFFECT)
        effect.launchEffect("Heal", world, target)

    waypointMover.unpause()


def healStart(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)

    physicals = sensor.queryPhysicals(
        "Heal",
        world,
        lambda p: p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")) and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.getAttribute("Hitpoints") < p.entity.getAttribute("Hitpoints maximum") and
                  p.entity.getAttribute("Team") is attr.get("Team"))
    if len(physicals) > 0:
        target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
        attr.set("Target", target.id)
        timer.addTimer("Heal start timer", "Heal target", Enums.TIMER_ONCE, "Heal time")
        waypointMover.pause()
        world.networkCommand(Enums.WORLD_EVENT_HEAL_PERFORMED, target, entity)


def healHandler(entity, world, (heal, originator)):
    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if entity.isDestroyed() or attributes.get("Status") == "Dead":
        return
    if attributes:
        # send the network message in all cases so we get overheal info as well
        world.networkCommand(Enums.WORLD_EVENT_HEAL_RECEIVED, (heal, originator), entity)
        hitpoints = attributes.get("Hitpoints")
        maxHitpoints = attributes.get("Hitpoints maximum")
        if hitpoints >= maxHitpoints:
            return

        healCap = hitpoints + heal - maxHitpoints
        if healCap > 0.0:
            heal -= healCap

        heal = int(heal)
        attributes.inc("Hitpoints", heal)


def stealHealthStart(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr.set("Attack ready", True)
    if attr.get("Status") != "Combat":
        timer.removeTimer("Combat timer")
        return
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        attr.set("Attack ready", False)
        timer.addTimer("Attack start timer", "Attack", Enums.TIMER_ONCE, "Attack time", target.id)
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def stealHealthHandler(entity, world, targetID):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    target = world.getEntityByID(targetID)

    if target and combatAttr and eventIO:
        dmgMin = combatAttr.queryEffectiveAttribute("Damage minimum")
        dmgMax = combatAttr.queryEffectiveAttribute("Damage maximum")
        dmgType = attr.get("Damage type")
        pierceAmount = combatAttr.queryEffectiveAttribute("Pierce amount")
        damage = eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, target.id))
        if damage is None:
            return

        physicals = sensor.queryPhysicals(
            "Attack",
            world,
            lambda p: not p.entity.hasTag("Building") and
                      not p.entity.hasTag("Capturable") and
                      not p.entity.hasTag("Incorporeal") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.getAttribute("Hitpoints") < p.entity.getAttribute("Hitpoints maximum") and
                      p.entity.getAttribute("Team") is attr.get("Team"))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            eventIO.sendEvent(target, "Heal", (damage, entity.id))


def healingTotemEffect(entity, world, targets):
    if targets is None:
        return

    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    if isinstance(targets, list):
        for t in targets:
            if attributes and eventIO:
                damage = int(attributes.get("Damage") * (float(attributes.get("Level")) / 2))
                target = t
                eventIO.sendEvent(target, "Damage", (damage, "Magical", 0.0, entity.id))
                if attributes.get("Penetrate") is False:
                    world.destroyEntity(entity)
        return
    else:
        if attributes and eventIO:
            damage = int(attributes.get("Damage") * (float(attributes.get("Level")) / 2))
            target = targets
            eventIO.sendEvent(target, "Damage", (damage, "Magical", 0.0, entity.id))

            if attributes.get("Penetrate") is False:
                world.destroyEntity(entity)


def steamGranadeDamage(entity, world, targets):
    if targets is None:
        return

    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    if isinstance(targets, list):
        for t in targets:
            if attributes and eventIO:
                damage = int(attributes.get("Damage") * (float(attributes.get("Level")) / 2))
                target = t
                eventIO.sendEvent(target, "Damage", (damage, "Ranged", 0.0, entity.id))
                if attributes.get("Penetrate") is False:
                    world.destroyEntity(entity)
        return
    else:
        if attributes and eventIO:
            damage = int(attributes.get("Damage") * (float(attributes.get("Level")) / 2))
            target = targets
            eventIO.sendEvent(target, "Damage", (damage, "Ranged", 0.0, entity.id))

            if attributes.get("Penetrate") is False:
                world.destroyEntity(entity)
