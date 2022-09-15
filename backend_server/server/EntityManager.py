class EntityManager(object):
    def __init__(self, world):
        self._idPool = 0
        self.world = world
        self.entities = {}

    def addEntity(self, entity):
        self.entities[entity.id] = entity

    def removeEntity(self, entity):
        del self.entities[entity.id]

    def removeEntityByID(self, id):
        try:
            del self.entities[id]
        except KeyError:
            return

    def getEntityByID(self, id):
        try:
            return self.entities[id]
        except KeyError:
            return None

    def getEntities(self):
        return self.entities.itervalues()

    def filterEntities(self, fltr):
        return filter(fltr, self.entities.itervalues())

    def getEntityCount(self):
        return len(self.entities)