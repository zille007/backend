import Enums
from euclid import Vector3
from random import random


def decoyIdleUpdate(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    hero = world.getEntityByID(attr.get("Originator"))

    if hero and hero.getAttribute("Status") != "Dead":
        pos = entity.getPosition()
        heroPos = hero.getPosition()
        heroDir = hero.getDirection()
        formationPoint1 = heroPos + Vector3(heroDir.y, -heroDir.x, 0)*2.5 + heroDir*.35
        formationPoint2 = heroPos + Vector3(-heroDir.y, heroDir.x, 0)*2.5 + heroDir*.35
        formationPoint = formationPoint1 if (formationPoint1 - pos).magnitude_squared() < (formationPoint2 - pos).magnitude_squared() else formationPoint2
        if (formationPoint - pos).magnitude_squared() > .1:
            mover.setDestination(formationPoint)
            attr.set("Status", "Moving")
            fsm.setState("Moving")
        else:
            enemies = world.iterateEnemyCreepsAndHeroesForTeam(attr.get("Team"))
            attackRange = attr.get("Attack range")
            for e in enemies:
                epos = e.getPosition()
                esize = e.getSize()
                if (epos - pos).magnitude_squared() <= (esize + attackRange)**2:
                    attr.set("Target", e.id)
                    attr.set("Status", "Combat")
                    fsm.setState("Combat")
                    if attr.get("Attack ready"):
                        eventIO.receiveEvent("Attack first")
                    if not timer.hasTimer("Combat timer"):
                        timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")


def decoyMovingUpdate(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    hero = world.getEntityByID(attr.get("Originator"))

    if not mover.hasDestination():
        attr.set("Status", "Idle")
        fsm.setState("Idle")
    elif hero and hero.getAttribute("Status") != "Dead":
        pos = entity.getPosition()
        heroPos = hero.getPosition()
        heroDir = hero.getDirection()
        attr.set("Status", "Moving")
        fsm.setState("Moving")
        formationPoint1 = heroPos + Vector3(heroDir.y, -heroDir.x, 0)*2.5 + heroDir*.35
        formationPoint2 = heroPos + Vector3(-heroDir.y, heroDir.x, 0)*2.5 + heroDir*.35
        formationPoint = formationPoint1 if (formationPoint1 - pos).magnitude_squared() < (formationPoint2 - pos).magnitude_squared() else formationPoint2
        mover.setDestination(formationPoint)


def decoyCombatUpdate(entity, world, args):
    attr = entity.getAttributes()
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    hero = world.getEntityByID(attr.get("Originator"))
    target = world.getEntityByID(attr.get("Target"))
    pos = entity.getPosition()

    if hero and not hero.isDestroyed() and hero.getAttribute("Status") != "Dead":
        heroPos = hero.getPosition()
        if (heroPos - pos).magnitude_squared() > 25:
            heroDir = hero.getDirection()
            attr.set("Target", Enums.NULL_ID)
            attr.set("Status", "Moving")
            fsm.setState("Moving")
            mover.setDestination(heroPos + Vector3(heroDir.y, -heroDir.x, 0)*2.5 + heroDir*.35)
            return

    attackRange = attr.get("Attack range")
    if target:
        tpos = target.getPosition()
        tsize = target.getSize()
    else:
        tpos = None
        tsize = None
    if not target or target.isDestroyed() or target.getAttribute("Status") == "Dead" or (tpos - pos).magnitude_squared() > (tsize + attackRange)**2:
        enemies = world.iterateEnemyCreepsAndHeroesForTeam(attr.get("Team"))
        attackRange = attr.get("Attack range")
        for e in enemies:
            epos = e.getPosition()
            esize = e.getSize()
            if (epos - pos).magnitude_squared() <= (esize + attackRange)**2:
                attr.set("Target", e.id)
                if attr.get("Attack ready"):
                    eventIO.receiveEvent("Attack first")
                if not timer.hasTimer("Combat timer"):
                    timer.addTimer("Combat timer", "Attack start", Enums.TIMER_INFINITE, "Attack period")
                return
        attr.set("Target", Enums.NULL_ID)
        attr.set("Status", "Idle")
        fsm.setState("Idle")