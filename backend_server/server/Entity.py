from Component import *
import Enums


class Entity(object):
    def __init__(self, id):
        self.id = id
        self.destroyed = 0
        self.eventCallbacks = [[] for i in xrange(Enums.COMP_EVENT_COUNT)]
        self.components = [None for i in xrange(COMP_TYPE_COUNT)]

    def getName(self):
        attributes = self.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attributes:
            subtype = attributes.get("Subtype")
            if subtype:
                return subtype + ("#%d" % (self.id,))
        return "Entity#%d" % (self.id,)

    def getPosition(self):
        xform = self.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if xform:
            return xform.getWorldPosition()
        return None

    def getDirection(self):
        xform = self.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if xform:
            return xform.getWorldDirection()
        return None

    def getSize(self):
        phys = self.getComponent(Enums.COMP_TYPE_PHYSICAL)
        if phys:
            if len(phys.shapes) > 0:
                shape = phys.shapes[0]
                if shape[Enums.PHYS_SHAPE] is Enums.SHAPE_TYPE_CIRCLE:
                    return shape[Enums.PHYS_CIRCLE_RADIUS]
        return None

    def getAttribute(self, key):
        attr = self.getAttributes()
        if attr:
            return attr.get(key)
        return None

    def setAttribute(self, key, value):
        attr = self.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            attr.set(key, value)

    def incAttribute(self, key, value):
        attr = self.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            attr.inc(key, value)

    def mulAttribute(self, key, value):
        attr = self.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            attr.mul(key, value)

    def toggleAttribute(self, key, value):
        attr = self.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if attr:
            attr.toggle(key, value)

    def hasTag(self, tag):
        tags = self.getComponent(Enums.COMP_TYPE_TAGS)
        if tags:
            return tags.has(tag)
        return False

    def hasAllOfTags(self, tags):
        tg = self.getComponent(Enums.COMP_TYPE_TAGS)
        if tg:
            return tg.hasAll(tags)
        return len(tags) is 0

    def hasOneOfTags(self, tags):
        if tags is None or len(tags) is 0:
            return True
        tg = self.getComponent(Enums.COMP_TYPE_TAGS)
        if tg:
            for t in tags:
                if tg.has(t):
                    return True
        return False

    def hasNoneOfTags(self, tags):
        tg = self.getComponent(Enums.COMP_TYPE_TAGS)
        if tg:
            return tg.hasNone(tags)
        return True

    def receiveEvent(self, eventType, data=None):
        eventIO = self.getComponent(Enums.COMP_TYPE_EVENTIO)
        if eventIO:
            eventIO.receiveEvent(eventType, data)

    def attachComponent(self, component):
        self.components[component.type] = component
        component.attach(self)

    def detachComponent(self, componentType):
        component = self.components[componentType]
        if component:
            component.detach()
            self.components[componentType] = None

    def deactivateAllComponents(self):
        for c in self.components:
            if c:
                c.deactivate()

    def activateAllComponents(self):
        for c in self.components:
            if c:
                c.activate()

    def hasComponent(self, componentType):
        return self.components[componentType] is not None

    def getComponent(self, componentType):
        # TODO: a lot of our expressions are of type entity.getComponent(...).doSomething()
        # which will obviously fail if we return None here, causing a lot of extraneous
        # checks on outside code. We might want to handle this in a different way (e.g.
        # a "null" component that has method signatures for everything, but does nothing).
        return self.components[componentType]

    def getComponents(self):
        return [c for c in self.components if c is not None]

    def getAttributes(self):
        combatAttr = self.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
        return combatAttr if combatAttr else self.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    def attachEventCallback(self, eventType, callback):
        self.eventCallbacks[eventType].append(callback)

    def detachEventCallback(self, eventType, callback):
        self.eventCallbacks[eventType].remove(callback)

    def localEvent(self, eventType, data=None):
        for cb in self.eventCallbacks[eventType]:
            cb(eventType, data)

    def destroy(self):
        self.deactivateAllComponents()
        self.destroyed += 1

    def isDestroyed(self):
        return self.destroyed > 0

    def isReleased(self):
        return self.destroyed > 2

    def initializeComponents(self):
        for c in self.components:
            if c is not None:
                c.initialize(None)