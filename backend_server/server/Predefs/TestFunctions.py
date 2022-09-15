import Enums
import random
from euclid import Vector3


def testRandomPath(entity, world, args):
    """
    testRandomPath

    Requires: WaypointMover, Transform
    """
    waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
    transform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
    if waypointMover and transform:
        startPos = transform.getWorldPosition()
        endPos = Vector3(random.randint(0, world.map.width), random.randint(0, world.map.height))
        path = world.findPath(startPos, endPos)
        waypointMover.setWaypoints(path)


def testIncrementProcess(entity, world, process):
    """
    testIncrementProcess

    Requires: Attributes
    """
    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attributes and attributes.has("testValue"):
        attributes.inc("testValue", 1)
        if attributes.get("testValue") >= 12:
            process[Enums.PROC_STATUS] |= Enums.PROC_STATUS_TERMINATED


def testAdditionProcess(entity, world, args):
    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attributes and attributes.has("testA") and attributes.has("testB"):
        attributes.inc("testA", attributes.get("testB"))


def testAttackAI(entity, world, args):
    """
    testAI

    Requires: Sensor, Effect, Attributes
    """
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    effect = entity.getComponent(Enums.COMP_TYPE_EFFECT)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    if attr and effect and sensor:
        if attr.get("Attacked"):
            effect.launchEffect("testAttack", world, map(lambda p: p.entity, sensor.queryPhysicals("testSensor", world)))
            attr.set("Attacked", False)


def testHandler(self, entity, world, sender):
    print "TestHandler called, receiver ID: " + str(entity.id) + ", sender ID: " + str(sender.id)


def testCallback(entity, world, args):
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    if tags:
        tags.add("Triggered")
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr:
        attr.set("Times triggered", attr.get("Times triggered") + 1)


def testEffect(entity, world, targets):
    for t in targets:
        attr = t.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            attr.set("Affected", True)


def testAttack(entity, world, targets):
    for t in targets:
        attr = t.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            attr.inc("Health", -1)


def testPredicate(entity, world, args):
    return entity.getAttribute("Test flag") is True