import Queue
from StringEnums import *
import Enums


class ComponentSystem(object):
    def __init__(self, world):
        self.world = world
        self.period = 1
        self.periodCounter = self.period

    def step(self):
        pass

    def process(self, dt, components):
        pass


class TransformSystem(ComponentSystem):
    def step(self):
        if Enums.USE_SPATIAL_HASH:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_TRANSFORM))

    def process(self, dt, components):
        for i in xrange(len(components)):
            transform = components[i]
            transform.oldPosition = transform.getLocalPosition()
            transform.oldDirection = transform.getLocalDirection()
            transform.oldScale = transform.getLocalScale()


class MoverSystem(ComponentSystem):
    def __init__(self, world):
        super(MoverSystem, self).__init__(world)
        self.period = Enums.MOVER_SYSTEM_UPDATE_PERIOD
        self.periodCounter = self.period

    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_MOVER))
            self.periodCounter = self.period

    def process(self, dt, components):
        for i in xrange(len(components)):
            mover = components[i]
            if not mover.isMoving():
                mover.sleep()
                continue
            xform = mover.entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
            if mover.entity.hasTag("Hero") and not mover.entity.hasTag("Air"):
                if mover.hasDestination():
                    if (xform.getWorldPosition() - mover.destination).magnitude_squared() <= (xform.getWorldDirection()*mover.speed*dt).magnitude_squared():
                        stop = False
                        newPos = mover.destination
                        if self.world.map.worldPosIsOutside(newPos):
                            stop = True
                        else:
                            newHeight = self.world.map.getGridNodeByWorldPos(newPos)[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            oldHeight = self.world.map.getGridNodeByWorldPos(xform.getWorldPosition())[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            if abs(newHeight - oldHeight) > .75:
                                stop = True
                        if stop:
                            mover.stop()
                            waypointMover = mover.entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
                            if waypointMover:
                                waypointMover.clearWaypoints()
                            attr = mover.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                            if attr:
                                attr.set("Status", "Idle")
                            fsm = mover.entity.getComponent(Enums.COMP_TYPE_FSM)
                            if fsm:
                                fsm.setState("Idle")
                        else:
                            xform.setWorldPosition(mover.destination)
                            mover.stop()
                            if mover.entity.hasComponent(Enums.COMP_TYPE_ATTRIBUTES) and mover.entity.hasComponent(Enums.COMP_TYPE_EVENTIO):
                                mover.entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Movement destination reached")
                    else:
                        stop = False
                        velVector = xform.getWorldDirection()*mover.speed*dt
                        newPos = xform.getWorldPosition() + velVector
                        if self.world.map.worldPosIsOutside(newPos):
                            stop = True
                        else:
                            newHeight = self.world.map.getGridNodeByWorldPos(newPos)[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            oldHeight = self.world.map.getGridNodeByWorldPos(xform.getWorldPosition())[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            if abs(newHeight - oldHeight) > .75:
                                stop = True
                        if stop:
                            mover.stop()
                            waypointMover = mover.entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
                            if waypointMover:
                                waypointMover.clearWaypoints()
                            attr = mover.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                            if attr:
                                attr.set("Status", "Idle")
                            fsm = mover.entity.getComponent(Enums.COMP_TYPE_FSM)
                            if fsm:
                                fsm.setState("Idle")
                        else:
                            xform.translate(velVector)
                else:
                    stop = False
                    velVector = xform.getWorldDirection()*mover.speed*dt
                    newPos = xform.getWorldPosition() + velVector
                    if self.world.map.worldPosIsOutside(newPos):
                        stop = True
                    else:
                        newHeight = self.world.map.getGridNodeByWorldPos(newPos)[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                        oldHeight = self.world.map.getGridNodeByWorldPos(xform.getWorldPosition())[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                        if abs(newHeight - oldHeight) > .75:
                            stop = True
                    if stop:
                        mover.stop()
                        waypointMover = mover.entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
                        if waypointMover:
                            waypointMover.clearWaypoints()
                        attr = mover.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                        if attr:
                            attr.set("Status", "Idle")
                        fsm = mover.entity.getComponent(Enums.COMP_TYPE_FSM)
                        if fsm:
                            fsm.setState("Idle")
                    else:
                        xform.translate(velVector)
            elif mover.entity.hasTag("Projectile"):
                if mover.hasDestination():
                    if (xform.getWorldPosition() - mover.destination).magnitude_squared() <= (xform.getWorldDirection()*mover.speed*dt).magnitude_squared():
                        stop = False
                        newPos = mover.destination
                        if self.world.map.worldPosIsOutside(newPos):
                            stop = True
                        else:
                            newHeight = self.world.map.getGridNodeByWorldPos(newPos)[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            oldHeight = self.world.map.getGridNodeByWorldPos(xform.getWorldPosition())[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            heightDiff = newHeight - oldHeight
                            if heightDiff > 0.0:
                                mover._projectileAscending = True
                            elif heightDiff < 0.0 and mover._projectileAscending:
                                stop = True
                        if stop:
                            mover.stop()
                            waypointMover = mover.entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
                            if waypointMover:
                                waypointMover.clearWaypoints()
                            mover.entity.receiveEvent("_destroy")
                        else:
                            xform.setWorldPosition(mover.destination)
                            mover.stop()
                            if mover.entity.hasComponent(Enums.COMP_TYPE_ATTRIBUTES) and mover.entity.hasComponent(Enums.COMP_TYPE_EVENTIO):
                                mover.entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Movement destination reached")
                    else:
                        stop = False
                        velVector = xform.getWorldDirection()*mover.speed*dt
                        newPos = xform.getWorldPosition() + velVector
                        if self.world.map.worldPosIsOutside(newPos):
                            stop = True
                        else:
                            newHeight = self.world.map.getGridNodeByWorldPos(newPos)[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            oldHeight = self.world.map.getGridNodeByWorldPos(xform.getWorldPosition())[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                            heightDiff = newHeight - oldHeight
                            if heightDiff > 0.0:
                                mover._projectileAscending = True
                            elif heightDiff < 0.0 and mover._projectileAscending:
                                stop = True
                        if stop:
                            mover.stop()
                            waypointMover = mover.entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
                            if waypointMover:
                                waypointMover.clearWaypoints()
                            mover.entity.receiveEvent("_destroy")
                        else:
                            xform.translate(velVector)
                else:
                    stop = False
                    velVector = xform.getWorldDirection()*mover.speed*dt
                    newPos = xform.getWorldPosition() + velVector
                    if self.world.map.worldPosIsOutside(newPos):
                        stop = True
                    else:
                        newHeight = self.world.map.getGridNodeByWorldPos(newPos)[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                        oldHeight = self.world.map.getGridNodeByWorldPos(xform.getWorldPosition())[Enums.NODE_DATA][Enums.GRIDNODE_DATA][Enums.GRIDNODE_DATA_HEIGHT]
                        heightDiff = newHeight - oldHeight
                        if heightDiff > 0.0:
                            mover._projectileAscending = True
                        elif heightDiff < 0.0 and mover._projectileAscending:
                            stop = True
                    if stop:
                        mover.stop()
                        waypointMover = mover.entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
                        if waypointMover:
                            waypointMover.clearWaypoints()
                        mover.entity.receiveEvent("_destroy")
                    else:
                        xform.translate(velVector)
            else:
                if mover.hasDestination():
                    if (xform.getWorldPosition() - mover.destination).magnitude_squared() <= (xform.getWorldDirection()*mover.speed*dt).magnitude_squared():
                        xform.setWorldPosition(mover.destination)
                        mover.stop()
                        attr = mover.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                        if attr:
                            attr.set("Status", "Idle")
                        fsm = mover.entity.getComponent(Enums.COMP_TYPE_FSM)
                        if fsm:
                            fsm.setState("Idle")
                        if mover.entity.hasComponent(Enums.COMP_TYPE_ATTRIBUTES) and mover.entity.hasComponent(Enums.COMP_TYPE_EVENTIO):
                            mover.entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Movement destination reached")
                    else:
                        xform.translate(xform.getWorldDirection()*mover.speed*dt)
                else:
                    xform.translate(xform.getWorldDirection()*mover.speed*dt)


class WaypointMoverSystem(ComponentSystem):
    def __init__(self, world):
        super(WaypointMoverSystem, self).__init__(world)
        self.period = Enums.WAYPOINTMOVER_SYSTEM_UPDATE_PERIOD
        self.periodCounter = self.period

    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_WAYPOINTMOVER))
            self.periodCounter = self.period

    def process(self, dt, components):
        for i in xrange(len(components)):
            waypointMover = components[i]
            if waypointMover.paused:
                continue
            if not waypointMover.hasWaypoint():
                waypointMover.clearWaypoints()
                continue
            mover = waypointMover.entity.getComponent(Enums.COMP_TYPE_MOVER)
            distSqrFromWaypoint = waypointMover.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getDistanceSquaredToWorldPosition(waypointMover.currentWaypoint())
            if distSqrFromWaypoint < .25:
                if waypointMover.hasNextWaypoint():
                    mover.setDestination(waypointMover.nextWaypoint())
                else:
                    waypointMover.clearWaypoints()
                    if waypointMover.entity.hasComponent(Enums.COMP_TYPE_ATTRIBUTES) and waypointMover.entity.hasComponent(Enums.COMP_TYPE_EVENTIO):
                        waypointMover.entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Waypoint movement complete")


class TimerSystem(ComponentSystem):
    def __init__(self, world):
        super(TimerSystem, self).__init__(world)
        self.period = Enums.TIMER_SYSTEM_UPDATE_PERIOD
        self.periodCounter = self.period

    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_TIMER))
            self.periodCounter = self.period

    def process(self, dt, components):
        for i in xrange(len(components)):
            timerComponent = components[i]
            timers = timerComponent.timers
            timerCount = len(timers)
            requiresCleanup = False

            for i in xrange(timerCount):
                timer = timers[i]

                if timer[Enums.TIMER_STATUS] & (Enums.TIMER_STATUS_REMOVED | Enums.TIMER_STATUS_PAUSED):
                    if timer[Enums.TIMER_STATUS] & Enums.TIMER_STATUS_REMOVED:
                        requiresCleanup = True
                    continue

                if not timer[Enums.TIMER_STATUS] & Enums.TIMER_STATUS_PAUSED:
                    timer[Enums.TIMER_CURRENT_COUNTDOWN] -= dt
                    if timer[Enums.TIMER_CURRENT_COUNTDOWN] <= 0.0:
                        timer[Enums.TIMER_STATUS] |= Enums.TIMER_STATUS_TRIGGERED

                if timer[Enums.TIMER_STATUS] & Enums.TIMER_STATUS_TRIGGERED:
                    timer[Enums.TIMER_STATUS] &= ~Enums.TIMER_STATUS_TRIGGERED
                    timer[Enums.TIMER_TRIGGER_COUNT] += 1
                    if timer[Enums.TIMER_TRIGGER_COUNT] < timer[Enums.TIMER_TRIGGER_LIMIT] or timer[Enums.TIMER_TRIGGER_LIMIT] < 0:
                        time = timer[Enums.TIMER_COUNTDOWN_START]
                        if isinstance(time, str):
                            attr = timerComponent.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                            combatAttr = timerComponent.entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
                            if combatAttr:
                                time = combatAttr.queryEffectiveAttribute(time)
                            else:
                                time = attr.get(time)
                        timer[Enums.TIMER_CURRENT_COUNTDOWN] += time
                    else:
                        timer[Enums.TIMER_STATUS] |= Enums.TIMER_STATUS_REMOVED
                        requiresCleanup = True
                    timerComponent.entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent(timer[Enums.TIMER_EVENT], timer[Enums.TIMER_DATA])

            if requiresCleanup:
                timerComponent.timers = filter(lambda t: not t[Enums.TIMER_STATUS] & Enums.TIMER_STATUS_REMOVED, timers)
            if len(timerComponent.timers) is 0:
                timerComponent.sleep()
            else:
                timerComponent.timers.sort(key=lambda t: t[Enums.TIMER_CURRENT_COUNTDOWN])


class EventIOSystem(ComponentSystem):
    def __init__(self, world):
        super(EventIOSystem, self).__init__(world)
        self.period = Enums.EVENT_SYSTEM_UPDATE_PERIOD
        self.periodCounter = self.period

    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_EVENTIO))
            self.periodCounter = self.period

    def process(self, dt, components):
        for i in xrange(len(components)):
            eventIO = components[i]
            events = eventIO.events
            eventIO.clearEventBuffer()
            for event in events:
                if event[0][0] == "_":
                    if event[0] == "_destroy":
                        self.world.destroyEntity(eventIO.entity)
                        break
                else:
                    handler = eventIO.getHandler(event[0])
                    if handler:
                        if isinstance(handler, list):
                            for h in handler:
                                h(eventIO.entity, self.world, event[1])
                        else:
                            handler(eventIO.entity, self.world, event[1])
                    #eventIO.onProcessEvent(event[0], event[1])


class FSMSystem(ComponentSystem):
    def __init__(self, world):
        super(FSMSystem, self).__init__(world)
        self.period = Enums.FSM_SYSTEM_UPDATE_PERIOD
        self.periodCounter = self.period

    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_FSM))
            self.periodCounter = self.period

    def process(self, dt, components):
        for i in xrange(len(components)):
            fsm = components[i]
            entity = fsm.entity
            if fsm.updatePeriod <= 0.0 or fsm.updatePeriod is None:
                entity.getComponent(Enums.COMP_TYPE_EVENTIO).receivePriorityEvent(fsm.state + " update")
            else:
                fsm.timer -= dt
                if fsm.timer <= 0.0:
                    fsm.timer += fsm.updatePeriod
                    entity.getComponent(Enums.COMP_TYPE_EVENTIO).receivePriorityEvent(fsm.state + " update")


class ProcessSystem(ComponentSystem):
    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_PROCESS))
            self.periodCounter = self.period

    def process(self, dt, components):
        for i in xrange(len(components)):
            process = components[i]
            requiresCleanup = False
            for proc in process.processes:
                if not proc[Enums.PROC_STATUS] & (Enums.PROC_STATUS_PAUSED | Enums.PROC_STATUS_TERMINATED):
                    proc[Enums.PROC_PERIOD_COUNTER] -= 1
                    if proc[Enums.PROC_PERIOD_COUNTER] <= 0:
                        proc[Enums.PROC_PERIOD_COUNTER] = proc[Enums.PROC_PERIOD]
                        proc[Enums.PROC_FUNCTION](process.entity, self.world, proc)
                        proc[Enums.PROC_TICK_COUNT] += 1
                if proc[Enums.PROC_STATUS] & Enums.PROC_STATUS_TERMINATED:
                    requiresCleanup = True
                    continue
            if requiresCleanup:
                for i in xrange(len(process.processes)):
                    proc = process.processes[i]
                    if proc[Enums.PROC_STATUS] & Enums.PROC_STATUS_TERMINATED:
                        process.processes[i] = None
                        process.onProcessEnded(proc[Enums.PROC_NAME])
                process.processes = filter(lambda p: p is not None, process.processes)
                if len(process.processes) is 0:
                    process.sleep()


class PhysicalSystem(ComponentSystem):
    def step(self):
        if Enums.USE_SPATIAL_HASH:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_PHYSICAL))

    def process(self, dt, components):
        for i in xrange(len(components)):
            physical = components[i]
            self.world.spatialHash.updatePhysical(physical)


