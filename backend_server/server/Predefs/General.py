import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector, clamp


def attackHandler(entity, world, targetID):
    """
    attackHandler enables an entity to perform an ordinary attack. The power and type of the attack is governed by the
    following attributes:

    - attr Damage minimum and Damage maximum define the range for the base damage.
    - attr Damage type defines the type of the attack. Can be either Melee, Ranged or Magical.
    - attr Pierce amount is the percentage how much damage goes unaffected by target armor. Value is between 0.0 and 1.0.

    If the given target is dead, the attribute Target is set to NULL_ID and no attack takes place. Also, if the attack
    performer has status Stunned, Knockback or Dead, nothing happens.

    - param targetID is the ID of the entity that is targeted by this attack.
    """
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status == "Stunned" or status == "Knockback" or status == "Dead" or entity.isDestroyed():
        return
    target = world.getEntityByID(targetID)
    if target is not None and not target.isDestroyed() and target.hasTag("Targetable") and world.queryLineOfSightForEntity(entity, target.getPosition()):
        combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
        eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
        eventIO.receiveImmediateEvent("Damage inflict", world, (
            combatAttr.get("Damage minimum"),
            combatAttr.get("Damage maximum"),
            attr.get("Damage type"),
            combatAttr.get("Pierce amount"),
            targetID)
        )
    else:
        attr.set("Target", Enums.NULL_ID)


