# coding=utf8

from euclid import Vector2, Vector3, Matrix3
import math
from Intersection import *
import ComponentField
from DataStructures import AssociativeList
from StringEnums import AttributeEnums
import Enums
import PredefinedFunctions
import utils
import copy
import sys

class ComponentError(Exception):
    def __init__(self, msg, component_instance):
        self.message = msg
        self.componentInstance = component_instance

    def __str__(self):
        return str(self.message) + " in instance " + repr(self.componentInstance)


class Component(object):
    def __init__(self, type):
        self.statusMask = Enums.COMP_MASK_NULL
        self.type = type
        self.index = 0
        self.initialized = False
        self.entity = None

    def initialize(self, args):
        self.initialized = True

    def clear(self):
        pass

    def awake(self):
        self.statusMask |= Enums.COMP_STATUS_AWAKE

    def sleep(self):
        self.statusMask &= ~Enums.COMP_STATUS_AWAKE

    def activate(self):
        self.statusMask |= Enums.COMP_STATUS_ACTIVE
        self.statusMask |= Enums.COMP_STATUS_AWAKE

    def deactivate(self):
        self.statusMask &= ~Enums.COMP_STATUS_ACTIVE
        self.statusMask &= ~Enums.COMP_STATUS_AWAKE

    def attach(self, entity):
        self.clear()
        self.entity = entity
        self.statusMask = Enums.COMP_MASK_AWAKE

    def detach(self):
        self.clear()
        self.entity = None
        self.initialized = False
        self.statusMask = Enums.COMP_MASK_RESERVED

    def hasStatus(self, status):
        return (self.statusMask & status) is status


class Attributes(Component):
    """
    Attributes

    Provides an entity with the ability to store named data of any kind.

    Requires: -
    """
    def __init__(self):
        super(Attributes, self).__init__(Enums.COMP_TYPE_ATTRIBUTES)
        self.attributes = AssociativeList()

    def initialize(self, args):
        """
        initialize

        Takes a list of key value tuples, which are interpreted as attribute names and attribute values.
        If a value is another key value tuple, it becomes a nested attribute, the depth of which is not bound.
        Example:

        attr.initialize((
            ("Hitpoints", 15),
            ("Armor", 2),
            ("Stats", (  # this is a nested attribute
                ("Strength", 5),
                ("Dexterity", 10),
                ("Intelligence", 9),),
            ("Attack period", 2.5),
        ))
        """
        if args is not None:
            self.setMultiple(args)
        super(Attributes, self).initialize(args)

    def addIncreases(self, increases):
        for inc in increases:
            self.addIncrease(inc)

    def addIncrease(self, (key, inc)):
        if isinstance(inc, tuple):
            for i in inc:
                self._addIncrease((key,), i)
        else:
            self.inc(key, inc)

    def _addIncrease(self, prevKeys, (key, inc)):
        if isinstance(inc, tuple):
            for i in inc:
                self._addIncrease(prevKeys + (key,), i)
        else:
            self.inc(prevKeys + (key,), inc)

    def clear(self):
        self.attributes.clear()

    def detach(self):
        super(Attributes, self).detach()

    def apply(self, key, value):
        """
        This method applies a change to an attribute based on a key with a special symbol at the beginning.
        The key is a normal attribute key with the exception that it has one of the following symbols at index 0:
            +, means inc
            -, means negative inc
            *, means mul
            /, means inverse mul
            =, means set

        Example:
            attr.apply("+Stats.Strength", 5)  # increases Strength by 5
            attr.apply("*Speed", 1.25)  # multiplies Speed by 1.25
        """
        t = key[0]
        key = key[1:]

        # SUPER HACK 100000
        if key == "DuckAlarm":
            t = "="
            key ="Abilities.Summon.Summon unit"
            value = "Celestial wolf"
            if self.get( key ) is None or self.get( "Subtype" ) == "Rogue":   # Extra check for rogues to fix DTEA-10
                return

        if t == "+":
            self.inc(key, value)
        elif t == "-":
            self.inc(key, -value)
        elif t == "*":
            self.mul(key, value)
        elif t == "/":
            self.mul(key, -value)
        elif t == "=":
            if type(value) is unicode:
                self.set( str(key), str(value) )
            else:
                self.set(key, value )

    def applyMultiple(self, increases):
        if isinstance(increases, AssociativeList):
            for key, value in increases.l:
                self.apply(key, value)
        elif isinstance(increases, tuple) or isinstance(increases, list):
            for key, value in increases:
                self.apply(key, value)

    def set(self, key, value):
        if isinstance(key, tuple):
            assocList = self.attributes.get(key[0])
            if assocList is None:
                assocList = AssociativeList()
                self.attributes.set(key[0], assocList)
            i = 1
            limit = len(key) - 1
            while i < limit:
                nestedAssocList = assocList.get(key[i])
                if nestedAssocList is None:
                    nestedAssocList = AssociativeList()
                    assocList.set(key[i], nestedAssocList)
                assocList = nestedAssocList
                i += 1
            old = assocList.get(key[-1])
            if isinstance(value, list):
                value = copy.deepcopy(value)
            elif isinstance(value, Vector3):
                value = value.copy()
            new = assocList.set(key[-1], value)
            if new != old:
                self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key, new, old, Enums.ATTR_SET))
        else:
            key = key.split(".")
            if len(key) is 1:
                old = self.attributes.get(key[0])
                if isinstance(value, list):
                    value = copy.deepcopy(value)
                elif isinstance(value, Vector3):
                    value = value.copy()
                new = self.attributes.set(key[0], value)
                if new != old:
                    self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key[0], new, old, Enums.ATTR_SET))
            else:
                self.set(tuple(key), value)

    def setMultiple(self, kvPairs):
        olds = []
        for (key, value) in kvPairs:
            key = str(key)
            if isinstance(value, tuple):
                old = []
                olds.append((key, old))
                assocList = self.attributes.get(key)
                if assocList is None:
                    assocList = AssociativeList()
                    self.attributes.set(key, assocList)
                self._setMultiple(assocList, old, value)
            elif isinstance(value, list):
                olds.append((key, self.attributes.get(key)))
                self.attributes.set(key, copy.deepcopy(value))
            elif isinstance(value, Vector3):
                olds.append((key, self.attributes.get(key)))
                self.attributes.set(key, value.copy())
            elif isinstance(value, unicode):
                olds.append((key, self.attributes.get(key)))
                self.attributes.set(key, value.encode( 'utf-8' ))
            else:
                olds.append((key, self.attributes.get(key)))
                self.attributes.set(key, value)
        self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (None, kvPairs, olds, Enums.ATTR_SET_MULTIPLE))

    def _setMultiple(self, assocList, olds, kvPairs):
        for (key, value) in kvPairs:
            key = str(key)
            if isinstance(value, tuple):
                old = []
                olds.append((key, old))
                nestedAssocList = assocList.get(key)
                if nestedAssocList is None:
                    nestedAssocList = AssociativeList()
                    assocList.set(key, nestedAssocList)
                self._setMultiple(nestedAssocList, old, value)
            elif isinstance(value, list):
                olds.append((key, assocList.get(key)))
                assocList.set(key, copy.deepcopy(value))
            elif isinstance(value, Vector3):
                olds.append((key, assocList.get(key)))
                assocList.set(key, value.copy())
            elif isinstance(value, unicode):
                olds.append((key, assocList.get(key)))
                assocList.set(key, str(value))
            else:
                olds.append((key, assocList.get(key)))
                assocList.set(key, value)

    def toggle(self, key):
        if isinstance(key, tuple):
            assocList = self.attributes.get(key[0])
            if assocList is None:
                return None
            i = 1
            limit = len(key) - 1
            while i < limit:
                assocList = assocList.get(key[i])
                if assocList is None:
                    return None
                i += 1
            old = assocList.get(key[-1])
            new = assocList.toggle(key[-1])
            self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key, new, old, Enums.ATTR_TOGGLE))
        else:
            key = key.split(".")
            if len(key) is 1:
                old = self.attributes.get(key[0])
                new = self.attributes.toggle(key[0])
                self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key[0], new, old, Enums.ATTR_TOGGLE))
            else:
                self.toggle(tuple(key))

    def inc(self, key, value):
        if isinstance(key, tuple):
            assocList = self.attributes.get(key[0])
            if assocList is None:
                return None
            i = 1
            limit = len(key) - 1
            while i < limit:
                assocList = assocList.get(key[i])
                if assocList is None:
                    return None
                i += 1
            old = assocList.get(key[-1])
            new = assocList.inc(key[-1], value)
            self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key, new, old, Enums.ATTR_INC))
        else:
            key = key.split(".")
            if len(key) is 1:
                old = self.attributes.get(key[0])
                new = self.attributes.inc(key[0], value)
                self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key[0], new, old, Enums.ATTR_INC))
            else:
                self.inc(tuple(key), value)

    def mul(self, key, value):
        if isinstance(key, tuple):
            assocList = self.attributes.get(key[0])
            if assocList is None:
                return None
            i = 1
            limit = len(key) - 1
            while i < limit:
                assocList = assocList.get(key[i])
                if assocList is None:
                    return None
                i += 1
            old = assocList.get(key[-1])
            new = assocList.mul(key[-1], value)
            self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key, new, old, Enums.ATTR_MUL))
        else:
            key = key.split(".")
            if len(key) is 1:
                old = self.attributes.get(key[0])
                new = self.attributes.inc(key[0], value)
                self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key[0], new, old, Enums.ATTR_MUL))
            else:
                self.mul(tuple(key), value)

    def has(self, key):
        if isinstance(key, tuple):
            assocList = self.attributes.get(key[0])
            if assocList is None:
                return None
            i = 1
            limit = len(key) - 1
            while i < limit:
                assocList = assocList.get(key[i])
                if assocList is None:
                    return None
                i += 1
            return assocList.has(key[-1])
        else:
            key = key.split(".")
            if len(key) is 1:
                return self.attributes.has(key[0])
            else:
                return self.has(tuple(key))

    def get(self, key):
        if isinstance(key, tuple):
            assocList = self.attributes.get(key[0])
            if assocList is None:
                return None
            i = 1
            limit = len(key) - 1
            while i < limit:
                assocList = assocList.get(key[i])
                if assocList is None:
                    return None
                i += 1
            return assocList.get(key[-1])
        else:
            key = key.split(".")
            if len(key) is 1:
                return self.attributes.get(key[0])
            else:
                return self.get(tuple(key))

    def remove(self, key):
        if isinstance(key, tuple):
            assocList = self.attributes.get(key[0])
            if assocList is None:
                return None
            i = 1
            limit = len(key) - 1
            while i < limit:
                assocList = assocList.get(key[i])
                if assocList is None:
                    return None
                i += 1
            old = assocList.get(key[-1])
            assocList.remove(key[-1])
            self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key, None, old, Enums.ATTR_REMOVE))
        else:
            key = key.split(".")
            if len(key) is 1:
                old = self.attributes.get(key[0])
                self.attributes.remove(key[0])
                self.entity.localEvent(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, (key[0], None, old, Enums.ATTR_REMOVE))
            else:
                self.remove(tuple(key))

    def getDictionary(self):
        return self.attributes.getDictionary()

    def getNetworkDictionary(self):
        return self._getNetworkDictionary(self.attributes)

    def _getNetworkDictionary(self, assocList):
        d = {}
        for e in assocList.l:
            if isinstance(e[1], Vector3):
                try:
                    d[AttributeEnums[e[0]]] = tuple(e[1])
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
            elif isinstance(e[1], AssociativeList):
                try:
                    d[AttributeEnums[e[0]]] = self._getNetworkDictionary(e[1])
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
            elif isinstance(e[1], list):
                try:
                    d[AttributeEnums[e[0]]] = utils.listToNetworkList(e[1])
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
            else:
                try:
                    d[AttributeEnums[e[0]]] = e[1]
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
        return d

    def printAttributes(self):
        utils.printAssociativeList(self.attributes)