class NetworkSystem(ComponentSystem):
    def __init__(self, world):
        super(NetworkSystem, self).__init__(world)
        self.period = Enums.NETWORK_COMMAND_PROCESS_PERIOD
        self.periodCounter = self.period
        self.requestQueue = Queue.Queue()
        self.networkRequestHandlers = None

    def processRequests(self, maxCount = -1):
        maxCount = self.requestQueue.qsize() if maxCount == -1 else maxCount
        i = 0
        while i < maxCount and not self.requestQueue.empty():
            i += 1
            user, request, seq_no, seq_dict = self.requestQueue.get()
            try:
                self.networkRequestHandlers[RequestEnums[request]](user, seq_no, **seq_dict)
            except KeyError:
                continue

    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_NETWORK))
            self.periodCounter = self.period

    def process(self, dt, components):
        for i in xrange(len(components)):
            network = components[i]
            if network.entity is not None:
                buf = network.eventBuffer
                for event_tuple in buf:
                    self.world.networkCommand(event_tuple[0], event_tuple[1], network.entity)
                network.eventBuffer = []

    def queueRequest(self, user, request, request_number, request_dict):
        self.requestQueue.put((user, request, request_number, request_dict))


class DeathSystem(ComponentSystem):
    """
    DeathSystem

    "Death must be engineered in order for it to exist, and thus it also requires a complex system to support it."
        - Miika

    "For since by man [came] death, by man [came] also the resurrection of the dead. For as in Adam all die, even so in
     Christ shall all be made alive."
        - 1 Corinthians 15: 21-22 (King James Version)
    """
    def __init__(self, world):
        super(DeathSystem, self).__init__(world)
        self.period = Enums.DEATH_CLEANUP_PERIOD
        self.periodCounter = self.period

    def step(self):
        self.periodCounter -= 1
        if self.periodCounter is 0:
            self.process(self.world.dt*self.period, self.world.getDestroyedEntities())
            self.periodCounter = self.period

    def process(self, dt, entities):
        for i in xrange(len(entities)):
            entities[i].destroy()
            if entities[i].isReleased():
                self.world.releaseDestroyedEntity(entities[i])
        self.world.removeDestroyedEntities()


