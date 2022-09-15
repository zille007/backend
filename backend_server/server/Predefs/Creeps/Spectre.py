import Enums
from utils import findClosestEntity


def spectreAI(entity, world, args):
    """
    spectreAI
    """
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    status = attr.get("Status")

    if status == "Idle":
        if not mover.hasDestination():
            base = findClosestEntity(entity.getPosition(), filter(lambda e: e.getAttribute("Team") is not attr.get("Team"), world.getBases()))
            if base:
                mover.setDestination(base.getPosition())
        if mover.isMoving():
            attr.set("Status", "Moving")

    elif status == "Moving":
        physicals = sensor.queryPhysicals(
            "Attack",
            world,
            lambda p: p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasOneOfTags(attr.get("Option tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")) and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team") is not attr.get("Team"))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            attr.setMultiple((
                ("Status", "Combat"),
                ("Target", target.id),
            ))
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
            mover.stop()

    elif status == "Combat":
        target = world.getEntityByID(attr.get("Target"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
            physicals = sensor.queryPhysicals(
                "Attack",
                world,
                lambda p: p.entity.hasAllOfTags(attr.get("Target tags")) and
                          p.entity.hasOneOfTags(attr.get("Option tags")) and
                          p.entity.hasNoneOfTags(attr.get("Ignore tags")) and
                          p.entity.getAttribute("Status") != "Dead" and
                          p.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team") is not attr.get("Team"))
            if len(physicals) > 0:
                target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
                attr.set("Target", target.id)
            else:
                attr.setMultiple((
                    ("Target", Enums.NULL_ID),
                    ("Status", "Idle"),
                ))
        elif sensor.intersectsEntity("Attack", target):
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            return

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    else:
        attr.set("Status", "Idle")


def spectreIdleUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)

    if not mover.hasDestination():
        base = findClosestEntity(entity.getPosition(), filter(lambda e: e.getAttribute("Team") is not attr.get("Team"), world.getBases()))
        if base:
            mover.setDestination(base.getPosition())
    if mover.isMoving():
        fsm.setState("Moving")
        attr.set("Status", "Moving")


def spectreMovingUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)

    physicals = sensor.queryPhysicals(
        "Attack",
        world,
        lambda p: p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasOneOfTags(attr.get("Option tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")) and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team") is not attr.get("Team"))
    if len(physicals) > 0:
        target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
        fsm.setState("Combat")
        attr.set("Status", "Combat")
        attr.set("Target", target.id)
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
        mover.stop()


def spectreCombatUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
        physicals = sensor.queryPhysicals(
            "Attack",
            world,
            lambda p: p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasOneOfTags(attr.get("Option tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")) and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Team") is not attr.get("Team"))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            attr.set("Target", target.id)
        else:
            fsm.setState("Moving")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Status", "Moving")
            bases = filter(
                lambda b: b.getAttribute("Team") is not entity.getAttribute("Team"),
                world.getBases()
            )
            enemyBase = findClosestEntity(entity.getPosition(), bases)
            mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
            mover.setDestination(enemyBase.getPosition())
    elif sensor.intersectsEntity("Attack", target):
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        return