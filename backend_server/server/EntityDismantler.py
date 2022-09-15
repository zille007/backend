from Component import *
import Enums


class EntityDismantler(object):
    def __init__(self, world):
        self.world = world

    def destroyEntity(self, entity):
        if entity.hasComponent(Enums.COMP_TYPE_NETWORK):
            self.world.networkCommand(Enums.WORLD_EVENT_ENTITY_DESTROY, None, entity)
        if entity.hasComponent(Enums.COMP_TYPE_PHYSICAL):
            self.detachComponent(entity, Enums.COMP_TYPE_PHYSICAL)
        for componentType in range(COMP_TYPE_COUNT):
            self.detachComponent(entity, componentType)

    def detachComponent(self, entity, componentType):
        component = entity.getComponent(componentType)
        if component is None:
            return
        if componentType is Enums.COMP_TYPE_PHYSICAL:
            if Enums.USE_SPATIAL_HASH:
                self.world.spatialHash.removePhysical(component)
        entity.detachComponent(componentType)
        self.world.componentManagers[componentType].release(component)