def attackStart(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr.set("Attack ready", True)
    if attr.get("Status") != "Combat":
        timer.removeTimer("Combat timer")
        return
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        attr.set("Attack ready", False)
        if not timer.hasTimer("Attack start timer"):
            timer.addAnonymousTimer("Attack", Enums.TIMER_ONCE, "Attack time", target.id)
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def attackFirst(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        attr.set("Attack ready", False)
        if not timer.hasTimer("Attack start timer"):
            timer.addAnonymousTimer("Attack", Enums.TIMER_ONCE, "Attack time", target.id)
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def heroInit(entity, world, args):
    """
    This is a general init function for heroes. All heroes should have it and no one should leave home without it.
    """
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    eventIO.receiveEvent("Damage recalculate")
    str = attr.get("Stats.Strength")
    attr.inc("Hitpoints", str*2)
    attr.inc("Hitpoints maximum", str*2)


def damageRecalculate(entity, world, args):
    """
    This handler recalculates total damage. It adds bonuses from stats.
    """
    attr = entity.getAttributes()
    damageType = attr.get("Damage type")
    damageBonus = 0
    if damageType == "Melee":
        damageBonus = attr.get("Stats.Strength")/2
    elif damageType == "Ranged":
        damageBonus = attr.get("Stats.Dexterity")/2
    elif damageType == "Magical":
        damageBonus = attr.get("Stats.Intelligence")/2
    damageTotalMinimum = int(attr.get("Damage minimum") + damageBonus)
    damageTotalMaximum = max(int(attr.get("Damage maximum") + damageBonus), damageTotalMinimum)
    attr.set("Damage total minimum", damageTotalMinimum)
    attr.set("Damage total maximum", damageTotalMaximum)


def spawnRandomItem(entity, world, args):
    width = world.width
    height = world.height
    x = random.random()*(width-2) + 1
    y = random.random()*(height-2) + 1
    i = 0
    while world.map.getGridNodeByWorldPos(Vector3(x, y))[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT] > 0.5:
        x = random.random()*(width-2) + 1
        y = random.random()*(height-2) + 1
        i += 1
        if i > 100:
            break
    itemList = list(entity.getAttribute("Item list"))
    if len(itemList) > 0:
        itemidx = random.randint(0, len(itemList)-1)
        item = itemList.pop(itemidx)
        entity.setAttribute("Item list", tuple(itemList))
        e = world.createGameEntity(item, Vector3(x, y), Vector3(1, 0, 0))
        e.setAttribute("Match item", True)


def damageInflict(entity, world, (baseDamageMin, baseDamageMax, dmgType, pierceAmount, targetID)):
    """
    damageInflict enables an entity to send correctly calculated damage events to other entities.
    This handler takes care of damage calculus automatically. It applies bonuses from
    Strength, Dexterity and Intelligence depending on the damage type. If the damage dealing
    entity is not the caster itself, but rather a proxy entity, such as a projectile, it
    probably has the Originator-attribute, which is used to look up the entity that created
    the proxy.

    - param baseDamageMin and baseDamageMax define the bounds for the base damage power.
    - param dmgType is the damage type, which can be either Melee, Ranged or Magical.
        Melee damage gets a bonus from Strength, Ranged from Dexterity and Magical from Intelligence.
    - param pierceAmount is a value between 0.0 and 1.0. It is the percentage how much of the damage will bypass armor.
    - param targetID is the ID of the target entity.
    """
    target = world.getEntityByID(targetID)
    if target is None:
        return


    attr = entity.getAttributes()
    originator = world.getEntityByID(attr.get("Originator"))

    # a good damage debug output spam
    #world.logInfo( "%s deals %d-%d damage to %s %s (%4.2f armor pierced)" %
    #               (entity.getName(), baseDamageMin, baseDamageMax, target.getName(),
    #                "(originator %s)" % (originator.getName(),) if originator is not None else "",
    #                pierceAmount))
    if originator and not originator.isDestroyed():
        combatAttr = originator.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    else:
        combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
    targetEventIO = target.getComponent(Enums.COMP_TYPE_EVENTIO)
    if combatAttr and targetEventIO:
        baseDamageMax = int(max(baseDamageMin, baseDamageMax))
        baseDamageMin = int(baseDamageMin)

        if dmgType is None:
            dmgType = "Melee"

        if pierceAmount is None:
            pierceAmount = 0.0

        if dmgType == "Melee":
            strength = combatAttr.queryEffectiveAttribute(("Stats", "Strength"))
            damage = random.randint(baseDamageMin, baseDamageMax) + (strength/2 if strength else 0)
        elif dmgType == "Ranged":
            dexterity = combatAttr.queryEffectiveAttribute(("Stats", "Dexterity"))
            damage = random.randint(baseDamageMin, baseDamageMax) + (dexterity/2 if dexterity else 0)
        elif dmgType == "Magical":
            intelligence = combatAttr.queryEffectiveAttribute(("Stats", "Intelligence"))
            damage = random.randint(baseDamageMin, baseDamageMax) + (intelligence/2 if intelligence else 0)

        damageTokens = attr.get("Damage tokens")
        if damageTokens is not None and len(damageTokens) > 0:
            damage *= damageTokens.pop()
            attr.set("Damage tokens", damageTokens)

        targetEventIO.receiveEvent("Damage", (damage, pierceAmount, entity.id, originator.id if originator else None))
        return damage
    return


def damageHandler(entity, world, (damage, pierceAmount, originatorID, origCreatorID)):
    """
    damageHandler enables an entity to receive and process damage events.

    - param damage is the amount of damage received.
    - param pierceAmount is a value between 0.0 and 1.0. It is the percentage how much damage bypasses armor.
    - param originatorID is the ID of the target entity.
    """
    if entity.getAttribute("Status") == "Dead":
        return
    attr = entity.getAttributes()
    if attr:
        armor = attr.get("Stats.Armor")
        if pierceAmount is not None:
            pierceAmount = clamp(pierceAmount, 0.0, 1.0)
            armor *= (1.0 - pierceAmount)
        originator = world.getEntityByID(originatorID)

        damage -= int(armor)
        if damage <= 0:
            damage = 1

        # check for smoke; cause miss (damage=0) if:
        # - target or originator is in smoke and originator does not ignore smoke
        if originator is not None and not originator.hasTag("Ignores smoke"):
            if originator.hasTag("In smoke") or entity.hasTag("In smoke"):
                damage = 0

        if entity.hasTag("Damage shielded"):
            dmgShieldCap = attr.get("Abilities.Damage shield.Capacity")
            dmgAbsorbed = attr.get("Abilities.Damage shield.Damage absorbed")

            dmgOver = damage + dmgAbsorbed - dmgShieldCap
            if dmgOver >= 0:
                attr.set("Abilities.Damage shield.Damage absorbed", dmgShieldCap)
                entity.receiveEvent("Damage shield end")
                damage -= dmgOver
            else:
                attr.inc("Abilities.Damage shield.Damage absorbed", damage)
                damage = 0
            # TODO: feedback fx on absorbed damage?

        hitpoints = attr.get("Hitpoints")
        if hitpoints - damage <= 0:
            attr.set("Hitpoints", 0)
        else:
            attr.inc("Hitpoints", -damage)
        if originator and originator.hasTag("Hero"):
            mana = attr.get("Mana reward")
            if mana:
                originator.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Mana", mana)
        world.networkCommand(Enums.WORLD_EVENT_DAMAGE, (damage, originator), entity)

        if entity.hasTag( "Hero" ):
            world.getMatch().playerStatIncEvent( "total_damage_in",entity.getAttribute( "Username" ), damage )
        if originator and originator.hasTag( "Hero" ):
            world.getMatch().playerStatIncEvent( "total_damage_out", originator.getAttribute( "Username" ), damage )


        if attr.get("Hitpoints") <= 0:
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Death", originatorID)

        tags = entity.getComponent(Enums.COMP_TYPE_TAGS)

        if tags.has("Hero") and damage > 0:
            # break any hero healing effect on damage
            timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
            if timer is not None:
                t = timer.getTimer("Hero heal timer")
                if t is not None:
                    t[Enums.TIMER_TRIGGER_LIMIT] = 0
                    # TODO: feedback fx?


def deathHandler(entity, world, originatorID):
    """
    deathHandler makes it possible for entities to die. This can happen due to damage or due to anything, really.
    Upon death, the entity sends experience to nearby enemy heroes and gives a mana reward.

    - param originatorID is the ID of the entity that caused the death. Can be NULL_ID or None, if no one is responsible.
    """
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    xpReward = attr.get("Experience reward")
    honorReward = attr.get("Honor reward")
    manaReward = attr.get("Mana reward")
    teamEntity = world.getTeamEntity(attr.get("Team"))
    teamAttr = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    home = world.getEntityByID(attr.get("Home"))
    if home:
        home.receiveEvent("Defender death")

    subtype = attr.get("Subtype")
    # actually why not if hasattr( "Defenders" ) )?
    if subtype == "Goblin ancestor" or subtype == "Pond dragon" or subtype == "Thunderwell" or subtype == "Watch tower":
        defenders = attr.get("Defenders")
        for d in defenders:
            if d is not None and not d.isDestroyed() and d.getAttribute("Status") != "Dead":
                d.receiveEvent("Death", entity.id)

    if entity.hasComponent(Enums.COMP_TYPE_SENSOR):
        physicals = entity.getComponent(Enums.COMP_TYPE_SENSOR).queryPhysicals(
            "Experience",
            world,
            lambda p: p.entity.hasTag("Hero") and p.entity.getAttribute("Team") is not entity.getAttribute("Team")
        )
        heroes = map(lambda p: p.entity, physicals)
        if xpReward:
            eventIO.sendEvent(heroes, "Experience", xpReward)
        if manaReward:
            eventIO.sendEvent(heroes, "Mana", manaReward)

    killer = world.getEntityByID(originatorID)
    if killer and killer.hasTag("Hero"):
        eventIO.sendEvent(killer, "Experience", xpReward)
        if manaReward:
            eventIO.sendEvent(killer, "Mana", manaReward)
        eventIO.sendEvent(killer, "Last hit", attr.get("Hitpoints maximum"))
        killer.getComponent( Enums.COMP_TYPE_EVENTIO ).receiveEvent( "Last hit", attr.get("Hitpoints maximum") )
        #world.logInfo( "Death of %s; killer %s" % (entity.getName(), killer.getName()))
        world.networkCommand(Enums.WORLD_EVENT_LAST_HIT, entity, world.getEntityByID(originatorID))
    if killer:
        killerTeam = world.getTeamEntity(killer.getAttribute("Team"))
        if killerTeam and honorReward:
            killerTeam.getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(("Resources", "Gold"), honorReward)

        if entity.hasTag("Creep"):
            world.getMatch().playerStatIncEvent( "creep_kills", killer.getAttributes().get("Username"), 1 )

    attr.set("Status", "Dead")
    if entity.hasTag("Building"):
        physicals = world.queryPhysicalsByPoint(entity.getPosition(), lambda p: p.entity.getAttribute("Subtype") == "Building slot")
        if len(physicals) > 0:
            slots = map(lambda p: p.entity, physicals)
            slot = findClosestEntity(entity.getPosition(), slots)
            slotAttr = slot.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            slotAttr.set("Status", "Open")
        if entity.getAttribute("Subtype") == "Barracks":
            teamAttr.inc(("Units", "Northerners", "Barracks", "Count"), -1)
        elif entity.getAttribute("Subtype") == "Battlestump":
            teamAttr.inc(("Units", "Fay", "Battlestump", "Count"), -1)

    world.destroyEntity(entity)
    world.networkCommand(Enums.WORLD_EVENT_ENTITY_DEATH, (originatorID,), entity)


def neutralBossDeathHandler(entity, world, originatorID):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    xpReward = attr.get("Experience reward")
    honorReward = attr.get("Honor reward")

    if xpReward and entity.hasComponent(Enums.COMP_TYPE_SENSOR):
        physicals = entity.getComponent(Enums.COMP_TYPE_SENSOR).queryPhysicals(
            "Experience",
            world,
            lambda p: p.entity.hasTag("Hero") and p.entity.getAttribute("Team") is not entity.getAttribute("Team")
        )
        heroes = map(lambda p: p.entity, physicals)
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).sendEvent(heroes, "Experience", xpReward)
    killer = world.getEntityByID(originatorID)
    if killer:
        killerTeam = world.getTeamEntity(killer.getAttribute("Team"))
        if killerTeam and honorReward:
            killerTeam.getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(("Resources", "Gold"), honorReward)
    attr.set("Status", "Dead")
    dropList = entity.getAttribute("Item drop list")
    item = dropList[random.randint(0, len(dropList)-1)]
    world.createGameEntity(item, entity.getPosition(), entity.getDirection())
    world.destroyEntity(entity)
    world.networkCommand(Enums.WORLD_EVENT_ENTITY_DEATH, None, entity)


def heroDeathHandler(entity, world, originatorID):
    entity.getComponent(Enums.COMP_TYPE_MOVER).stop()
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    world.getMatch().playerStatIncEvent( "deaths", attr.get("Username"), 1 )

    xpReward = attr.get("Experience reward")
    honorReward = attr.get("Honor reward")
    if xpReward and entity.hasComponent(Enums.COMP_TYPE_SENSOR):
        physicals = entity.getComponent(Enums.COMP_TYPE_SENSOR).queryPhysicals(
            "Experience",
            world,
            lambda p: p.entity.hasTag("Hero") and p.entity.getAttribute("Team") is not entity.getAttribute("Team")
        )
        heroes = map(lambda p: p.entity, physicals)
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).sendEvent(heroes, "Experience", xpReward)
    killer = world.getEntityByID(originatorID)
    if killer and killer.hasTag("Hero"):
        manaReward = attr.get("Mana reward")
        eio = entity.getComponent( Enums.COMP_TYPE_EVENTIO )
        eio.sendEvent(killer, "Last hit", attr.get("Hitpoints maximum") )
        eio.sendEvent(killer, "Mana", manaReward)
        world.networkCommand(Enums.WORLD_EVENT_LAST_HIT, entity, world.getEntityByID(originatorID))
    if killer:
        #world.logInfo( "Hero entity id %d dies, killer %s" % (entity.id, killer.getName()))
        killerTeam = world.getTeamEntity(killer.getAttribute("Team"))
        if killerTeam and honorReward:
            killerTeam.getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(("Resources", "Gold"), honorReward)
        if killer.hasTag("Hero"):
            world.getMatch().playerStatIncEvent( "kills", killer.getAttributes().get("Username"), 1 )
        elif killer.getAttribute( "Originator" ) is not None:
            originator_id = killer.getAttribute( "Originator" )
            origin_entity = world.getEntityByID( originator_id )
            if origin_entity is not None and origin_entity.hasTag( "Hero" ):
                world.getMatch().playerStatIncEvent( "kills", origin_entity.getAttributes().get("Username"), 1 )
    else:
        #world.logInfo( "Hero entity id %d dies (no killer)." % (entity.id,))
        pass


    attr.set("Status", "Dead")
    fsm.setState("Dead")
    fsm.setUpdatePeriod(1.0)
    attr.set("Target selected", Enums.NULL_ID)

    world.networkCommand(Enums.WORLD_EVENT_ENTITY_DEATH, (originatorID,), entity)
    timer.removeTimer("Combat timer")
    timer.addTimer("Respawn timer", "Respawn", Enums.TIMER_ONCE, "Respawn time")
    timer.addTimer("Teleport timer", "Teleport", Enums.TIMER_ONCE, 1.0, world.getBaseForTeamID(attr.get("Team")).getPosition())