class VisibilitySystem(ComponentSystem):
    def __init__(self, world):
        super(VisibilitySystem, self).__init__(world)
        self.period = Enums.VISIBILITY_UPDATE_PERIOD
        self.periodCounter = self.period

    def entityInsideRadius(self, entity, center, radius):
        if radius is None:
            return False
        distSqr = (entity.getPosition() - center).magnitude_squared()
        return distSqr <= radius**2

    def step(self):
        if Enums.CALCULATE_VISIBILITY:
            self.periodCounter -= 1
            if self.period >= self.world.getTeamCount():
                if 0 < self.periodCounter <= self.world.getTeamCount():
                    teamID = self.periodCounter
                    units = self.world.getUnitsForTeam(teamID) + self.world.getWardsForTeam(teamID) + [self.world.getBaseForTeamID(teamID)]
                    enemies = [(self.world.getUnitsForTeam(i) + [self.world.getBaseForTeamID(i)] + self.world.getWardsForTeam(i) + self.world.getVictoryPointsForTeamID(i), i) for i in xrange(1, self.world.getTeamCount() + 1) if i is not teamID]
                    self.process(self.world.dt*self.period, teamID, units, enemies)
                elif self.periodCounter is 0:
                    units = self.world.getUnitsForTeam(0)
                    if len(units) > 0:
                        enemies = [(self.world.getUnitsForTeam(i), i) for i in xrange(1, self.world.getTeamCount() + 1) if i is not 0]
                        self.process(self.world.dt*self.period, 0, units, enemies)
                    self.periodCounter = self.period
            else:
                if self.periodCounter is 0:
                    for i in xrange(self.world.getTeamCount() + 1):
                        teamID = i
                        units = self.world.getUnitsForTeam(teamID) + [self.world.getBaseForTeamID(teamID)]
                        enemies = [(self.world.getUnitsForTeam(i) + [self.world.getBaseForTeamID(i)] + self.world.getVictoryPointsForTeamID(i), i) for i in xrange(1, self.world.getTeamCount() + 1) if i is not teamID]
                        self.process(self.world.dt*self.period, teamID, units, enemies)
                    self.periodCounter = self.period

    def process(self, dt, teamID, units, enemies):
        for u in units:
            if u is None:
                continue

            attr = u.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            for enemyTeam in enemies:
                enemyTeamID = enemyTeam[1]
                for e in enemyTeam[0]:
                    if e is not None:
                        if e.hasComponent(Enums.COMP_TYPE_COMBATATTRIBUTES):
                            enemyAttr = e.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
                        else:
                            enemyAttr = e.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
                        if self.entityInsideRadius(u, e.getPosition(), enemyAttr.get("Sight range")):
                            attr.set(("Visibility", str(enemyTeamID)), True)
                            break
                else:
                    attr.set(("Visibility", str(enemyTeamID)), False)


