import Enums


class ComponentManager(object):
    def __init__(self, typeConstructor, world):
        self.type = typeConstructor
        self.world = world
        self.componentBuffer = [None]*Enums.COMPONENT_MANAGER_INIT_SIZE
        self.tokens = range(len(self.componentBuffer))
        self.capacity = len(self.componentBuffer)
        self.reserved = 0
        for i in range(len(self.componentBuffer)):
            component = self.type()
            component.index = i
            self.componentBuffer[i] = component

    def reserve(self):
        if self.reserved is self.capacity:
            self.tokens.append(self.capacity)
            comp = self.type()
            comp.index = self.capacity
            self.componentBuffer.append(comp)
            self.capacity += 1
        component = self.componentBuffer[self.tokens[self.reserved]]
        self.reserved += 1
        component.statusMask = Enums.COMP_MASK_RESERVED
        return component

    def release(self, component):
        self.reserved -= 1
        component.clear()
        component.statusMask = Enums.COMP_MASK_NULL
        self.tokens[self.reserved] = component.index

    def getBuffer(self):
        return self.componentBuffer

    def getReserved(self):
        return filter(lambda c: c.hasStatus(Enums.COMP_MASK_RESERVED), self.componentBuffer)

    def getAttached(self):
        return filter(lambda c: c.hasStatus(Enums.COMP_MASK_ATTACHED), self.componentBuffer)

    def getActive(self):
        return filter(lambda c: c.hasStatus(Enums.COMP_MASK_ACTIVE), self.componentBuffer)

    def getAwake(self):
        return filter(lambda c: c.hasStatus(Enums.COMP_MASK_AWAKE), self.componentBuffer)

    def filterComponents(self, fltr):
        return filter(fltr, self.componentBuffer)