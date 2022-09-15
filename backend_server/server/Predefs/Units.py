import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector, findFirstUnitWithinRadius
from Intersection import circleToCircle


def basicCreepAI(entity, world, args):
    """
    basicCreepAI
    """
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")

    # do this here without callback so we can manage without populating eventio with
    # an event just because of this
    if timer.hasTimer( "Unit wait timer" ) and not timer.hasTriggered( "Unit wait timer" ):
        return

    if status == "Idle":
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
                ("Status", "Combat"),
                ("Target", target.id),
            ))
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
            waypointMover.pause()
        elif waypointMover.hasWaypoint():
            attr.set("Status", "Moving")
            waypointMover.unpause()

    elif status == "Moving":
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
                ("Status", "Combat"),
                ("Target", target.id),
            ))
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
            waypointMover.pause()

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
            if len(physicals) > 0:
                target = findClosestEntity(entity.getPosition(), map(lambda p: p.entity, physicals))
                attr.set("Target", target.id)
            else:
                attr.setMultiple((
                    ("Target", Enums.NULL_ID),
                    ("Status", "Idle"),
                ))
                # wait as a function of max hit points

                wacm = attr.get( "Wait after combat maximum" )
                wait_max = wacm if wacm is not None else 2.0
                wait_t = wait_max * (1.0 - (attr.get( "Hitpoints" ) / attr.get( "Hitpoints maximum" )))
                timer.addTimer( "Unit wait timer", None, Enums.TIMER_ONCE, wait_t, None )
        elif sensor.intersectsEntity("Attack", target):
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            return

    elif status == "Dead":
        return

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    else:
        attr.set("Status", "Idle")