def teleportHandler(entity, world, pos):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    mover.teleport(pos)


def heroAbilityHandler(entity, world, (name, pos, targetID)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status.split(" ")[0] == "Casting":
        return
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    type = attr.get(("Abilities", name, "Type"))
    cost = attr.get(("Abilities", name, "Cost"))
    ready = attr.get(("Abilities", name, "Ready"))
    mana = attr.get("Mana")
    if cost <= mana and ready:
        cooldown = attr.get(("Abilities", name, "Cooldown"))
        casttime = attr.get(("Abilities", name, "Casting time"))

        if casttime is None or casttime == 0.0:
            # automatically trigger
            world.networkAbilityImmediateSuccess(name, entity)
            if type == "Position":
                range = attr.get(("Abilities", name, "Range"))
                if (entity.getPosition() - pos).magnitude_squared() > range**2:
                    return
                eventIO.receiveEvent(name, pos)
            elif type == "Target":
                range = attr.get(("Abilities", name, "Range"))
                target = world.getEntityByID(targetID)
                if target is None:
                    return
                targetType = attr.get(("Abilities", name, "Target type"))
                if targetType == "Enemy" and target.getAttribute("Team") is attr.get("Team"):
                    return
                elif targetType == "Friendly" and target.getAttribute("Team") is not attr.get("Team"):
                    return
                pos = target.getPosition()
                if (entity.getPosition() - pos).magnitude_squared() > range**2:
                    return
                eventIO.receiveEvent(name, targetID)
            elif type == "Active":
                eventIO.receiveEvent(name)
        else:
            mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
            waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
            if waypointMover:
                waypointMover.clearWaypoints()
            mover.stop()
            # set up timer to launch the ability properly
            if type == "Position":
                range = attr.get(("Abilities", name, "Range"))
                if (entity.getPosition() - pos).magnitude_squared() > range**2:
                    return
                timer.addTimer(name + " casting timer", name, Enums.TIMER_ONCE, casttime, pos)
            elif type == "Target":
                range = attr.get(("Abilities", name, "Range"))
                target = world.getEntityByID(targetID)
                if target is None:
                    return
                targetType = attr.get(("Abilities", name, "Target type"))
                if targetType == "Enemy" and target.getAttribute("Team") is attr.get("Team"):
                    return
                elif targetType == "Friendly" and target.getAttribute("Team") is not attr.get("Team"):
                    return
                pos = target.getPosition()
                if (entity.getPosition() - pos).magnitude_squared() > range**2:
                    return
                timer.addTimer(name + " casting timer", name, Enums.TIMER_ONCE, casttime, targetID)
            elif type == "Active":
                timer.addTimer(name + " casting timer", name, Enums.TIMER_ONCE, casttime)
            attr.set("Status", "Casting " + name)
            fsm.setState("Casting")
            world.networkCommand(Enums.WORLD_EVENT_CAST_STARTED, (name, casttime), entity)

        if attr.get(("Abilities", name, "Costless")):
            attr.set(("Abilities", name, "Costless"), False)
        else:
            attr.inc("Mana", -cost)
            attr.set(("Abilities", name, "Ready"), False)
            timer.addTimer(name + " ability timer", "Ability ready", Enums.TIMER_ONCE, cooldown, name)


def heroAbilityLaunchHandler(entity, world, args):
    pass


def heroAbilityCancelHandler(entity, world, args):
    pass


def heroAbilityUpgradeHandler(entity, world, name):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    skillPoints = attr.get(("Stats", "Skill points"))
    abilLevel = attr.get(("Abilities", name, "Level"))
    levelMax = attr.get(("Abilities", name, "Level maximum"))
    if skillPoints > 0 and abilLevel < levelMax:
        attr.inc(("Stats", "Skill points"), -1)
        attr.inc(("Abilities", name, "Level"), 1)
        attr.applyMultiple(attr.get(("Abilities", name, "Upgrade increases", "Level " + str(abilLevel + 1))))
        attr.set("Previously upgraded ability", name)


def heroLevelUpHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Stats", "Level"), 1)
    attr.inc(("Stats", "Skill points"), 1)
    oldStr = attr.get("Stats.Strength")
    attr.applyMultiple(attr.get("Stats.Level up increases.Level " + str(attr.get("Stats.Level"))))
    world.getMatch().playerStatAssignEvent( "level", attr.get("Username"), attr.get(("Stats","Level") ) )
    userEntity = world.getUserEntity(attr.get("Username"))
    if userEntity:
        userInstance = userEntity.getAttribute("User instance")
        heroLevel = attr.get(("Stats", "Level"))
        increases = world.getItemIncreasesForUser(userInstance, heroLevel, heroLevel)
        if increases:
            world.addIncreasesToHero(entity, increases)
    newStr = attr.get("Stats.Strength")
    hpInc = (newStr - oldStr)*2
    if hpInc > 0:
        attr.inc("Hitpoints", hpInc)
        attr.inc("Hitpoints maximum", hpInc)
    entity.receiveEvent("Damage recalculate")


def respawnHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)

    attr.set("Status", "Idle")
    fsm.setState("Idle")
    fsm.setUpdatePeriod(0.0)
    attr.set("Hitpoints", attr.get("Hitpoints maximum"))
    attr.set("Target", Enums.NULL_ID)
    attr.set("Target selected", Enums.NULL_ID)
    attr.inc("Respawn time", 2)
    attr.set("Mana", attr.get("Mana maximum"))
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if fsm:
        fsm.setState("Idle")
    mid_dir = -((xform.position - world.getMapMidpoint()).normalized())
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    mover.setDestination(xform.position + mid_dir * 3.0)
    entity.receiveEvent("Damage recalculate")
    world.networkCommand(Enums.WORLD_EVENT_ENTITY_RESPAWN, None, entity)