class CombatAttributes(Component):
    """
    CombatAttributes

    Provides an entity with the ability to have modifiers attached to any attribute.
    A modifier can be either added or multiplied with an attribute.

    Requires: Attributes
    """
    strength = ComponentField.IntegerValue(default=1)
    dexterity = ComponentField.IntegerValue(default=1)
    intelligence = ComponentField.IntegerValue(default=1)
    armor = ComponentField.IntegerValue(default=0)
    magicResist = ComponentField.IntegerValue(default=0)
    hitpointsMaximum = ComponentField.IntegerValue(default=20)
    hitpoints = ComponentField.IntegerValue(default=20)
    minimumDamage = ComponentField.IntegerValue(default=1)
    maximumDamage = ComponentField.IntegerValue(default=1)
    attackPeriod = ComponentField.FloatValue(default=1.0)
    attackRange = ComponentField.FloatValue(default=1.0)
    speed = ComponentField.FloatValue(default=1.0)
    sightRange = ComponentField.FloatValue(default=5.0)

    def __init__(self):
        super(CombatAttributes, self).__init__(Enums.COMP_TYPE_COMBATATTRIBUTES)
        self.tokenPool = 0
        self.modifiers = {}  ## TODO need to replace this with list
        self.tokenToKey = {}  ## TODO need to do something about this as well

    def clear(self):
        self.tokenPool = 0
        self.modifiers = {}
        self.tokenToKey = {}

    def initialize(self, args):
        if args is not None:
            for a in args:
                self.addModifier(a[0], a[1], a[2])
        super(CombatAttributes, self).initialize(args)

    def attach(self, entity):
        super(CombatAttributes, self).attach(entity)

    def detach(self):
        super(CombatAttributes, self).detach()
        self._Attributes = None

    def addAttribute(self, key, value):
        self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set(key, value)

    def addModifier(self, key, mod, modType):
        token = self.tokenPool
        self.tokenPool += 1
        self.tokenToKey[token] = (key, modType)
        try:
            mods = self.modifiers[key]
        except KeyError:
            mods = [[], [], [], []]
            self.modifiers[key] = mods
        mods[modType].append((mod, modType, token))
        self.entity.localEvent(Enums.COMP_EVENT_COMBATATTRIBUTE_ADDED, (key, token, mod, modType))
        return token

    def hasModifiers(self, key):
        try:
            mods = self.modifiers[key]
            for modType in mods:
                if len(modType) > 0:
                    return True
        except KeyError:
            pass
        return False

    def removeModifier(self, token):
        try:
            key, modType = self.tokenToKey[token]
            modTypes = self.modifiers[key]
            mods = modTypes[modType]
            for i in xrange(len(mods)):
                if mods[i][2] is token:
                    mod = mods[i][0]
                    modType = mods[i][1]
                    del mods[i]
                    self.entity.localEvent(Enums.COMP_EVENT_COMBATATTRIBUTE_REMOVED, (key, token, mod, modType))
                    return key
        except KeyError:
            return None
        return key

    def queryBaseAttribute(self, key):
        return self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(key)

    def queryEffectiveAttribute(self, key):
        base = self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(key)
        if base is None:
            return None
        try:
            mods = self.modifiers[key]
            modSetOverrides = mods[Enums.MOD_TYPE_SET_OVERRIDE]
            if len(modSetOverrides) > 0:
                for m in modSetOverrides:
                    base = m[0]
            else:
                for m in mods[Enums.MOD_TYPE_SET]:
                    base = m[0]
                for m in mods[Enums.MOD_TYPE_ADD]:
                    base += m[0]
                for m in mods[Enums.MOD_TYPE_MUL]:
                    base *= m[0]
        except KeyError:
            pass
        return base

    def apply(self, key, value):
        self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).apply(key, value)

    def applyMultiple(self, increases):
        self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).applyMultiple(increases)

    # these are here just to mirror attributes
    # TODO: implement this better
    def get(self, key):
        return self.queryEffectiveAttribute(key)

    def set(self, key, value):
        return self.addAttribute(key, value)

    def inc(self, key, value):
        return self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(key, value)

    def mul(self, key, value):
        return self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).mul(key, value)

    def toggle(self, key, value):
        return self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).toggle(key, value)

    def getNetworkDictionary(self):
        return self._getNetworkDictionary([], self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).attributes)

    def _getNetworkDictionary(self, keyChain, assocList):
        d = {}
        for e in assocList.l:
            if isinstance(e[1], Vector3):
                try:
                    d[AttributeEnums[e[0]]] = tuple(e[1])
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
            elif isinstance(e[1], AssociativeList):
                try:
                    d[AttributeEnums[e[0]]] = self._getNetworkDictionary(keyChain + [e[0]], e[1])
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
            elif isinstance(e[1], list):
                try:
                    d[AttributeEnums[e[0]]] = utils.listToNetworkList(e[1])
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
            else:
                try:
                    if self.hasModifiers(e[0]):
                        d[AttributeEnums[e[0]]] = self.get(tuple(keyChain + [e[0]]))
                    else:
                        d[AttributeEnums[e[0]]] = e[1]
                except KeyError:
                    #print "Not found in AttributeEnums: " + str(e)
                    continue
        return d