class PredicateSystem(ComponentSystem):
    def __init__(self, world):
        super(PredicateSystem, self,).__init__(world)
        self.period = Enums.PREDICATE_SYSTEM_UPDATE_PERIOD
        self.periodCounter = self.period

    def step(self):
        self.process(self.world.dt*self.period, self.world.getAwakeComponents(Enums.COMP_TYPE_PREDICATE))

    def process(self, dt, components):
        for i in xrange(len(components)):
            predComponent = components[i]
            for j in xrange(len(predComponent.predicates)):
                pred = predComponent.predicates[j]
                pred[Enums.PRED_CURRENT_COUNTDOWN] -= dt
                if pred[Enums.PRED_CURRENT_COUNTDOWN] <= 0.0:
                    if pred[Enums.PRED_FUNCTION](predComponent.entity, self.world, None):
                        pred[Enums.PRED_TRIGGER_COUNT] += 1
                        predComponent.entity.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent(pred[Enums.PRED_EVENT], pred[Enums.PRED_DATA])
                        if pred[Enums.PRED_TRIGGER_COUNT] < pred[Enums.PRED_TRIGGER_LIMIT] or pred[Enums.PRED_TRIGGER_LIMIT] < 0:
                            pred[Enums.PRED_CURRENT_COUNTDOWN] += pred[Enums.PRED_PERIOD]
                        else:
                            predComponent.predicates[j] = None
            predComponent.predicates = filter(lambda p: p is not None, predComponent.predicates)


COMPSYS_TYPES = [
    TransformSystem,
    MoverSystem,
    WaypointMoverSystem,
    TimerSystem,
    EventIOSystem,
    FSMSystem,
    ProcessSystem,
    PhysicalSystem,
    NetworkSystem,
    DeathSystem,
    VisibilitySystem,
    PredicateSystem,
]


COMPSYS_TYPE_COUNT = len(COMPSYS_TYPES)