def moveHandler(entity, world, destination):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat" and status != "Carry":
        return
    if attr.get("State") == "Dead":
        return
    attr.set("Target selected", Enums.NULL_ID)

    if entity.hasTag( "AI Controlled"):
        moveHandlerWithGeometryAvoidance( entity, world, destination )
        return

    if isinstance(destination, Vector3):
        path = world.findLineAvoidBuildings(entity.getPosition(), destination.copy())
        waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
        if len(path) > 1:
            waypointMover.setWaypoints(path)
            return
        waypointMover.clearWaypoints()
        mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
        mover.setDestination(destination)
    else:
        waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
        waypointMover.setWaypoints(destination)

def moveHandlerWithGeometryAvoidance( entity, world, destination ):
    attr = entity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    status = attr.get( "Status" )
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat" and status != "Carry":
        return
    if attr.get("State") == "Dead":
        return
    attr.set("Target selected", Enums.NULL_ID)

    #world.logInfo( "%s moving with geometry avoidance..." % (entity.getName(),))

    if isinstance(destination, Vector3):
        mapnodes = world.map.rayCast( entity.getPosition(), destination.copy() )
        mustPathFind = False
        oldHeight = 0.0
        newHeight = 0.0
        for n in mapnodes:
            world.logInfo(n)
            newHeight = n[1][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
            if abs(newHeight - oldHeight) > .75:
                mustPathFind = True
                break
            oldHeight = newHeight
        if mustPathFind:
            #world.logInfo( "Geometry avoidance must pathfind...")
            path = world.findPath( entity.getPosition(), destination.copy() )
            waypointMover = entity.getComponent( Enums.COMP_TYPE_WAYPOINTMOVER )
            waypointMover.setWaypoints( path )
        else:
            #world.logInfo( "Geometry avoidance NOT pathfinding...")
            path = world.findLineAvoidBuildings(entity.getPosition(), destination.copy())
            waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
            if len(path) > 1:
                waypointMover.setWaypoints(path)
                return
            waypointMover.clearWaypoints()
            mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
            mover.setDestination(destination)
    else:
        waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
        waypointMover.setWaypoints(destination)

def stopHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat":
        return
    attr.set("Target selected", Enums.NULL_ID)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    waypointMover.clearWaypoints()
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    mover.stop()


def targetHandler(entity, world, targetID):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if targetID is Enums.NULL_ID or attr.get("Status") == "Dead":
        return
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    waypointMover.clearWaypoints()
    target = world.getEntityByID(targetID)
    if target and target.getAttribute("Team") is not attr.get("Team") and target.hasAllOfTags(attr.get("Target tags")) and target.hasNoneOfTags(attr.get("Ignore tags")):
        attr.set("Target selected", targetID)
        if attr.get("Status") == "Combat":
            attr.set("Target", targetID)


def experienceHandler(entity, world, xp):
    if xp is None:
        return
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Stats", "Experience"), xp)
    attr.inc(("Stats", "Experience total"), xp)
    world.getMatch().playerStatIncEvent( "total_experience", attr.get("Username"), xp )
    if attr.get(("Stats", "Experience")) >= attr.get(("Stats", "Next level")):
        attr.inc(("Stats", "Experience"), -attr.get(("Stats", "Next level")))
        if attr.get("Stats.Level") < attr.get("Stats.Level maximum"):
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveImmediateEvent("Level up", world)


def basicItemPickupHandler(entity, world, heroID):
    hero = world.getEntityByID(heroID)
    if hero and not hero.isDestroyed() and hero.getAttribute("Status") != "Dead":
        attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        attr.set("Status", "Picked up")
        time = attr.get("Time")
        effectType = attr.get("Effect type")
        increases = attr.get("Increases")
        multipliers = attr.get( "Multipliers" )
        itemtype = attr.get("Subtype")
        sets = attr.get("Sets")
        if multipliers:
            for m in multipliers.l:
                hero.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Buff", (m[0], m[1], Enums.ATTR_MUL, effectType, time))

        if increases:
            for i in increases.l:
                hero.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Buff", (i[0], i[1], Enums.ATTR_INC, effectType, time))
        if sets:
            for s in sets.l:
                hero.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Buff", (s[0], s[1], Enums.ATTR_SET, effectType, time))
        world.networkCommand(Enums.WORLD_EVENT_ITEM_PICKUP, itemtype, hero)
        world.destroyEntity(entity)

        # add back to match item list if a match item
        if attr.has( "Match item" ) and attr.get( "Match item" ) == True:
            match = world.getMatchEntity()
            match_attr = match.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
            items = match_attr.get( "Item list" )
            items += ( attr.get("Subtype"), )
            match_attr.set( "Item list", items )



def heroPickupChecker(entity, world, args):
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)

    items = sensor.queryPhysicals(
        "Pick up",
        world,
        lambda p: p.entity.getAttribute("Type") == "Item"
    )
    for i in items:
        i.entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Pick up", entity.id)


