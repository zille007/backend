import Enums


def ghostIdleUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    if attr.get("Target") is Enums.NULL_ID:
        victims = attr.get("Victims")
        enemyBuildings = world.getEnemyBuildingsForTeam(attr.get("Team"))
        enemyBuildings = filter(lambda b: b.getAttribute("Team") is not attr.get("Team") and b.getAttribute("Status") != "Freeze" and b.id not in victims, enemyBuildings)
        for b in enemyBuildings:
            if (b.getPosition() - entity.getPosition()).magnitude_squared() <= (b.getSize() + attr.get("Haunt range"))**2:
                attr.set("Target", b.id)
                victims.append(b.id)
                waypointMover.pause()
                mover.setDestination(b.getPosition())
                hauntTime = attr.get("Haunt time")
                b.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Freeze", hauntTime)
                attr.set("Status", "Haunt")
                fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
                fsm.setState("Haunt")
                timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
                timer.addTimer("Haunt timer", "Haunt end", 1, hauntTime)
                break


def ghostHauntUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    target = world.getEntityByID(attr.get("Target"))
    if target and not target.isDestroyed():
        if (target.getPosition() - entity.getPosition()).magnitude_squared() < .25:
            tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
            if tags.has("Targetable"):
                tags.remove("Targetable")
    else:
        timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
        timer.removeTimer("Haunt timer")
        eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
        eventIO.receiveEvent("Haunt end")