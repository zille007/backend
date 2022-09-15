import Enums
from utils import findClosestEntity


def summonAI( entity, world, args ):
    """
    Aggression AI that uses a single summon location for aggression radius
    """
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    status = attr.get("Status")

    aggro_center_attr = "Rally point"
    aggro_radius_attr = "Sight range"

    if status == "Idle":
        physicals = sensor.queryPhysicals(
            "Attack",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        # add physicals from rally point
        physicals += world.queryPhysicalsByCircle(attr.get(aggro_center_attr), attr.get(aggro_radius_attr),
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
            return
        if not mover.atPosition(attr.get("Rally point")):
            mover.setDestination(attr.get("Rally point"))
        return

    elif status == "Target":
        target = world.getEntityByID(attr.get("Target"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
            physicals = world.queryPhysicalsByCircle(attr.get(aggro_center_attr), attr.get(aggro_radius_attr),
                                                     lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                                                               p.entity.getAttribute("Status") != "Dead" and
                                                               p.entity.hasAllOfTags(attr.get("Target tags")) and
                                                               p.entity.hasNoneOfTags(attr.get("Ignore tags")))
            if len(physicals) > 0:
                target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
                attr.set("Target", target.id)
                mover.setDestination(target.getPosition())
                return
            attr.setMultiple((
                ("Status", "Idle"),
                ("Target", Enums.NULL_ID),
            ))
            return
        elif sensor.intersectsEntity("Attack", target):
            mover.stop()
            attr.set("Status", "Combat")
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            return
        elif target in world.queryEntitiesByCircle( attr.get( aggro_center_attr ), attr.get( aggro_radius_attr ) ):
            mover.setDestination(target.getPosition())
            return
        attr.setMultiple((
            ("Status", "Idle"),
            ("Target", Enums.NULL_ID),
        ))
        return

    elif status == "Combat":
        target = world.getEntityByID(attr.get("Target"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
            physicals = sensor.queryPhysicals(
                "Attack",
                world,
                lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                          p.entity.getAttribute("Status") != "Dead" and
                          p.entity.hasAllOfTags(attr.get("Target tags")) and
                          p.entity.hasNoneOfTags(attr.get("Ignore tags")))
            physicals += world.queryPhysicalsByCircle(attr.get(aggro_center_attr), attr.get(aggro_radius_attr),
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
                return
            else:
                attr.setMultiple((
                    ("Target", Enums.NULL_ID),
                    ("Status", "Idle"),
                ))
        elif sensor.intersectsEntity("Attack", target):
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            return
        elif target in world.queryEntitiesByCircle(attr.get(aggro_center_attr), attr.get(aggro_radius_attr)):
            mover.setDestination(target.getPosition())
            return
        attr.setMultiple((
            ("Target", Enums.NULL_ID),
            ("Status", "Idle"),
        ))
        return

    elif status == "Dead":
        return

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    attr.set("Status", "Idle")
    return


def summonIdleUpdate(entity, world, args):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    aggro_center_attr = "Rally point"
    aggro_radius_attr = "Sight range"

    physicals = sensor.queryPhysicals(
        "Attack",
        world,
        lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.hasAllOfTags(attr.get("Target tags")) and
                  p.entity.hasNoneOfTags(attr.get("Ignore tags")))
    # add physicals from rally point
    physicals += world.queryPhysicalsByCircle(
        attr.get(aggro_center_attr),
        attr.get(aggro_radius_attr),
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
        return
    if not mover.atPosition(attr.get("Rally point")):
        mover.setDestination(attr.get("Rally point"))


def summonTargetUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    aggro_center_attr = "Rally point"
    aggro_radius_attr = "Sight range"

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
        physicals = world.queryPhysicalsByCircle(
            attr.get(aggro_center_attr),
            attr.get(aggro_radius_attr),
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        if len(physicals) > 0:
            target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
            attr.set("Target", target.id)
            mover.setDestination(target.getPosition())
            return
        fsm.setState("Idle")
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        return
    elif sensor.intersectsEntity("Attack", target):
        mover.stop()
        fsm.setState("Combat")
        attr.set("Status", "Combat")
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
        timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        return
    elif target in world.queryEntitiesByCircle(attr.get(aggro_center_attr), attr.get(aggro_radius_attr)):
        mover.setDestination(target.getPosition())
        return
    fsm.setState("Idle")
    attr.set("Status", "Idle")
    attr.set("Target", Enums.NULL_ID)


def summonCombatUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    aggro_center_attr = "Rally point"
    aggro_radius_attr = "Sight range"

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
        physicals = sensor.queryPhysicals(
            "Attack",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        physicals += world.queryPhysicalsByCircle(
            attr.get(aggro_center_attr),
            attr.get(aggro_radius_attr),
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
            return
        else:
            fsm.setState("Idle")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Status", "Idle")
    elif sensor.intersectsEntity("Attack", target):
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        return
    elif target in world.queryEntitiesByCircle(attr.get(aggro_center_attr), attr.get(aggro_radius_attr)):
        mover.setDestination(target.getPosition())
        return
    fsm.setState("Idle")
    attr.set("Target", Enums.NULL_ID)
    attr.set("Status", "Idle")