class Tags(Component):
    """
    Tags

    Provides an entity with the ability to have tags, which can denote characteristics, for example.

    Requires: -
    """
    def __init__(self):
        super(Tags, self).__init__(Enums.COMP_TYPE_TAGS)
        self.tags = []

    def initialize(self, args):
        if args is not None:
            for a in args:
                self.add(a)
        super(Tags, self).initialize(args)

    def clear(self):
        self.tags = []

    def add(self, tag):
        if not self.has(tag):
            self.tags.append(tag)
            self.entity.localEvent(Enums.COMP_EVENT_TAG_ADDED, tag)

    def has(self, tag):
        for t in self.tags:
            if t == tag:
                return True
        return False

    def hasAll(self, tags):
        for t in tags:
            if not self.has(t):
                return False
        return True

    def hasNone(self, tags):
        for t in tags:
            if self.has(t):
                return False
        return True

    def remove(self, tag):
        try:
            self.tags.remove(tag)
            self.entity.localEvent(Enums.COMP_EVENT_TAG_REMOVED, tag)
        except ValueError:
            return

    def getList(self):
        return self.tags


class Transform(Component):
    """
    Transform

    Provides an entity with the ability to have a position, rotation and scale in the world.

    Requires: -
    """
    def __init__(self):
        super(Transform, self).__init__(Enums.COMP_TYPE_TRANSFORM)
        self.position = Vector3(0, 0, 0)
        self.direction = Vector3(1, 0, 0)
        self.scale = Vector3(1, 1, 1)
        self.oldPosition = Vector3(0, 0, 0)
        self.oldDirection = Vector3(1, 0, 0)
        self.oldScale = Vector3(1, 1, 1)

    def initialize(self, args):
        self.direction = Vector3(1, 0, 0)
        self.scale = Vector3(1, 1, 1)
        self.oldPosition = Vector3(0, 0, 0)
        self.oldDirection = Vector3(1, 0, 0)
        self.oldScale = Vector3(1, 1, 1)
        if args is not None:
            self.position = args[0].copy()
        else:
            self.position = Vector3(0, 0, 0)
        super(Transform, self).initialize(args)

    def clear(self):
        self.position = Vector3(0, 0, 0)
        self.direction = Vector3(1, 0, 0)
        self.scale = Vector3(1, 1, 1)
        self.oldPosition = Vector3(0, 0, 0)
        self.oldDirection = Vector3(1, 0, 0)
        self.oldScale = Vector3(1, 1, 1)

    def detach(self):
        super(Transform, self).detach()

    def setParent(self, transform):
        pass

    def setLocalPosition(self, position):
        self.position = position.copy()

    def setLocalX(self, x):
        self.position.x = x

    def setLocalY(self, y):
        self.position.y = y

    def setLocalRotation(self, rotation):
        pass

    def setLocalDirection(self, direction):
        self.direction = direction.copy()

    def setLocalScale(self, scale):
        self.scale = scale.copy()

    def setWorldPosition(self, position):
        self.position = position.copy()

    def setWorldX(self, x):
        self.position.x = x

    def setWorldY(self, y):
        self.position.y = y

    def setWorldRotation(self, rotation):
        pass

    def setWorldDirection(self, direction):
        self.direction = direction.copy()

    def getChildren(self):
        pass

    def getLocalPosition(self):
        return self.position.copy()

    def getLocalRotation(self):
        return None

    def getLocalDirection(self):
        return self.direction.copy()

    def getLocalScale(self):
        return self.scale

    def getWorldPosition(self):
        return self.position.copy()

    def getWorldRotation(self):
        return None

    def getWorldDirection(self):
        return self.direction.copy()

    def getWorldScale(self):
        return self.scale

    def translate(self, vector):
        self.position += vector

    def rotate(self, rotation):
        pass

    def getDistanceToLocalPosition(self, position):
        return (self.position - position).magnitude()

    def getDistanceToWorldPosition(self, position):
        return (self.position - position).magnitude()

    def getDistanceSquaredToLocalPosition(self, position):
        return (self.position - position).magnitude_squared()

    def getDistanceSquaredToWorldPosition(self, position):
        return (self.position - position).magnitude_squared()

    def getDistanceToTransform(self, transform):
        return (self.position - transform.position).magnitude()

    def getDistanceSquaredToTransform(self, transform):
        return (self.position - transform.position).magnitude_squared()

    def getDistanceToEntity(self, entity):
        xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if xform is None:
            return None
        return (self.position - xform.position).magnitude()

    def getDistanceSquaredToEntity(self, entity):
        xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if xform is None:
            return None
        return (self.position - xform.position).magnitude_squared()


