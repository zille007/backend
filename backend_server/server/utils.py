import math
import random
from euclid import *
import Enums
from DataStructures import AssociativeList
from StringEnums import AttributeEnums
from Intersection import lineInfToCircleIntersectionPoints


def randomVector3Rect(lower_x, lower_y, upper_x, upper_y):
    range_x = upper_x - lower_x
    range_y = upper_y - lower_y
    return Vector3(random.random()*range_x + lower_x, random.random()*range_y + lower_y, 0.0)


def angleToUnitVector3(a, zeroAngleUnitVector3=None):
    if zeroAngleUnitVector3 is None:
        return Vector3(math.cos(math.radians(a)), math.sin(math.radians(a)))
    else:
        zeroAngle = math.copysign(math.degrees(math.acos(zeroAngleUnitVector3[0])), zeroAngleUnitVector3[1])
        return Vector3(math.cos(math.radians(a + zeroAngle)), math.sin(math.radians(a + zeroAngle)))


def unitVector3ToAngle(u, zeroAngleUnitVector3=None):
    if zeroAngleUnitVector3 is None:
        return math.degrees(math.acos(u[0]))
    else:
        zeroAngle = math.copysign(math.degrees(math.acos(zeroAngleUnitVector3[0])), zeroAngleUnitVector3[1])
        angle = math.copysign(math.degrees(math.acos(u[0])), u[1]) - zeroAngle
        return angle + 360.0 if angle < -180.0 else angle - 360.0 if angle > 180.0 else angle


def areOnSameTeam(entities):
    if len(entities) is 0:
        return
    if len(entities) is 1:
        return True
    team = entities[0].getAttribute("Team")
    for i in xrange(1, len(entities)):
        if entities[i].getAttribute("Team") is not team:
            return False
    return True


def addJitterToVector(vec, jitter):
    return vec + angleToUnitVector3(random.random()*360)*jitter*random.random()


def findFirstUnitWithinLOS(world, center, radius, fltr, units):
    for unit in units:
        unitPos = unit.getPosition()
        if fltr(unit) and (unitPos - center).magnitude_squared() <= (unit.getSize() + radius)**2 and world.queryLineOfSight(center, unitPos):
            return unit
    return None


def findFirstUnitWithinRadius(center, radius, fltr, units):
    for unit in units:
        if fltr(unit) and (unit.getPosition() - center).magnitude_squared() <= (unit.getSize() + radius)**2:
            return unit
    return None


def findFirstUnit(fltr, units):
    for unit in units:
        if fltr(unit):
            return unit
    return None


def findOneEntity(fltr, entities):
    for e in entities:
        if fltr(e):
            return e
    return None


def findAllEntities(fltr, entities):
    return filter(fltr, entities)


def findClosestEntity(pos, entities):
    xform = None
    for e in entities:
        if xform is None:
            xform = e.getComponent(Enums.COMP_TYPE_TRANSFORM)
            continue
        otherXForm = e.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if otherXForm:
            if otherXForm.getDistanceSquaredToWorldPosition(pos) < xform.getDistanceSquaredToWorldPosition(pos):
                xform = otherXForm
    if xform:
        return xform.entity
    return None


def findClosestTransform(pos, xforms):
    xform = None
    for t in xforms:
        if xform is None:
            xform = t
            continue
        if t.getDistanceSquaredToWorldPosition(pos) < xform.getDistanceSquaredToWorldPosition(pos):
            xform = t
    return xform


def findClosestPhysical(pos, physicals):
    xform = None
    for p in physicals:
        if xform is None:
            xform = p.entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
            continue
        otherXForm = p.entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if otherXForm:
            if otherXForm.getDistanceSquaredToWorldPosition(pos) < xform.getDistanceSquaredToWorldPosition(pos):
                xform = otherXForm
    if xform:
        return xform.getComponent(Enums.COMP_TYPE_PHYSICAL)
    return None


def findClosestWaypoint(pos, waypoints):
    pass


def unitQueueHasAvailableSlots(queue):
    for slot in queue:
        if slot == "":
            return True
    return False


def dictToNestedTuple(d):
    l = []
    for k in d.iterkeys():
        v = d[k]
        if k == "_id":
            continue
        if isinstance(v, dict):
            l.append((k, dictToNestedTuple(v)))
        else:
            l.append((k, v))
    return tuple(l)


def nestedTupleToDict(nestedTuple):
    d = {}
    for (key, value) in nestedTuple:
        if isinstance(value, tuple):
            d[key] = nestedTupleToDict(value)
        else:
            d[key] = value
    return d


def nestedTupleToNetworkDict(nestedTuple):
    d = {}
    for (key, value) in nestedTuple:
        if isinstance(value, Vector3):
            d[AttributeEnums[key]] = tuple(value)
        elif isinstance(value, tuple):
            d[AttributeEnums[key]] = nestedTupleToNetworkDict(value)
        else:
            d[AttributeEnums[key]] = value
    return d


