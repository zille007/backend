import Enums
from utils import findClosestEntity


def gnomeAI(entity, world, args):
    """
    gnomeAI
    """
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")

    if status == "Idle":
        physicals = sensor.queryPhysicals(
            "Sight",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            attr.setMultiple((
                ("Status", "Target"),
                ("Target", target.id),
            ))
            waypointMover.pause()
            mover.setDestination(target.getPosition())
        elif waypointMover.hasWaypoint():
            attr.set("Status", "Moving")
            waypointMover.unpause()

    elif status == "Moving":
        physicals = sensor.queryPhysicals(
            "Sight",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            attr.setMultiple((
                ("Status", "Target"),
                ("Target", target.id),
            ))
            waypointMover.pause()
            mover.setDestination(target.getPosition())

    elif status == "Target":
        target = world.getEntityByID(attr.get("Target"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Sight", target):
            physicals = sensor.queryPhysicals(
                "Sight",
                world,
                lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                          p.entity.getAttribute("Status") != "Dead" and
                          p.entity.hasAllOfTags(attr.get("Target tags")) and
                          p.entity.hasNoneOfTags(attr.get("Ignore tags")))
            if len(physicals) > 0:
                target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
                attr.set("Target", target.id)
                mover.setDestination(target.getPosition())
            else:
                attr.setMultiple((
                    ("Status", "Idle"),
                    ("Target", Enums.NULL_ID),
                ))
        elif sensor.intersectsEntity("Attack", target):
            mover.stop()
            attr.set("Status", "Combat")
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            return
        else:
            mover.setDestination(target.getPosition())

    elif status == "Combat":
        target = world.getEntityByID(attr.get("Target"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Sight", target):
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
                    ("Status", "Target"),
                    ("Target", target.id),
                ))
                mover.setDestination(target.getPosition())
            else:
                attr.setMultiple((
                    ("Target", Enums.NULL_ID),
                    ("Status", "Idle"),
                ))
        elif sensor.intersectsEntity("Attack", target):
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            return
        elif sensor.intersectsEntity("Sight", target):
            attr.set("Status", "Target")
            mover.setDestination(target.getPosition())

    elif status == "Dead":
        pass

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    else:
        attr.set("Status", "Idle")


def gnomeIdleUpdate(entity, world, args):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    physicals = sensor.queryPhysicals(
        "Sight",
        world,
        lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")))
    if len(physicals) > 0:
        target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
        fsm.setState("Target")
        attr.set("Status", "Target")
        attr.set("Target", target.id)
        waypointMover.pause()
        mover.setDestination(target.getPosition())
    elif waypointMover.hasWaypoint():
        fsm.setState("Moving")
        attr.set("Status", "Moving")
        waypointMover.unpause()


def gnomeMovingUpdate(entity, world, args):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    physicals = sensor.queryPhysicals(
        "Sight",
        world,
        lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")))
    if len(physicals) > 0:
        target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
        fsm.setState("Target")
        attr.set("Status", "Target")
        attr.set("Target", target.id)
        waypointMover.pause()
        mover.setDestination(target.getPosition())


def gnomeTargetUpdate(entity, world, args):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Sight", target):
        physicals = sensor.queryPhysicals(
            "Sight",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            attr.set("Target", target.id)
            mover.setDestination(target.getPosition())
        else:
            fsm.setState("Idle")
            attr.set("Status", "Idle")
            attr.set("Target", Enums.NULL_ID)
    elif sensor.intersectsEntity("Attack", target):
        mover.stop()
        fsm.setState("Combat")
        attr.set("Status", "Combat")
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
        timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        return
    else:
        mover.setDestination(target.getPosition())


def gnomeCombatUpdate(entity, world, args):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Sight", target):
        physicals = sensor.queryPhysicals(
            "Attack",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            fsm.setState("Target")
            attr.set("Status", "Target")
            attr.set("Target", target.id)
            mover.setDestination(target.getPosition())
        else:
            fsm.setState("Idle")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Status", "Idle")
    elif sensor.intersectsEntity("Attack", target):
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        return
    elif sensor.intersectsEntity("Sight", target):
        fsm.setState("Target")
        attr.set("Status", "Target")
        mover.setDestination(target.getPosition())