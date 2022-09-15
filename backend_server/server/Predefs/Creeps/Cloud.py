import Enums


def cloudAttackHandler(entity, world, targetID):
    attr = entity.getAttributes()
    status = attr.get("Status")
    if status == "Dead" or entity.isDestroyed():
        return
    target = world.getEntityByID(targetID)
    if target is not None and not target.isDestroyed() and target.hasTag("Targetable") and world.queryLineOfSightForEntity(entity, target.getPosition()):
        team = attr.get("Team")
        damageRadius = attr.get("Damage radius")
        enemies = world.getEnemyUnitsForTeam(team)
        pos = entity.getPosition()
        for e in enemies:
            epos = e.getPosition()
            esize = e.getSize()
            if (epos - pos).magnitude_squared() <= (damageRadius + esize)**2:
                eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
                eventIO.receiveImmediateEvent("Damage inflict", world, (
                    attr.get("Damage minimum"),
                    attr.get("Damage maximum"),
                    attr.get("Damage type"),
                    attr.get("Pierce amount"),
                    e.id)
                )
    else:
        attr.set("Target", Enums.NULL_ID)