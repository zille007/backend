import sys
import logging
import ConfigParser
from Component import *
from Entity import Entity
import Enums
import EntityPrefabs


class EntityAssembler(object):
    def __init__(self, world):
        self._idPool = 0
        self.world = world
        self.log = logging.getLogger( "server" )

    def createEntity(self):
        self._idPool += 1
        entity = Entity(self._idPool)
        self.world.entityManager.addEntity(entity)
        return entity

    def assemblePrefab(self, entity, prefab, pos=None):
        components = self.world.prefabs[prefab]
        for c in components:
            component = self.world.componentManagers[c[0]].reserve()
            entity.attachComponent(component)
        for c in components:
            try:
                component = entity.getComponent(c[0])
                component.initialize(c[1])
            except ComponentError as e:
                self.log.warning( "Could not initialize component type "+str(c[0])+" on entity " + entity.getName()+": " +e.message )
        if pos is not None:
            xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
            if xform:
                xform.setWorldPosition(pos)
        phys = entity.getComponent(Enums.COMP_TYPE_PHYSICAL)
        if phys:
            if Enums.USE_SPATIAL_HASH:
                self.world.spatialHash.addPhysical(phys)

    def attachComponent(self, entity, componentType, initList=None):
        component = self.world.componentManagers[componentType].reserve()
        entity.attachComponent(component)
        component.initialize(initList)
        if componentType is Enums.COMP_TYPE_PHYSICAL:
            if Enums.USE_SPATIAL_HASH:
                self.world.spatialHash.addPhysical(component)


#test stuff
if __name__ == "__main__":
    ea = EntityAssembler(None)
    ea.addPrefabFromFile( "Prefabs/test.prefab" )
