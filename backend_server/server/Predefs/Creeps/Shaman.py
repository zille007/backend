import Enums


def shamanAI(entity, world, args):
    """
    shamanAI
    """
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")

    if not timer.hasTimer("Combat timer"):
        timer.addTimer("Combat timer", "Heal start", Enums.TIMER_INFINITE, "Heal period")

    if status == "Idle":
        if waypointMover.hasWaypoint():
            attr.set("Status", "Moving")
            waypointMover.unpause()

    elif status == "Moving":
        return

    elif status == "Dead":
        return

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    else:
        attr.set("Status", "Idle")


def shamanIdleUpdate(entity, world, args):
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if not timer.hasTimer("Combat timer"):
        timer.addTimer("Combat timer", "Heal start", Enums.TIMER_INFINITE, "Heal period")

    if waypointMover.hasWaypoint():
        fsm.setState("Moving")
        attr.set("Status", "Moving")
        waypointMover.unpause()