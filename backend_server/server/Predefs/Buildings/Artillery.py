import Enums
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector


def artilleryIdleUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if attr.get("Status") == "Freeze":
        attr.set("Target", Enums.NULL_ID)

    physicals = sensor.queryPhysicals(
        "Attack",
        world,
        lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")))
    if len(physicals) > 0:
        target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
        attr.set("Status", "Combat")
        attr.set("Target", target.id)
        fsm.setState("Combat")
        if attr.get("Attack ready"):
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")


def artilleryCombatUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if attr.get("Status") == "Freeze":
        attr.set("Target", Enums.NULL_ID)

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        fsm.setState("Idle")
    elif not sensor.intersectsEntity("Attack", target):
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        fsm.setState("Idle")
    else:
        return


def artilleryBulletProcess(entity, world, args):
    """
    artilleryBulletProcess
    """
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if mover.atDestination():
        sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
        physicals = sensor.queryPhysicals(
            "Damage",
            world,
            lambda p: p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasTag("Targetable") and
                      p.entity.getAttribute("Team") is not attr.get("Team"))
        targets = map(lambda p: p.entity, physicals)
        dmgType = attr.get("Damage type")
        if dmgType is None:
            dmgType = "Ranged"
        armorPierce = attr.get("Armor pierce")
        if armorPierce is None:
            armorPierce = 0.0
        for t in targets:
            t.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Damage", (attr.get("Damage"), dmgType, armorPierce, entity.id))
        attr.set("Status", "Hit")
        world.destroyEntity(entity)


def artilleryBulletIdleUpdate(entity, world, args):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if mover.atDestination():
        sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
        physicals = sensor.queryPhysicals(
            "Damage",
            world,
            lambda p: p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasTag("Targetable") and
                      p.entity.getAttribute("Team") is not attr.get("Team"))
        targets = map(lambda p: p.entity, physicals)
        dmgMin = attr.get("Damage minimum")
        dmgMax = attr.get("Damage maximum")
        dmgType = attr.get("Damage type")
        pierceAmount = attr.get("Pierce amount")
        for t in targets:
            eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, t.id))
        entity.getComponent(Enums.COMP_TYPE_MOVER).stop()
        fsm.setState("Hit")
        attr.set("Status", "Hit")
        eventIO.receiveEvent("_destroy")


def artilleryAttackFirst(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        attr.set("Attack ready", False)
        timer.addTimer("Attack start timer", "Attack", Enums.TIMER_ONCE, "Attack time", target.getPosition())
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def artilleryAttackStart(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr.set("Attack ready", True)
    if attr.get("Status") != "Combat":
        timer.removeTimer("Combat timer")
        return
    target = world.getEntityByID(attr.get("Target"))
    if target is not None:
        attr.set("Attack ready", False)
        timer.addTimer("Attack start timer", "Attack", Enums.TIMER_ONCE, "Attack time", target.getPosition())
        world.networkCommand(Enums.WORLD_EVENT_ATTACK, target, entity)


def artilleryAttackHandler(entity, world, pos):
    attr = entity.getAttributes()

    dmgMin = attr.get("Damage minimum")
    dmgMax = attr.get("Damage maximum")
    dmgType = attr.get("Damage type")
    pierceAmount = attr.get("Pierce amount")
    bullet = world.createGameEntityForUser(
        "Artillery bullet",
        entity.getPosition(),
        (pos - entity.getPosition()).normalized(),
        attr.get("OwnerId"),
        (
            ("Team", attr.get("Team")),
            ("Damage minimum", dmgMin),
            ("Damage maximum", dmgMax),
            ("Damage radius", attr.get("Damage radius")),
            ("Damage type", dmgType),
            ("Pierce amount", pierceAmount),
            ("Speed", attr.get("Bullet speed")),
            ("Destination", pos.copy()),
            ("Originator", entity.id),
        )
    )
    if bullet is None:
        return

    bulletMover = bullet.getComponent(Enums.COMP_TYPE_MOVER)
    bulletMover.setDestination(pos.copy())


def upgradeArtillery(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    base = world.getBaseForTeamID(attr.get("Team"))
    if base is None:
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    baseLevel = base.getAttribute(("Stats", "Level"))
    maxLevel = min(baseLevel + 1, maxLevel)
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    attr.inc(("Stats", "Level"), 1)
    attr.inc("Damage minimum", 30)
    attr.inc("Damage maximum", 10)
    attr.inc("Damage radius", .1)
    attr.inc("Attack range", .2)
    attr.inc("Attack period", -.2)
    attr.inc("Hitpoints", 50)
    attr.inc("Hitpoints maximum", 50)

    level = attr.get(("Stats", "Level"))
    user = world.getUserForUnit(entity)
    #increases = world.getGemIncreasesForUser(user, level, level)
    #world.addIncreasesToBuilding(entity, increases)

    if attr.get( "Status" ) == "Upgrading":
        attr.set( "Status", "Idle" )

    world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADED, None, entity)