def startUpgrade( entity, world, args ):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    base = world.getBaseForTeamID(attr.get("Team"))
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    baseLevel = base.getAttribute(("Stats", "Level"))
    maxLevel = min(baseLevel + 1, maxLevel)
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    gold = teamAttr.get(("Resources", "Gold"))
    cost = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Upgrade cost"))
    time = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Upgrade time"))
    if gold >= cost:
        teamAttr.inc(("Resources", "Gold"), -cost)
        timer = entity.getComponent( Enums.COMP_TYPE_TIMER )
        timer.addTimer( "Upgrade timer", "Upgrade", Enums.TIMER_ONCE, time, None )
        attr.set( "Status", "Upgrading" )
        world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADING, time, entity)


def repairHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status == "Dead" or status == "Sold" or status == "Building" or status == "Upgrading":
        #world.logInfo( "Will ingore repair request on entity %s (status %s)" % (entity.getName(), status) )
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    gold = teamAttr.get(("Resources", "Gold"))
    cost = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Repair cost"))
    if gold >= cost and attr.get("Hitpoints") < attr.get("Hitpoints maximum"):
        teamAttr.inc(("Resources", "Gold"), -cost)
        attr.set("Hitpoints", attr.get("Hitpoints maximum"))


def sellHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status == "Dead" or status == "Sold" or status == "Building" or status == "Upgrading":
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    priceFactor = .5*(float(attr.get("Hitpoints")) / float(attr.get("Hitpoints maximum")))
    sellPrice = int(teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Cost"))*priceFactor)
    teamAttr.inc(("Resources", "Gold"), sellPrice)
    attr.set("Status", "Sold")

    physicals = world.queryPhysicalsByPoint(entity.getPosition(), lambda p: p.entity.getAttribute("Subtype") == "Building slot")
    if len(physicals) > 0:
        slots = map(lambda p: p.entity, physicals)
        slot = findClosestEntity(entity.getPosition(), slots)
        slotAttr = slot.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        slotAttr.set("Status", "Open")
    if entity.getAttribute("Subtype") == "Barracks":
        teamAttr.inc(("Units", "Northerners", "Barracks", "Count"), -1)
    elif entity.getAttribute("Subtype") == "Battlestump":
        teamAttr.inc(("Units", "Fay", "Battlestump", "Count"), -1)

    world.destroyEntity(entity)
    world.networkCommand(Enums.WORLD_EVENT_ENTITY_SELL, None, entity)


def buildingReady(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    attr.set("Status", "Idle")
    if fsm:
        fsm.setState("Idle")

    if attr.has("Rally point"):
        xform = entity.getComponent( Enums.COMP_TYPE_TRANSFORM )
        dist = attr.get( "Rally range" ) / 1.5
        base = world.getBaseForTeamID( attr.get( "Team" ) )
        if base is not None:
            base_xform = base.getComponent( Enums.COMP_TYPE_TRANSFORM )
            basedir = (xform.position - base_xform.position).normalized()
            subtype = attr.get("Subtype")
            base_rally = xform.position + (basedir * dist) * (0.0 if subtype == "Watch tower" or subtype == "Nymph ancestor" or subtype == "Pond dragon" else 1.0)
            attr.set( "Rally point", base_rally )

    if entity.hasTag("Defender"):
        entity.receiveEvent("Spawn")
    world.networkCommand(Enums.WORLD_EVENT_BUILDING_READY, None, entity)


def buildHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    attr.set("Status", "Building")
    if fsm:
        fsm.setState("Building")
    teamEntity = world.getTeamEntity(attr.get("Team"))
    buildingTime = teamEntity.getAttribute(("Units", attr.get("Faction"), attr.get("Subtype"), "Building time"))
    timer.addTimer("Building timer", "Ready", Enums.TIMER_ONCE, buildingTime)
    world.networkCommand(Enums.WORLD_EVENT_BUILDING, buildingTime, entity)


def startWave(entity, world, args):
    interval = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Wave interval")
    world.broadcastEvent("Wave", interval)
    world.networkCommand(Enums.WORLD_EVENT_START_WAVE, interval, entity)


def waveTick(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    if attr.get( "Wave timer active") == False:
        return

    attr.inc("Wave timer counter", -1)
    if attr.get("Wave timer counter") <= 0:
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Start wave")
        attr.set("Wave timer counter", attr.get("Wave interval"))


def waveHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get("Status") == "Building" or attr.get("Status") == "Upgrading":
        return
    attr.set("Queue index", 0)
    entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Spawn timer", "Spawn", Enums.TIMER_INFINITE, "Spawn period")


def manaHandler(entity, world, amount):
    attr = entity.getAttributes()
    if entity.isDestroyed() or attr.get("Status") == "Dead":
        return
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    regenPeriod = attr.get("Mana regenerate period") - (attr.get(("Stats", "Intelligence"))*.02)
    timer.addTimer("Mana timer", "Mana", -1, regenPeriod)
    if amount is None:
        amount = 1
    manaFactor = attr.get("Mana factor")
    if manaFactor:
        amount *= manaFactor
        amount = int(amount)
    attr.inc("Mana", amount)
    if attr.get("Mana") > attr.get("Mana maximum"):
        attr.set("Mana", attr.get("Mana maximum"))


def healthHandler(entity, world, amount):
    attr = entity.getAttributes()
    if entity.isDestroyed() or attr.get("Status") == "Dead":
        return
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    regenPeriod = attr.get("Health regenerate period") - (attr.get("Stats.Strength")*.05)
    timer.addTimer("Health timer", "Health", -1, regenPeriod)
    if amount is None:
        amount = 1
    attr.inc("Hitpoints", amount)
    if attr.get("Hitpoints") > attr.get("Hitpoints maximum"):
        attr.set("Hitpoints", attr.get("Hitpoints maximum"))