class Physical(Component):
    """
    Physical

    Provides an entity with the ability to have physical form in the world that can then be queried using efficient
    spatial queries.

    Requires: Transform
    """
    def __init__(self):
        super(Physical, self).__init__(Enums.COMP_TYPE_PHYSICAL)
        self.shapes = []
        # TODO bounding box

    def initialize(self, args):
        if args is not None:
            for a in args:
                if a[0] is Enums.SHAPE_TYPE_POINT:
                    self.addShape(Enums.SHAPE_TYPE_POINT, center=a[1])
                elif a[0] is Enums.SHAPE_TYPE_CIRCLE:
                    self.addShape(Enums.SHAPE_TYPE_CIRCLE, center=a[1], radius=a[2])
                elif a[0] is Enums.SHAPE_TYPE_AABB:
                    self.addShape(Enums.SHAPE_TYPE_AABB, center=a[1], width=a[2], height=a[3])
        super(Physical, self).initialize(args)

    def clear(self):
        self.shapes = []

    def attach(self, entity):
        super(Physical, self).attach(entity)

    def detach(self):
        super(Physical, self).detach()

    def getSize(self):
        if len(self.shapes) > 0 and self.shapes[0][Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
            return self.shapes[0][Enums.PHYS_CIRCLE_RADIUS]
        return 0.0

    def addShape(self, shapeType, **kwargs):
        shape = None
        if shapeType is Enums.SHAPE_TYPE_POINT:
            shape = (
                Enums.SHAPE_TYPE_POINT,  # the shape of the physical, in this case point
                kwargs["center"].copy()  # the center (origin) of the point
            )
        elif shapeType is Enums.SHAPE_TYPE_CIRCLE:
            shape = (
                Enums.SHAPE_TYPE_CIRCLE,  # shape, in this case circle
                kwargs["center"].copy(),  # the center of the circle
                kwargs["radius"]  # the radius of the circle
            )
        elif shapeType is Enums.SHAPE_TYPE_AABB:
            shape = (
                Enums.SHAPE_TYPE_AABB,  # shape, in this case an axis-aligned bounding box
                kwargs["center"].copy(),  # the center of the AABB, at (width/2, height/2) from the lower left corner of the AABB
                kwargs["width"],  # the width of the AABB
                kwargs["height"]  # the height of the AABB
            )
        if shape is not None:
            self.shapes.append(shape)

    def intersectsPoint(self, worldPos):
        if self.entity is None or self.entity.isDestroyed():
            return False
        pos = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for s in self.shapes:
            if s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_POINT:
                if ((pos + s[Enums.PHYS_CENTER]) - worldPos).magnitude_squared() < Enums.EPSILON_VECTOR_DISTANCE:
                    return True
            elif s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                if pointToCircle(worldPos, pos + s[Enums.PHYS_CENTER], s[Enums.PHYS_CIRCLE_RADIUS]):
                    return True
            elif s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_AABB:
                ## TODO
                pass
        return False

    def intersectsCircle(self, worldPos, radius):
        if self.entity is None or self.entity.isDestroyed():
            return False
        pos = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for s in self.shapes:
            if s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_POINT:
                if pointToCircle(pos + s[Enums.PHYS_CENTER], worldPos, radius):
                    return True
            elif s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                if circleToCircle(pos + s[Enums.PHYS_CENTER], s[Enums.PHYS_CIRCLE_RADIUS], worldPos, radius):
                    return True
            elif s[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_AABB:
                ## TODO
                pass
        return False

    def intersectsAABB(self, lowerLeft, width, height):
        ## TODO
        return False

    def intersectsPhysical(self, physical):
        if self.entity.isDestroyed():
            return False
        pos_self = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        pos_other = physical.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for sh_self in self.shapes:
            if sh_self[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_POINT:
                for sh_other in physical.shapes:
                    if sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_POINT:
                        if ((pos_self + sh_self[Enums.PHYS_CENTER]) - (pos_other + sh_other[Enums.PHYS_CENTER])).magnitude_squared() < Enums.EPSILON_VECTOR_DISTANCE:
                            return True
                    elif sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                        if pointToCircle(pos_self + sh_self[Enums.PHYS_CENTER], pos_other + sh_other[Enums.PHYS_CENTER], sh_other[Enums.PHYS_CIRCLE_RADIUS]):
                            return True
                    elif sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_AABB:
                        cnt = pos_other + sh_other[Enums.PHYS_CENTER]
                        if pointToAABB(pos_self + sh_self[Enums.PHYS_CENTER],
                                       Vector3(cnt.x - sh_other[Enums.PHYS_AABB_WIDTH]/2, cnt.y - sh_other[Enums.PHYS_AABB_HEIGHT]/2),
                                       sh_other[Enums.PHYS_AABB_WIDTH], sh_other[Enums.PHYS_AABB_HEIGHT]):
                            return True
            elif sh_self[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                for sh_other in physical.shapes:
                    if sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_POINT:
                        if pointToCircle(pos_other + sh_other[Enums.PHYS_CENTER], pos_self + sh_self[Enums.PHYS_CENTER], sh_self[Enums.PHYS_CIRCLE_RADIUS]):
                            return True
                    elif sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                        if circleToCircle(pos_self + sh_self[Enums.PHYS_CENTER], sh_self[Enums.PHYS_CIRCLE_RADIUS],
                                          pos_other + sh_other[Enums.PHYS_CENTER], sh_other[Enums.PHYS_CIRCLE_RADIUS]):
                            return True
                    elif sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_AABB:
                        cnt = pos_other + sh_other[Enums.PHYS_CENTER]
                        if circleToAABB(pos_self + sh_self[Enums.PHYS_CENTER], sh_self[Enums.PHYS_CIRCLE_RADIUS],
                                        Vector3(cnt.x - sh_other[Enums.PHYS_AABB_WIDTH]/2, cnt.y - sh_other[Enums.PHYS_AABB_HEIGHT]/2),
                                        sh_other[Enums.PHYS_AABB_WIDTH], sh_other[Enums.PHYS_AABB_HEIGHT]):
                            return True
            elif sh_self[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_AABB:
                for sh_other in physical.shapes:
                    if sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_POINT:
                        ## TODO
                        pass
                    elif sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                        ## TODO
                        pass
                    elif sh_other[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_AABB:
                        ## TODO
                        pass
        return False


class Sensor(Component):
    """
    Sensor

    Provides an entity with the ability to have sensor shapes for querying Physicals in the world.

    Requires: Transform, Attributes
    """
    def __init__(self):
        super(Sensor, self).__init__(Enums.COMP_TYPE_SENSOR)
        self.sensors = []

    def initialize(self, args):
        if args is not None:
            for a in args:
                if a[0] is Enums.SHAPE_TYPE_POINT:
                    self.addSensor(
                        Enums.SHAPE_TYPE_POINT,
                        a[1],
                        center=a[2].copy()
                    )
                elif a[0] is Enums.SHAPE_TYPE_CIRCLE:
                    self.addSensor(
                        Enums.SHAPE_TYPE_CIRCLE,
                        a[1],
                        center=a[2].copy(),
                        radius=a[3]
                    )
                elif a[0] is Enums.SHAPE_TYPE_AABB:
                    self.addSensor(
                        Enums.SHAPE_TYPE_AABB,
                        a[1],
                        center=a[2].copy(),
                        width=a[3],
                        height=a[4]
                    )
        super(Sensor, self).initialize(args)

    def clear(self):
        self.sensors = []

    def attach(self, entity):
        super(Sensor, self).attach(entity)

    def detach(self):
        super(Sensor, self).detach()

    def hasSensor(self, name):
        for s in self.sensors:
            if s[Enums.SENSOR_NAME] == name:
                return True
        return False

    def addSensor(self, sensorType, name=None, **kwargs):  ## TODO trigger callback implementation
        shape = None
        if sensorType is Enums.SHAPE_TYPE_POINT:
            shape = [
                Enums.SHAPE_TYPE_POINT,  # shape of the sensor, in this case point
                name,  # sensor name, can be None
                kwargs["center"]  # the center (origin) of the point shape
            ]
        elif sensorType is Enums.SHAPE_TYPE_CIRCLE:
            rad = kwargs["radius"]
            if isinstance(rad, str) or isinstance(rad, unicode):
                rad = str(rad)
            shape = [
                Enums.SHAPE_TYPE_CIRCLE,  # shape, in this case circle
                name,  # name
                kwargs["center"],  # the center of the circle shape
                rad  # the radius of the circle shape
            ]
        elif sensorType is Enums.SHAPE_TYPE_AABB:
            shape = [
                Enums.SHAPE_TYPE_AABB,  # shape, in this case an axis-aligned bounding box
                name,  # name
                kwargs["center"],  # the center point of the AABB, at (width/2, height/2) from the lower left corner of the AABB
                kwargs["width"],  # the width of the AABB
                kwargs["height"]  # the height of the AABB
            ]
        if shape is not None:
            self.sensors.append(shape)

    def intersectsPhysicals(self, sensorName, world, fltr=None):
        if self.entity.isDestroyed():
            return False
        pos = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        phys = self.entity.getComponent(Enums.COMP_TYPE_PHYSICAL)
        filters = []
        if isinstance(fltr, list):
            filters += fltr
        elif fltr is not None:
            filters.append(fltr)
        if phys is not None:
            filters.append(lambda p: p is not phys)
        for s in self.sensors:
            if s[Enums.SENSOR_NAME] != sensorName:
                continue
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_POINT:
                query = world.queryPhysicalsByPoint(pos + s[Enums.SENSOR_CENTER])
                for f in filters:
                    query = filter(f, query)
                    if len(query) is 0:
                        break
                if len(query) > 0:
                    return True
            elif s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                radius = s[Enums.SENSOR_CIRCLE_RADIUS]
                if isinstance(radius, str) or isinstance(radius, tuple):
                    if self.entity.hasComponent( Enums.COMP_TYPE_COMBATATTRIBUTES ):
                        radius = self.entity.getComponent( Enums.COMP_TYPE_COMBATATTRIBUTES).queryEffectiveAttribute( radius )
                    else:
                        radius = self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(radius)
                query = world.queryPhysicalsByCircle(pos + s[Enums.SENSOR_CENTER], radius)
                for f in filters:
                    query = filter(f, query)
                    if len(query) is 0:
                        break
                if len(query) > 0:
                    return True
            elif s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_AABB:
                ## TODO
                pass
        return False

    def queryPhysicals(self, sensorName, world, fltr=None):
        if self.entity.isDestroyed():
            return []
        pos = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        phys = self.entity.getComponent(Enums.COMP_TYPE_PHYSICAL)
        filters = []
        if isinstance(fltr, list):
            filters += fltr
        elif fltr is not None:
            filters.append(fltr)
        if phys is not None:
            filters.append(lambda p: p is not phys)
        physicals = []
        for s in self.sensors:
            if s[Enums.SENSOR_NAME] != sensorName:
                continue
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_POINT:
                query = world.queryPhysicalsByPoint(pos + s[Enums.SENSOR_CENTER])
                for f in filters:
                    query = filter(f, query)
                    if len(query) is 0:
                        break
                for p in query:
                    if p not in physicals:
                        physicals.append(p)
                continue
            elif s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                radius = s[Enums.SENSOR_CIRCLE_RADIUS]
                if isinstance(radius, str) or isinstance(radius, tuple):
                    radius = self.entity.getAttributes().get(radius)
                query = world.queryPhysicalsByCircle(pos + s[Enums.SENSOR_CENTER], radius)
                for f in filters:
                    query = filter(f, query)
                    if len(query) is 0:
                        break
                for p in query:
                    if p not in physicals:
                        physicals.append(p)
                continue
            elif s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_AABB:
                ## TODO
                pass
        return physicals


    def intersectsPoint(self, sensorName, worldPos):
        pos = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for s in self.sensors:
            if s[Enums.SENSOR_NAME] != sensorName:
                continue
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_POINT:
                if ((pos + s[Enums.SENSOR_CENTER]) - worldPos).magnitude_squared < Enums.EPSILON_VECTOR_DISTANCE:
                    return True
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                sensorRadius =  self.entity.getAttribute(s[Enums.SENSOR_CIRCLE_RADIUS]) if isinstance(s[Enums.SENSOR_CIRCLE_RADIUS], str) or isinstance(s[Enums.SENSOR_CIRCLE_RADIUS], tuple) else s[Enums.SENSOR_CIRCLE_RADIUS]
                if pointToCircle(worldPos, pos + s[Enums.SENSOR_CENTER], sensorRadius):
                    return True
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_AABB:
                ## TODO
                continue
        return False


    def intersectsCircle(self, sensorName, worldPos, radius):
        pos = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for s in self.sensors:
            if s[Enums.SENSOR_NAME] != sensorName:
                continue
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_POINT:
                if pointToCircle(pos + s[Enums.SENSOR_CENTER], worldPos, radius):
                    return True
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                sensorRadius =  self.entity.getAttribute(s[Enums.SENSOR_CIRCLE_RADIUS]) if isinstance(s[Enums.SENSOR_CIRCLE_RADIUS], str) or isinstance(s[Enums.SENSOR_CIRCLE_RADIUS], tuple) else s[Enums.SENSOR_CIRCLE_RADIUS]
                if circleToCircle(worldPos, radius, pos + s[Enums.SENSOR_CENTER], sensorRadius):
                    return True
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_AABB:
                ## TODO
                continue
        return False


    def intersectsPhysical(self, sensorName, physical):
        pos = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        for s in self.sensors:
            if s[Enums.SENSOR_NAME] != sensorName:
                continue
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_POINT:
                if physical.intersectsPoint(pos + s[Enums.SENSOR_CENTER]):
                    return True
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                sensorRadius =  self.entity.getAttribute(s[Enums.SENSOR_CIRCLE_RADIUS]) if isinstance(s[Enums.SENSOR_CIRCLE_RADIUS], str) or isinstance(s[Enums.SENSOR_CIRCLE_RADIUS], tuple) else s[Enums.SENSOR_CIRCLE_RADIUS]
                if physical.intersectsCircle(pos + s[Enums.SENSOR_CENTER], sensorRadius):
                    return True
            if s[Enums.SENSOR_SHAPE] is Enums.SHAPE_TYPE_AABB:
                ## TODO
                continue
        return False


    def intersectsEntity(self, sensorName, entity):
        phys = entity.getComponent(Enums.COMP_TYPE_PHYSICAL)
        if phys:
            return self.intersectsPhysical(sensorName, phys)
        entityPos = entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition()
        return self.intersectsPoint(sensorName, entityPos)


class Mover(Component):
    """
    Mover

    Provides an entity with basic linear movement capabilities. Movement can be either destination limited or
    infinite. In both cases the entity will begin vectoring in a single direction.

    Requires: Transform, Attributes
    """
    def __init__(self):
        super(Mover, self).__init__(Enums.COMP_TYPE_MOVER)
        self.destination = None
        self.moving = False
        self.speed = 1.0
        self._projectileAscending = False  # This is used for projectile movement calculations in MoverSystem

    def initialize(self, args):
        if args is not None:
            self.setDirection(args[0])
        else:
            self.destination = None
            self.sleep()
        self.updateSpeed()
        super(Mover, self).initialize(args)

    def clear(self):
        self._projectileAscending = False
        self.destination = None
        self.moving = False
        if self.entity:
            self.updateSpeed()

    def updateSpeed(self):
        combatAttributes = self.entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
        if combatAttributes:
            dexterity = combatAttributes.queryEffectiveAttribute(("Stats", "Dexterity"))
            speed = combatAttributes.queryEffectiveAttribute("Speed")
            self.speed = (speed if speed else 1) + (dexterity*.01 if dexterity else 0)
        else:
            attributes = self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            if attributes:
                dexterity = attributes.get(("Stats", "Dexterity"))
                speed = attributes.get("Speed")
                self.speed = (speed if speed else 1) + (dexterity*.01 if dexterity else 0)

    def attach(self, entity):
        super(Mover, self).attach(entity)
        self.entity.attachEventCallback(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, self.onAttributesChanged)
        self.entity.attachEventCallback(Enums.COMP_EVENT_COMBATATTRIBUTE_ADDED, self.onAttributesChanged)
        self.entity.attachEventCallback(Enums.COMP_EVENT_COMBATATTRIBUTE_REMOVED, self.onAttributesChanged)

    def detach(self):
        entity = self.entity
        super(Mover, self).detach()
        entity.detachEventCallback(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, self.onAttributesChanged)
        entity.detachEventCallback(Enums.COMP_EVENT_COMBATATTRIBUTE_ADDED, self.onAttributesChanged)
        entity.detachEventCallback(Enums.COMP_EVENT_COMBATATTRIBUTE_REMOVED, self.onAttributesChanged)

    def sleep(self):
        super(Mover, self).sleep()
        self.entity.localEvent(Enums.COMP_EVENT_MOVEMENT_ENDED)

    def awake(self):
        super(Mover, self).awake()
        if self.isMoving():
            self.entity.localEvent(Enums.COMP_EVENT_MOVEMENT_STARTED)

    def onAttributesChanged(self, eventType, (key, new, old, changeType)):
        if eventType is Enums.COMP_EVENT_ATTRIBUTES_CHANGED:
            if changeType is Enums.ATTR_SET_MULTIPLE:
                speedChange = False
                for (k, v) in new:
                    if k == "Speed":
                        speedChange = True
                        self.updateSpeed()
                if speedChange:
                    self.onSpeedChange()
            elif key == "Speed":
                self.updateSpeed()
                self.onSpeedChange()
        else:
            if key == "Speed":
                self.speed = self.entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES).queryEffectiveAttribute(key)
                self.onSpeedChange()

    def stop(self):
        if self.isMoving():
            self.destination = None
            self.moving = False
            self.sleep()

    def isMoving(self):
        if self.hasStatus(Enums.COMP_STATUS_AWAKE):
            if self.speed > 0.0:
                return self.moving
        return False

    def hasDestination(self):
        return self.destination is not None

    def teleport(self, destination):
        transform = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if transform:
            self.stop()
            transform.setWorldPosition(destination)
            self.entity.localEvent(Enums.COMP_EVENT_MOVEMENT_TELEPORT, destination)

    def setDestination(self, destination):
        if self.entity.isDestroyed():
            return
        transform = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if transform:
            if self.atPosition(destination):
                return
            self.destination = destination.copy()
            self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).setWorldDirection(
                (destination - transform.getWorldPosition()).normalized()
            )
            self.moving = True
            self.awake()

    def setDirectionAndMove(self, direction):
        if self.entity.isDestroyed():
            return
        self.destination = None
        self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).setWorldDirection(direction)
        self.moving = True
        self.awake()

    def setDirection(self, direction):
        self.stop()
        self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM).setWorldDirection(direction)
        self.entity.localEvent(Enums.COMP_EVENT_MOVEMENT_DIRECTION)

    def onSpeedChange(self):
        self.entity.localEvent(Enums.COMP_EVENT_MOVEMENT_SPEED)

    def atDestination(self):
        if self.destination is None:
            return True
        transform = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if transform:
            return (self.destination - transform.getWorldPosition()).magnitude_squared() < Enums.EPSILON_VECTOR_DISTANCE
        return False

    def atPosition(self, position):
        transform = self.entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if transform:
            return (position - transform.getWorldPosition()).magnitude_squared() < Enums.EPSILON_VECTOR_DISTANCE
        return False


class WaypointMover(Component):
    """
    WaypointMover

    Provides an entity with waypoint movement capabilities. A waypoint-list can be set and the entity will travel
    through all waypoints.

    Requires: Mover
    """
    def __init__(self):
        super(WaypointMover, self).__init__(Enums.COMP_TYPE_WAYPOINTMOVER)
        self.waypoints = []
        self.currentWaypointIndex = -1
        self.paused = False

    def initialize(self, args):
        if args is not None:
            self.setWaypoints(args[0])
        super(WaypointMover, self).initialize(args)

    def clear(self):
        self.waypoints = []
        self.currentWaypointIndex = -1
        self.paused = False

    def attach(self, entity):
        super(WaypointMover, self).attach(entity)

    def detach(self):
        super(WaypointMover, self).detach()
        self.waypoints = []

    def pause(self):
        if self.paused:
            return
        self.entity.getComponent(Enums.COMP_TYPE_MOVER).stop()
        self.paused = True

    def unpause(self):
        if not self.paused:
            return
        if self.hasNextWaypoint():
            self.entity.getComponent(Enums.COMP_TYPE_MOVER).setDestination(self.currentWaypoint())
        self.paused = False

    def setWaypoints(self, waypoints):
        if self.entity.isDestroyed():
            return
        if waypoints is None or len(waypoints) is 0:
            self.clearWaypoints()
            return
        self.waypoints = waypoints
        self.currentWaypointIndex = 0
        self.awake()
        self.entity.getComponent(Enums.COMP_TYPE_MOVER).setDestination(self.currentWaypoint())
        self.entity.localEvent(Enums.COMP_EVENT_PATH_STARTED)

    def clearWaypoints(self):
        self.waypoints = []
        self.currentWaypointIndex = -1
        self.sleep()
        self.entity.localEvent(Enums.COMP_EVENT_PATH_ENDED)

    def hasWaypoint(self):
        return 0 <= self.currentWaypointIndex < len(self.waypoints)

    def currentWaypoint(self):
        return self.waypoints[self.currentWaypointIndex]

    def hasNextWaypoint(self):
        return self.currentWaypointIndex + 1 < len(self.waypoints)

    def nextWaypoint(self):
        self.currentWaypointIndex += 1
        return self.waypoints[self.currentWaypointIndex]


class Effect(Component):
    """
    Effect

    Provides an entity with the ability to have named effects, which can be launched at given targets from processes,
    timer functions, event handlers or other effect functions.

    Requires: -
    """
    def __init__(self):
        super(Effect, self).__init__(Enums.COMP_TYPE_EFFECT)
        self.effects = []

    def initialize(self, args):
        if args is not None:
            for a in args:
                self.addEffect(a[0], a[1])
        super(Effect, self).initialize(args)

    def clear(self):
        self.effects = []

    def addEffect(self, name, effectFunction):
        if isinstance(effectFunction, str):
            try:
                self.effects.append((
                    name,
                    getattr(PredefinedFunctions, effectFunction)
                ))
            except AttributeError:
                raise ComponentError("Attempting to attach effect function %s for effect %s but there is no predef for it!" % (effectFunction, name), self)
        else:
            self.effects.append((
                name,
                effectFunction
            ))

    def getEffect(self, name):
        index = -1
        i = 0
        while i < len(self.effects):
            if self.effects[i][Enums.EFFECT_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return None
        return self.effects[index]

    def launchEffect(self, name, world, targets):
        if self.entity.isDestroyed():
            return
        for effect in self.effects:
            if effect[Enums.EFFECT_NAME] == name:
                effect[Enums.EFFECT_FUNCTION](self.entity, world, targets)
        self.entity.localEvent(Enums.COMP_EVENT_EFFECT_LAUNCHED, (name, targets))


class FSM(Component):
    """
    FSM

    Provides an entity with the ability to have managed states, each with an update function.

    Requires: Attributes, EventIO
    """
    def __init__(self):
        super(FSM, self).__init__(Enums.COMP_TYPE_FSM)
        self.updatePeriod = 0.0
        self.timer = 0.0
        self.state = "Idle"
        self.sleep()

    def initialize(self, args):
        if args is not None:
            self.setState(args[0])
            self.setUpdatePeriod(args[1])
        else:
            self.setState("Idle")
            self.setUpdatePeriod(0.0)
        super(FSM, self).initialize(args)

    def attach(self, entity):
        super(FSM, self).attach(entity)
        entity.attachEventCallback(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, self.onAttributesChanged)
        if entity.hasComponent(Enums.COMP_TYPE_ATTRIBUTES):
            self.updatePeriod = self.entity.getAttribute("Update period")
        self.awake()

    def detach(self):
        entity = self.entity
        self.sleep()
        super(FSM, self).detach()
        entity.detachEventCallback(Enums.COMP_EVENT_ATTRIBUTES_CHANGED, self.onAttributesChanged)

    def initialize(self, args):
        super(FSM, self).initialize(args)

    def setState(self, state):
        attr = self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            oldState = attr.get("State")
            if state != oldState:
                ## TODO implement state exit and enter functions
                attr.set("State", state)
        self.state = state

    def setUpdatePeriod(self, period):
        attr = self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            attr.set("Update period", period)
        self.updatePeriod = period

    def onAttributesChanged(self, eventType, (key, new, old, changeType)):
        attr = self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        self.state = attr.get("State")
        self.updatePeriod = attr.get("Update period")


class Process(Component):
    """
    Process

    Provides an entity with the ability to have named processes, which will tick at given rates. Processes can be
    higher level AI functions, or they can be simple ability drivers checking cooldown timers and launching effects.

    Requires: -
    """
    def __init__(self):
        super(Process, self).__init__(Enums.COMP_TYPE_PROCESS)
        self.processes = []
        self.sleep()

    def initialize(self, args):
        if args is not None:
            for a in args:
                self.addProcess(a[0], a[1], a[2])
        super(Process, self).initialize(args)

    def addProcess(self, name, processFunction, period):
        try:
            proc = [
                name,  # the name of this process

                getattr(PredefinedFunctions, processFunction) if isinstance(processFunction, str) else processFunction,  # the process function

                period,  # period counter

                period,  # period, i.e. once per how many frames the process ticks

                Enums.PROC_STATUS_NULL,  # the initial status of this process

                0  # tick count, i.e. how many times this process has been run
            ]
        except AttributeError:
            raise ComponentError("Attempting to attach process function %s for process %s but there is no predef for it!" % (processFunction, name), self)
        for i in xrange(len(self.processes)):
            if self.processes[i][Enums.PROC_NAME] == name:
                self.processes[i] = proc
                self.awake()
                self.entity.localEvent(Enums.COMP_EVENT_PROCESS_STARTED, name)
                return
        self.processes.append(proc)
        self.awake()
        self.entity.localEvent(Enums.COMP_EVENT_PROCESS_STARTED, name)

    def removeProcess(self, name):
        index = -1
        for i in xrange(len(self.processes)):
            if self.processes[i][Enums.PROC_NAME] == name:
                index = i
                break
        if index < 0:
            return
        del self.processes[index]
        if len(self.processes) is 0:
            self.sleep()
        self.onProcessEnded(name)

    def onProcessEnded(self, name):
        self.entity.localEvent(Enums.COMP_EVENT_PROCESS_ENDED, name)

    def getProcess(self, name):
        for p in self.processes:
            if p[Enums.PROC_NAME] == name:
                return p
        return None

    def getProcessPeriod(self, name):
        for p in self.processes:
            if p[Enums.PROC_NAME] == name:
                return p[Enums.PROC_PERIOD]
        return None

    def setProcessPeriod(self, name, period):
        for p in self.processes:
            if p[Enums.PROC_NAME] == name:
                p[Enums.PROC_PERIOD] = period
                p[Enums.PROC_PERIOD_COUNTER] = period
                return

    def terminateProcess(self, name):
        for p in self.processes:
            if p[Enums.PROC_NAME] == name:
                p[Enums.PROC_STATUS] |= Enums.PROC_STATUS_TERMINATED
                return

    def clear(self):
        self.processes = []
        self.sleep()

    def pauseProcess(self, name):
        for proc in self.processes:
            if proc[Enums.PROC_NAME] == name:
                proc[Enums.PROC_STATUS] |= Enums.PROC_STATUS_PAUSED
                return

    def unpauseProcess(self, name):
        for proc in self.processes:
            if proc[Enums.PROC_NAME] == name:
                proc[Enums.PROC_STATUS] &= ~Enums.PROC_STATUS_PAUSED
                return

    def unpauseAllProcesses(self):
        for proc in self.processes:
            proc[Enums.PROC_STATUS] &= ~Enums.PROC_STATUS_PAUSED


class EventIO(Component):
    """
    EventIO

    Provides an entity with the ability to send and receive events from other entities.

    Requires: -
    """
    def __init__(self):
        super(EventIO, self).__init__(Enums.COMP_TYPE_EVENTIO)
        self.handlers = {}
        self.events = []
        self.sleep()

    def clear(self):
        self.handlers = {}
        self.events = []
        self.sleep()

    def clearEventBuffer(self):
        self.events = []
        self.sleep()

    def initialize(self, args):
        if args is not None:
            for a in args:
                self.attachHandler(a[0], a[1])
        super(EventIO, self).initialize(args)

    def attachHandler(self, eventType, handler):
        if isinstance(handler, str):
            try:
                self.handlers[eventType] = getattr(PredefinedFunctions, handler)
            except AttributeError:
                raise ComponentError("Attempting to attach handler %s for event %s but there is no predef for it!" % (handler, eventType), self)
        elif isinstance(handler, list):
            handlers = []
            for h in handler:
                try:
                    t = getattr(PredefinedFunctions, h)
                    handlers.append(t)
                except AttributeError:
                    raise ComponentError("Attempting to attach handler %s for event %s but there is no predef for it!" % (h, eventType), self)
            self.handlers[eventType] = handlers
        else:
            self.handlers[eventType] = handler

    def getHandler(self, eventType):
        try:
            return self.handlers[eventType]
        except KeyError:
            return None

    def receiveImmediateEvent(self, eventType, world, data=None):
        """
        This processes an event immediately in-place as if it were "inlined". Use with caution, and if possible, use
        receiveEvent instead as it buffers events and processes them in a separate step.

        This method also returns any value the handler returns, which can be used for shortcuts. Again, use with caution
        and avoid if possible.
        """
        if self.entity.isDestroyed():
            return
        if eventType[0] == "_":
            if eventType == "_destroy":
                world.destroyEntity(self.entity)
        else:
            handler = self.getHandler(eventType)
            if handler:
                return handler(self.entity, world, data)

    def receivePriorityEvent(self, eventType, data=None):
        if self.entity.isDestroyed():
            return
        self.events.insert(0, (eventType, data))
        self.awake()
        self.entity.localEvent(Enums.COMP_EVENT_EVENT_RECEIVED, (eventType, data))

    def receiveEvent(self, eventType, data=None):
        if self.entity.isDestroyed() or eventType is None:
            return
        self.events.append((eventType, data))
        self.awake()
        self.entity.localEvent(Enums.COMP_EVENT_EVENT_RECEIVED, (eventType, data))

    def sendEvent(self, entities, eventType, data=None):
        if self.entity.isDestroyed():
            return
        if not isinstance(entities, list) and not isinstance(entities, tuple):
            entities = [entities]
        for e in entities:
            eventIO = e.getComponent(Enums.COMP_TYPE_EVENTIO)
            if eventIO is not None:
                eventIO.receiveEvent(eventType, data)
        self.entity.localEvent(Enums.COMP_EVENT_EVENT_SENT, (eventType, data))

    def onProcessEvent(self, eventType, data):
        self.entity.localEvent(Enums.COMP_EVENT_EVENT_PROCESSED, (eventType, data))


class Timer(Component):
    """
    Timer

    Provides an entity with the ability to have named timers. When a timer triggers it emits an event.

    Requires: Attributes, EventIO
    """
    def __init__(self):
        super(Timer, self).__init__(Enums.COMP_TYPE_TIMER)
        self.timers = []
        self._nextAnon = 0

    def clear(self):
        self.timers = []

    def initialize(self, args):
        if args is not None:
            for a in args:
                if len(a) == 5:
                    self.addTimer(a[0], a[1], a[2], a[3], a[4])
                else:
                    self.addTimer(a[0], a[1], a[2], a[3])
        super(Timer, self).initialize(args)

    def addAnonymousTimer(self, eventType, triggerLimit, time, data=None):
        self.addTimer("_" + str(self._nextAnon), eventType, triggerLimit, time, data)
        self._nextAnon += 1

    def addTimer(self, name, eventType, triggerLimit, time, data=None):
        if self.entity.isDestroyed():
            return
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                del self.timers[i]
                continue
            i += 1
        if isinstance(time, unicode):
            time = str(time)
        elif isinstance(time, list) or isinstance(time, tuple):
            time = utils.dbStringListToTuple(time)
        if isinstance(time, str) or isinstance(time, tuple):
            attr = self.entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            combatAttr = self.entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
            if combatAttr:
                currentTime = combatAttr.queryEffectiveAttribute(time)
            else:
                currentTime = attr.get(time)
        else:
            currentTime = time
        timer = [
            name,  # all timers need a name, and timers with the same name will replace each other

            eventType,  # the event that is emitted on trigger

            0,  # how many times this timer has triggered

            triggerLimit,  # how many times it will trigger, -1 means forever

            currentTime,  # current countdown in seconds

            time,  # countdown start, which is either a float or a string

            Enums.TIMER_STATUS_NULL,  # the status bitmask, initially all zero

            data
        ]
        if currentTime is None:
            raise ComponentError( "AddTimer with no time: %s, %s, %s, %s" % (name, eventType, str(triggerLimit), str(time)), self )
            return
        for i in xrange(len(self.timers)):
            if timer[Enums.TIMER_CURRENT_COUNTDOWN] <= self.timers[i][Enums.TIMER_CURRENT_COUNTDOWN]:
                self.timers.insert(i, timer)
                break
        else:
            self.timers.append(timer)
        self.awake()

    def getTimer(self, name):
        index = -1
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return None
        return self.timers[index]

    def hasTimer(self, name):
        for t in self.timers:
            if t[Enums.TIMER_NAME] == name:
                return True
        return False

    def getTimerTriggerCount(self, name):
        index = -1
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return None
        return self.timers[index][Enums.TIMER_TRIGGER_COUNT]

    def hasTriggered(self, name):
        index = -1
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return None
        return self.timers[index][Enums.TIMER_TRIGGER_COUNT] > 0

    def hasEnded(self, name):
        index = -1
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return None
        return self.timers[index][Enums.TIMER_STATUS] & Enums.TIMER_STATUS_ENDED

    def pauseTimer(self, name):
        index = -1
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return
        self.timers[index][Enums.TIMER_STATUS] |= Enums.TIMER_STATUS_PAUSED

    def unpauseTimer(self, name):
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                timer = self.timers[i]
                del self.timers[i]
                break
            i += 1
        else:
            return
        timer[Enums.TIMER_STATUS] &= ~Enums.TIMER_STATUS_PAUSED
        for i in xrange(len(self.timers)):
            if timer[Enums.TIMER_CURRENT_COUNTDOWN] <= self.timers[i][Enums.TIMER_CURRENT_COUNTDOWN]:
                self.timers.insert(i, timer)
                break
        else:
            self.timers.append(timer)
        self.awake()

    def resetTimer(self, name):
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                timer = self.timers[i]
                del self.timers[i]
                break
            i += 1
        else:
            return
        time = timer[Enums.TIMER_COUNTDOWN_START]
        if isinstance(time, str) or isinstance(time, tuple):
            time = self.entity.getAttributes().get(time)
        timer[Enums.TIMER_CURRENT_COUNTDOWN] = time
        timer[Enums.TIMER_TRIGGER_COUNT] = 0
        timer[Enums.TIMER_STATUS] = Enums.TIMER_STATUS_NULL
        for i in xrange(len(self.timers)):
            if timer[Enums.TIMER_CURRENT_COUNTDOWN] <= self.timers[i][Enums.TIMER_CURRENT_COUNTDOWN]:
                self.timers.insert(i, timer)
                break
        else:
            self.timers.append(timer)
        self.awake()

    def resetTimerTriggerCount(self, name):
        index = -1
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return
        timer = self.timers[index]
        timer[Enums.TIMER_TRIGGER_COUNT] = 0
        self.awake()

    def triggerTimer(self, name):
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                timer = self.timers[i]
                del self.timers[i]
                break
            i += 1
        else:
            return
        timer[Enums.TIMER_CURRENT_COUNTDOWN] = 0.0
        for i in xrange(len(self.timers)):
            if timer[Enums.TIMER_CURRENT_COUNTDOWN] <= self.timers[i][Enums.TIMER_CURRENT_COUNTDOWN]:
                self.timers.insert(i, timer)
                break
        else:
            self.timers.append(timer)

    def removeTimer(self, name):
        index = -1
        i = 0
        while i < len(self.timers):
            if self.timers[i][Enums.TIMER_NAME] == name:
                index = i
                break
            i += 1
        if index < 0:
            return
        self.timers[index][Enums.TIMER_STATUS] |= Enums.TIMER_STATUS_REMOVED
        self.awake()


class Predicate(Component):
    def __init__(self):
        super(Predicate, self).__init__(Enums.COMP_TYPE_PREDICATE)
        self.predicates = []

    def clear(self):
        self.predicates = []

    def initialize(self, args):
        if args is not None:
            for a in args:
                self.addPredicate(a[0], a[1], a[2], a[3], a[4])
        super(Predicate, self).initialize(args)

    def addPredicate(self, name, eventType, triggerLimit, period, predicateFunction, data=None):
        i = 0
        while i < len(self.predicates):
            if self.predicates[i][Enums.PRED_NAME] == name:
                del self.predicates[i]
                break
            i += 1
        if isinstance(predicateFunction, str):
            try:
                predicateFunction = getattr(PredefinedFunctions, predicateFunction)
            except AttributeError:
                raise ComponentError("Attempting to attach predicate function %s for predicate %s but there is no predef for it!" % (predicateFunction, name), self)
        predicate = [
            name,  # The name of the predicate.

            eventType,  # The event the predicate will emit to this entity upon triggering.

            0,  # The number of times this predicate has triggered.

            triggerLimit,  # The number of times the predicate will trigger before it is removed, -1 means forever.

            period,  # The remaining time before the predicate condition will be checked.

            period,  # The period how often the predicate condition will be check.

            predicateFunction,  # The predicate condition function. Will return either True (which means triggering) or False.

            data  # Data to be passed to the event handler.
        ]
        self.predicates.append(predicate)
        self.awake()

    def removePredicate(self, name):
        i = 0
        while i < len(self.predicates):
            if self.predicates[i][Enums.PRED_NAME] == name:
                del self.predicates[i]
                break
            i += 1
        if len(self.predicates) is 0:
            self.sleep()


class Network(Component):
    def __init__(self):
        super(Network, self).__init__(Enums.COMP_TYPE_NETWORK)
        self.listenEvents = [
            Enums.COMP_EVENT_ATTRIBUTES_CHANGED,
            Enums.COMP_EVENT_COMBATATTRIBUTE_ADDED,
            Enums.COMP_EVENT_COMBATATTRIBUTE_REMOVED,
            Enums.COMP_EVENT_TAG_ADDED,
            Enums.COMP_EVENT_TAG_REMOVED,
            Enums.COMP_EVENT_MOVEMENT_STARTED,
            Enums.COMP_EVENT_MOVEMENT_SPEED,
            Enums.COMP_EVENT_MOVEMENT_DIRECTION,
            Enums.COMP_EVENT_MOVEMENT_ENDED,
            Enums.COMP_EVENT_MOVEMENT_TELEPORT,
            Enums.COMP_EVENT_EFFECT_LAUNCHED
        ]
        self.eventBuffer = []

    def clear(self):
        self.eventBuffer = []

    def initialize(self, args):
        pass

    def attach(self, entity):
        super(Network, self).attach(entity)

        assert(self.entity is not None)
        [entity.attachEventCallback(e, self.eventCallback) for e in self.listenEvents]

    def detach(self):
        entity = self.entity
        super(Network, self).detach()
        [entity.detachEventCallback(e, self.eventCallback) for e in self.listenEvents]

    def eventCallback(self, event, data):
        if self.initialized:
            self.eventBuffer.append((event, data))


COMP_TYPES = [
    Transform,
    Physical,
    Sensor,
    Attributes,
    Tags,
    CombatAttributes,
    Mover,
    WaypointMover,
    Effect,
    Process,
    FSM,
    EventIO,
    Timer,
    Predicate,
    Network,
]


COMP_TYPE_COUNT = len(COMP_TYPES)