def listToNetworkList(lst):
    newList = []
    for e in lst:
        if isinstance(e, Vector3):
            newList.append(tuple(e))
        else:
            newList.append(e)
    return newList


def dbListToList(lst):
    result = []
    for l in lst:
        if isinstance(l, unicode):
            result.append(str(l))
        elif isinstance(l, list):
            if isVector3(l):
                result.append(listToVector(l))
            else:
                result.append(dbListToList(l))
        else:
            result.append(l)
    return result


def nestedListToNestedTuple(lst):
    for i in xrange(len(lst)):
        if isinstance(lst[i], list):
            lst[i] = nestedListToNestedTuple(lst[i])
    return tuple(lst)


def getFromNestedTuple(nestedTuple, key):
    for (k, v) in nestedTuple:
        if k == key:
            return v
    return None


def dbStringListToTuple(lst):
    t = []
    for l in lst:
        t.append(str(l))
    return tuple(t)


def isVector2(numberList):
    if len(numberList) is not 2:
        return False
    for n in numberList:
        if not isinstance(n, int) and not isinstance(n, float):
            return False
    return True


def isVector3(numberList):
    if len(numberList) is not 3:
        return False
    for n in numberList:
        if not isinstance(n, int) and not isinstance(n, float):
            return False
    return True


def listToVector(elem):
    assert(type(elem) is list)
    if len(elem) == 3:
        return Vector3(float(elem[0]), float(elem[1]), float(elem[2]))

    if len(elem) == 2:
        return Vector2(float(elem[0]), float(elem[1]))

    return None


def dictToVector(elem):
    assert(type(elem) is dict)
    if len(elem) == 3:
        return Vector3(float(elem['x']), float(elem['y']), float(elem['z']))

    if len(elem) == 2:
        return Vector2(float(elem['x']), float(elem['y']))

    return None


def dict_diff(first, second):
    if isinstance(first, dict):
        d = {}
        for key in first.iterkeys():
            key = str(key)
            if not second.has_key(key):
                d[key] = str(first[key]) + " != (key missing)"
            else:
                if isinstance(second, dict):
                    diff = dict_diff(first[key], second[key])
                    if diff is not None:
                        d[key] = diff
                else:
                    d[key] = str(first[key]) + " != " + str(second[key])
        return None if d == {} else d
    else:
        if first != second:
            return str(first) + " != " + str(second)


def dict_miss(first, second):
    if isinstance(first, dict):
        d = {}
        for key in first.iterkeys():
            key = str(key)
            if second is None or not second.has_key(key):
                d[key] = str(first[key]) + " != (key missing)"
            else:
                if isinstance(second, dict):
                    diff = dict_miss(first[key], second[key])
                    if diff is not None:
                        d[key] = diff
        return None if d == {} else d


def print_dict(d, keypath=None):
    if isinstance(d, dict):
        for key in d.iterkeys():
            print_dict(d[key], key if keypath is None else keypath + "." + key)
    else:
        print "  " + keypath + ": " + str(d)


def sign(a):
    if a < 0.0:
        return 1
    
    return 0


def lerp(a, b, coeff):
    return a + (b - a) * coeff


def clamp(a, in_min, in_max):
    ret = a
    if ret < in_min:
        ret = in_min
    if ret > in_max:
        ret = in_max
        
    return ret


def todegs(rads):
    return rads * 180.0 / math.pi


def pointsAroundCircle(center, radius, start, end, count):
    """
    Possibly buggy - avoid for now
    """
    points = [start]
    endAngle = unitVector3ToAngle((end - center).normalized(), (start - center).normalized())
    increment = endAngle/(count + 1)
    for i in xrange(count):
        points.append(angleToUnitVector3((i + 1)*increment, start.normalized())*radius + center)
    points.append(end)
    return points


def vectorAverage(vectors):
    count = len(vectors)
    x = sum([v.x for v in vectors])
    y = sum([v.y for v in vectors])
    return Vector3(x/count, y/count)


def moveToPerimeter(pos, center, radius):
    v = pos - center
    if v.magnitude_squared() <= radius**2:
        return pos + v.normalized()*radius
    return pos


def printNestedTuple(t, indent=None):
    if indent is None:
        indent = ""
    for (k, v) in t:
        if isinstance(v, tuple):
            print indent + k + ":"
            printNestedTuple(v, indent + "  ")
        else:
            print indent + k + ": " + str(v)


def printAssociativeList(assocList, indent=None):
    if indent is None:
        indent = ""
    for (k, v) in assocList.l:
        if isinstance(v, AssociativeList):
            print indent + k + ":"
            printAssociativeList(v, indent + "  ")
        else:
            print indent + k + ": " + str(v)