def basicHeroAI(entity, world, args):
    """
    basicHeroAI

    Requires: Sensor, Effect, Timer, Mover, Attributes
    """
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    if status == "Dead":
        return

    if status == "Idle":
        if attr.get("Target selected") is not Enums.NULL_ID:
            attr.set("Status", "Target")
        elif mover.isMoving():
            attr.set("Status", "Moving")
        else:
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
                if attr.get("Attack ready"):
                    entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
                if not timer.hasTimer("Combat timer"):
                    timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")

    elif status == "Moving":
        if attr.get("Target selected") is not Enums.NULL_ID:
            attr.set("Status", "Target")
        elif not mover.isMoving():
            attr.set("Status", "Idle")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Target selected", Enums.NULL_ID)

    elif status == "Target":
        target = world.getEntityByID(attr.get("Target selected"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
            attr.set("Status", "Idle")
            attr.set("Target selected", Enums.NULL_ID)
        elif sensor.intersectsEntity("Attack", target):
            mover.stop()
            attr.set("Status", "Combat")
            attr.set("Target", target.id)
            if attr.get("Attack ready"):
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        else:
            if not mover.hasDestination() or (mover.destination - target.getPosition()).magnitude_squared() > 1.0:
                mover.setDestination(target.getPosition())

    elif status == "Combat":
        # make sure our target changes are reflected properly
        target = world.getEntityByID(attr.get("Target"))

        if mover.isMoving():
            attr.set("Status", "Moving")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Target selected", Enums.NULL_ID)
        elif attr.get( "Target selected") != attr.get("Target" ) and attr.get( "Target selected" ) != Enums.NULL_ID:
            #make sure we change targets properly even in combat
            attr.set( "Status", "Idle" )
        elif target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
            attr.set("Status", "Idle")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Target selected", Enums.NULL_ID)
        elif not sensor.intersectsEntity("Attack", target):
            if attr.get("Target selected") is not Enums.NULL_ID:
                attr.set("Status", "Target")
            else:
                attr.set("Status", "Idle")
                attr.set("Target", Enums.NULL_ID)
        else:
            return
    elif status == "Charge":
        physicals = sensor.queryPhysicals(
            "Charge",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasTag("Targetable"))
        targets = map(lambda p: p.entity, physicals)
        victims = entity.getAttribute(("Abilities", "Charge", "Victims"))
        targets = [t for t in targets if t not in victims]
        stun_time = entity.getAttribute( ("Abilities", "Charge", "Stun time") )
        for t in targets:
            victims.append(t)
            t.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Stun", stun_time)
        entity.getComponent(Enums.COMP_TYPE_EFFECT).launchEffect("Charge", world, targets)

        if len(targets) > 0:
            # end charge immediately; we need the charge speed increase token from the
            # timer first
            timer = entity.getComponent( Enums.COMP_TYPE_TIMER )
            t = timer.getTimer( "Charge timer" )

            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent( "Charge end", t[ Enums.TIMER_DATA ])
            entity.getComponent(Enums.COMP_TYPE_TIMER).removeTimer( "Charge timer" )

    elif status == "Dead":
        return

    elif status == "Stunned":
        return

    elif status == "Knockback":
        return

    else:
        attr.set("Status", "Idle")


def aggroIdleUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    attr = entity.getAttributes()
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    home = world.getEntityByID(attr.get("Home"))
    teamID = attr.get("Team")
    targetTags = attr.get("Target tags")
    ignoreTags = attr.get("Ignore tags")
    unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                            e.hasAllOfTags(targetTags) and
                            e.hasNoneOfTags(ignoreTags))
    target = None
    if home is not None:
        target = findFirstUnitWithinRadius(home.getPosition(), home.getAttribute("Aggro range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

    if target is None:
        target = findFirstUnitWithinRadius(entity.getPosition(), attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

    if target:
        fsm.setState("Target")
        attr.set("Status", "Target")
        attr.set("Target", target.id)
        mover.setDestination(target.getPosition())
        return
    if not mover.atPosition(attr.get("Rally point")):
        mover.setDestination(attr.get("Rally point"))
        fsm.setState("Moving")
        attr.set("Status", "Moving")
    else:
        fsm.setState("Idle")
        attr.set("Status", "Idle")


def aggroTargetUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    attr = entity.getAttributes()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    home = world.getEntityByID(attr.get("Home"))

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not circleToCircle(target.getPosition(), target.getSize(), entity.getPosition(), attr.get("Attack range")):
        teamID = attr.get("Team")
        targetTags = attr.get("Target tags")
        ignoreTags = attr.get("Ignore tags")
        unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                                e.hasAllOfTags(targetTags) and
                                e.hasNoneOfTags(ignoreTags))
        if home is not None:
            target = findFirstUnitWithinRadius(home.getPosition(), home.getAttribute("Aggro range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))
        if target is None:
            target = findFirstUnitWithinRadius(entity.getPosition(), attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

        if target:
            attr.set("Target", target.id)
            if attr.get("Subtype") != "Pond defender":
                mover.setDestination(target.getPosition())
            return
        else:
            fsm.setState("Idle")
            attr.set("Status", "Idle")
            attr.set("Target", Enums.NULL_ID)
            return
    elif circleToCircle(target.getPosition(), target.getSize(), entity.getPosition(), attr.get("Attack range")):
        mover.stop()
        fsm.setState("Combat")
        attr.set("Status", "Combat")
        if attr.get("Attack ready"):
            entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        return
    elif circleToCircle(target.getPosition(), target.getSize(), home.getPosition(), home.getAttribute("Aggro range")):
        if attr.get("Subtype") != "Pond defender":
            mover.setDestination(target.getPosition())
        return
    fsm.setState("Idle")
    attr.set("Status", "Idle")
    attr.set("Target", Enums.NULL_ID)


def aggroCombatUpdate(entity, world, args):
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    attr = entity.getAttributes()
    team = attr.get("Team")
    pos = entity.getPosition()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    home = world.getEntityByID(attr.get("Home"))

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not circleToCircle(target.getPosition(), target.getSize(), pos, attr.get("Attack range")):
        teamID = attr.get("Team")
        targetTags = attr.get("Target tags")
        ignoreTags = attr.get("Ignore tags")
        unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                                e.hasAllOfTags(targetTags) and
                                e.hasNoneOfTags(ignoreTags))
        if home is not None:
            target = findFirstUnitWithinRadius(home.getPosition(), home.getAttribute("Aggro range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))
        if target is None:
            target = findFirstUnitWithinRadius(pos, attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

        if target:
            fsm.setState("Target")
            attr.set("Status", "Target")
            attr.set("Target", target.id)
            if attr.get("Subtype") != "Pond defender":
                mover.setDestination(target.getPosition())
            return
        else:
            fsm.setState("Idle")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Status", "Idle")
    elif circleToCircle(target.getPosition(), target.getSize(), pos, attr.get("Attack range")):
        ourCreeps = world.getCreepsForTeam(team)
        intersecting = []
        for creep in ourCreeps:
            if creep == entity:
                continue
            creepPos = creep.getPosition()
            if (creepPos - pos).magnitude_squared() <= .25:
                intersecting.append(creep)
        if len(intersecting) > 0:
            avgPos = reduce(lambda a, b: a + b.getPosition(), intersecting, Vector3(0, 0, 0)) / len(intersecting)
            mover.setDestination(pos - (avgPos - pos).normalized()*.3)
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
        return
    elif circleToCircle(target.getPosition(), target.getSize(), home.getPosition(), home.getAttribute("Aggro range")):
        if attr.get("Subtype") != "Pond defender":
            mover.setDestination(target.getPosition())
        return
    fsm.setState("Idle")
    attr.set("Target", Enums.NULL_ID)
    attr.set("Status", "Idle")


def aggroAI(entity, world, args):
    """
    An AI behavior that aggresses units on a radius

    Requires: Sensor, Effect, Timer, Mover, Attributes
    """
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    status = attr.get("Status")
    home = world.getEntityByID(attr.get("Home"))
    if home is not None:
        homeAttr = home.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        homeSensor = home.getComponent(Enums.COMP_TYPE_SENSOR)

    if status == "Idle" or status == "Moving":
        physicals = sensor.queryPhysicals(
            "Attack",
            world,
            lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                      p.entity.getAttribute("Status") != "Dead" and
                      p.entity.hasAllOfTags(attr.get("Target tags")) and
                      p.entity.hasNoneOfTags(attr.get("Ignore tags")))
        if home is not None:
            physicals += homeSensor.queryPhysicals(
                "Aggro",
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
            return
        if not mover.atPosition(attr.get("Rally point")):
            mover.setDestination(attr.get("Rally point"))
            attr.set( "Status", "Moving")
        else:
            attr.set( "Status", "Idle")
        return

    elif status == "Target":
        target = world.getEntityByID(attr.get("Target"))
        if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not sensor.intersectsEntity("Attack", target):
            physicals = sensor.queryPhysicals(
                "Attack",
                world,
                lambda p: p.entity.getAttribute("Team") is not attr.get("Team") and
                          p.entity.getAttribute("Status") != "Dead" and
                          p.entity.hasAllOfTags(attr.get("Target tags")) and
                          p.entity.hasNoneOfTags(attr.get("Ignore tags")))
            if home is not None:
               physicals += homeSensor.queryPhysicals(
                    "Aggro",
                    world,
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
            if attr.get("Attack ready"):
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
            return
        elif homeSensor.intersectsEntity("Aggro", target):
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
            if home is not None:
                physicals += homeSensor.queryPhysicals(
                    "Aggro",
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
        elif homeSensor.intersectsEntity("Aggro", target):
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


def creepIdleUpdate(entity, world, args):
    attr = entity.getAttributes()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if timer.hasTimer("Unit wait timer") and not timer.hasTriggered("Unit wait timer"):
        return

    teamID = attr.get("Team")
    targetTags = attr.get("Target tags")
    ignoreTags = attr.get("Ignore tags")
    unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                            e.hasAllOfTags(targetTags) and
                            e.hasNoneOfTags(ignoreTags))
    target = findFirstUnitWithinRadius(entity.getPosition(), attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

    if target:
        fsm.setState("Combat")
        attr.set("Status", "Combat")
        attr.set("Target", target.id)
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
        waypointMover.pause()
    elif waypointMover.hasWaypoint():
        fsm.setState("Moving")
        attr.set("Status", "Moving")
        waypointMover.unpause()


def creepMovingUpdate(entity, world, args):
    attr = entity.getAttributes()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    pos = entity.getPosition()
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if timer.hasTimer("Unit wait timer") and not timer.hasTriggered("Unit wait timer"):
        return

    waypointMover.unpause()
    teamID = attr.get("Team")
    targetTags = attr.get("Target tags")
    ignoreTags = attr.get("Ignore tags")
    unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                            e.hasAllOfTags(targetTags) and
                            e.hasNoneOfTags(ignoreTags))
    target = findFirstUnitWithinRadius(pos, attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

    if target:
        fsm.setState("Combat")
        attr.set("Status", "Combat")
        attr.set("Target", target.id)
        entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack start")
        waypointMover.pause()
        return

    ourCreeps = world.getCreepsForTeam(teamID)
    intersecting = []
    for creep in ourCreeps:
        if creep == entity:
            continue
        creepPos = creep.getPosition()
        if (creepPos - pos).magnitude_squared() <= .25:
            intersecting.append(creep)
    if len(intersecting) > 0:
        waypointMover.pause()
        waypoint = waypointMover.currentWaypoint()
        avgPos = reduce(lambda a, b: a + b.getPosition(), intersecting, Vector3(0, 0, 0)) / len(intersecting)
        evadePos = pos - (avgPos - pos).normalized()*.3
        normal = (waypoint - pos).normalized()
        normalPos1 = pos + Vector3(-normal.y, normal.x)
        normalPos2 = pos + Vector3(normal.y, -normal.x)
        normalPos = normalPos1 if (normalPos1 - evadePos).magnitude_squared() < (normalPos2 - evadePos).magnitude_squared() else normalPos2
        mover.setDestination((waypoint + normalPos)/2)


def creepCombatUpdate(entity, world, args):
    attr = entity.getAttributes()
    team = attr.get("Team")
    pos = entity.getPosition()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if timer.hasTimer("Unit wait timer") and not timer.hasTriggered("Unit wait timer"):
        return

    target = world.getEntityByID(attr.get("Target"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead" or not circleToCircle(target.getPosition(), target.getSize(), pos, attr.get("Attack range")):
        targetTags = attr.get("Target tags")
        ignoreTags = attr.get("Ignore tags")
        unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                                e.hasAllOfTags(targetTags) and
                                e.hasNoneOfTags(ignoreTags))
        target = findFirstUnitWithinRadius(pos, attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(team))

        if target:
            attr.set("Target", target.id)
        else:
            fsm.setState("Idle")
            attr.set("Target", Enums.NULL_ID)
            attr.set("Status", "Idle")
            # wait as a function of max hit points

            wacm = attr.get("Wait after combat maximum")
            wait_max = wacm if wacm is not None else 2.0
            wait_t = wait_max * (1.0 - (attr.get("Hitpoints") / attr.get("Hitpoints maximum")))
            timer.addTimer("Unit wait timer", None, Enums.TIMER_ONCE, wait_t, None)
    elif circleToCircle(target.getPosition(), target.getSize(), pos, attr.get("Attack range")):
        ourCreeps = world.getCreepsForTeam(team)
        intersecting = []
        for creep in ourCreeps:
            if creep == entity:
                continue
            creepPos = creep.getPosition()
            if (creepPos - pos).magnitude_squared() <= .25:
                intersecting.append(creep)
        if len(intersecting) > 0:
            avgPos = reduce(lambda a, b: a + b.getPosition(), intersecting, Vector3(0, 0, 0)) / len(intersecting)
            mover.setDestination(pos - (avgPos - pos).normalized()*.3)
        if not timer.hasTimer("Combat timer"):
            timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")


def heroIdleUpdate(entity, world, args):
    attr = entity.getAttributes()
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if attr.get("Target selected") is not Enums.NULL_ID:
        fsm.setState("Target")
        attr.set("Status", "Target")
    elif mover.isMoving():
        fsm.setState("Moving")
        attr.set("Status", "Moving")
    else:
        teamID = attr.get("Team")
        targetTags = attr.get("Target tags")
        ignoreTags = attr.get("Ignore tags")
        unitFilter = (lambda e: e.getAttribute("Status") != "Dead" and
                                e.hasAllOfTags(targetTags) and
                                e.hasNoneOfTags(ignoreTags))
        target = findFirstUnitWithinRadius(entity.getPosition(), attr.get("Attack range"), unitFilter, world.iterateEnemyCreepsAndHeroesForTeam(teamID))

        if target is not None:
            fsm.setState("Combat")
            attr.set("Status", "Combat")
            attr.set("Target", target.id)
            if attr.get("Attack ready"):
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Attack first")
            if not timer.hasTimer("Combat timer"):
                timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")


def heroMovingUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    if attr.get("Target selected") is not Enums.NULL_ID:
        fsm.setState("Target")
        attr.set("Status", "Target")
    elif not mover.isMoving():
        fsm.setState("Idle")
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        attr.set("Target selected", Enums.NULL_ID)


def heroTargetUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    target = world.getEntityByID(attr.get("Target selected"))
    if target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
        fsm.setState("Idle")
        attr.set("Status", "Idle")
        attr.set("Target selected", Enums.NULL_ID)
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


def heroCombatUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)

    # make sure our target changes are reflected properly
    target = world.getEntityByID(attr.get("Target"))

    if mover.isMoving():
        fsm.setState("Moving")
        attr.set("Status", "Moving")
        attr.set("Target", Enums.NULL_ID)
        attr.set("Target selected", Enums.NULL_ID)
    elif attr.get("Target selected") != attr.get("Target") and attr.get("Target selected") != Enums.NULL_ID:
        #make sure we change targets properly even in combat
        fsm.setState("Idle")
        attr.set("Status", "Idle")
    elif target is None or target.isDestroyed() or target.getAttribute("Status") == "Dead":
        fsm.setState("Idle")
        attr.set("Status", "Idle")
        attr.set("Target", Enums.NULL_ID)
        attr.set("Target selected", Enums.NULL_ID)
    elif not sensor.intersectsEntity("Attack", target):
        if attr.get("Target selected") is not Enums.NULL_ID:
            fsm.setState("Target")
            attr.set("Status", "Target")
        else:
            fsm.setState("Idle")
            attr.set("Status", "Idle")
            attr.set("Target", Enums.NULL_ID)
    else:
        return


def scoutIdleUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    if not waypointMover.hasWaypoint():
        bases = filter(
            lambda b: b.getAttribute("Team") is not attr.get("Team"),
            world.getBases()
        )
        enemyBase = findClosestEntity(entity.getPosition(), bases)
        path = world.findPath(entity.getPosition(), enemyBase.getPosition(), True)
        waypointMover.setWaypoints(path)


def hauntEnd(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    waypointMover.unpause()
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    tags.add("Targetable")
    attr.set("Status", "Idle")
    attr.set("Target", Enums.NULL_ID)
    if fsm:
        fsm.setState("Idle")

def reachBaseHandler(entity, world, enemyBase):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    baseAttr = enemyBase.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    teamEntity = world.getTeamEntity(attr.get("Team"))
    teamAttr = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    honorReward = attr.get("Honor reward")
    if honorReward:
        teamAttr.inc(("Resources", "Honor"), honorReward)
    entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Status", "Reach base")
    enemyTeamEntity = world.getTeamEntity( baseAttr.get("Team" ) )
    enemyTeamAttr = enemyTeamEntity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    tix = enemyTeamAttr.get( ("Resources", "Tickets") )
    mintix = enemyTeamAttr.get( ("Resources", "Tickets minimum") )
    tix = max( mintix, tix-10 )
    enemyTeamAttr.set( ("Resources", "Tickets"), tix )
    world.networkCommand(Enums.WORLD_EVENT_REACH_BASE, enemyBase, entity)
    world.destroyEntity(entity)


