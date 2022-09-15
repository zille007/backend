import Enums


def thiefAI(entity, world, args):
    """
    thiefAI
    """
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")

    if status == "Idle":
        if waypointMover.hasWaypoint():
            attr.set("Status", "Moving")
            waypointMover.unpause()

    elif status == "Dead":
        return

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    else:
        attr.set("Status", "Idle")


def thiefIdleUpdate(entity, world, args):
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if waypointMover.hasWaypoint():
        fsm.setState("Moving")
        attr.set("Status", "Moving")
        waypointMover.unpause()


def thiefReachBaseHandler(entity, world, enemyBase):
    entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Status", "Reach base")
    enemyBaseAttr = world.getTeamEntity(enemyBase.getAttribute("Team")).getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    enemyBaseAttr.inc(("Resources", "Tickets"), -10)
    enemyGold = enemyBaseAttr.get(("Resources", "Gold"))
    if enemyGold is 0:
        pass
    elif enemyGold - 75 < 0:
        enemyBaseAttr.set(("Resources", "Gold"), 0)
    else:
        enemyBaseAttr.inc(("Resources", "Gold"), -75)
    world.getTeamEntity(entity.getAttribute("Team")).getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(("Resources", "Gold"), 75)
    world.networkCommand(Enums.WORLD_EVENT_REACH_BASE, enemyBase, entity)
    world.destroyEntity(entity)