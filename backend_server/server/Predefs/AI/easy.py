import Enums
from utils import findClosestEntity, randomVector3Rect


def aiEasyIdleUpdate(entity, world, args):
    attr = entity.getAttributes()
    team = attr.get("Team")
    base = world.getBaseForTeamID(team)
    basePos = base.getPosition()
    heroes = world.getHeroesForTeam(team)

    user = world.getMatch().findUserById( attr.get( "OwnerId") )

    if heroes and len(heroes) > 0:
        hero = heroes[0]
        hero = world.getHeroForUser( user )
        heroAttr = hero.getAttributes()
        heroStatus = heroAttr.get("Status")
        heroPos = hero.getPosition()

        if heroStatus == "Dead":
            return

        if heroStatus == "Idle" or heroStatus == "Moving" or heroStatus == "Target" or heroStatus == "Combat":
            attackRange = heroAttr.get("Attack range")
            damageType = heroAttr.get("Damage type")
            enemyHeroes = world.getEnemyHeroesForTeam(team)
            for enemyHero in enemyHeroes:
                if enemyHero.getAttribute("Status") == "Dead":
                    continue
                enemyHeroPos = enemyHero.getPosition()
                heroToEnemy = enemyHeroPos - heroPos
                if damageType == "Magical" and heroToEnemy.magnitude_squared() > (attackRange - 1.0)**2 and heroToEnemy.magnitude_squared() <= heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Target", enemyHero.id)
                    return
                if damageType == "Magical" and heroStatus == "Target" and heroToEnemy.magnitude_squared() > heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Move", heroPos - heroToEnemy.normalized()*3.0)
                    return
                if damageType == "Ranged" and heroToEnemy.magnitude_squared() > (attackRange - 1.0)**2 and heroToEnemy.magnitude_squared() <= heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Target", enemyHero.id)
                    return
                if damageType == "Ranged" and heroStatus == "Target" and heroToEnemy.magnitude_squared() > heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Move", heroPos - heroToEnemy.normalized()*3.0)
                    return
                if damageType == "Melee" and enemyHero.getAttribute("Damage type") == "Ranged" and heroToEnemy.magnitude_squared() <= 6.0**2 and not world.queryMapObstacle(heroPos, enemyHeroPos):
                    hero.receiveEvent("Target", enemyHero.id)
                    return
                if damageType == "Melee" and enemyHero.getAttribute("Damage type") == "Magical" and heroToEnemy.magnitude_squared() <= 6.0**2 and not world.queryMapObstacle(heroPos, enemyHeroPos):
                    hero.receiveEvent("Target", enemyHero.id)
                    return
                if damageType == "Melee" and enemyHero.getAttribute("Damage type") == "Melee" and heroToEnemy.magnitude_squared() <= 3.5**2 and not world.queryMapObstacle(heroPos, enemyHeroPos):
                    hero.receiveEvent("Target", enemyHero.id)
                    return
                if damageType == "Melee":
                    enemyCreeps = world.getEnemyCreepsForTeam(team)
                    if len(enemyCreeps) > 0:
                        enemyCreep = findClosestEntity(heroPos, enemyCreeps)
                        enemyCreepPos = enemyCreep.getPosition()
                        heroToEnemy = enemyCreepPos - heroPos
                        if heroToEnemy.magnitude_squared() <= 4.5**2 and not world.queryMapObstacle(heroPos, enemyCreepPos):
                            hero.receiveEvent("Target", enemyCreep.id)
                            return
                continue

        if heroStatus == "Idle" or heroStatus == "Target":
            goldmines = [b for b in world.getEnemyBuildingsForTeam(team) if b.getAttribute("Subtype") == "Goldmine" and b.getPosition().y >= world.height/1.5]
            target = None
            if len(goldmines) > 0:
                target = findClosestEntity(heroPos, goldmines)
                targetPos = target.getPosition()
                while world.queryMapObstacle(heroPos, targetPos):
                    goldmines.remove(target)
                    if len(goldmines) is 0:
                        target = None
                        targetPos = None
                        break
                    else:
                        target = findClosestEntity(heroPos, goldmines)
                        targetPos = target.getPosition()
            if target is None:
                victoryPoints = [vp for vp in world.getVictoryPoints() if vp.getPosition().y >= world.height/1.5]
                if len(victoryPoints) > 0:
                    target = findClosestEntity(heroPos, victoryPoints)
                    targetPos = target.getPosition()
                    while target.getAttribute("Team") == team or world.queryMapObstacle(heroPos, targetPos):
                        victoryPoints.remove(target)
                        if len(victoryPoints) is 0:
                            target = None
                            targetPos = None
                            break
                        else:
                            target = findClosestEntity(heroPos, victoryPoints)
                            targetPos = target.getPosition()
                    if target is None:
                        if world.queryMapObstacle(heroPos, basePos):
                            victoryPoints = [vp for vp in world.getVictoryPoints() if vp.getPosition().y >= world.height/1.5]
                            target = findClosestEntity(basePos, victoryPoints)
                            targetPos = target.getPosition()
                            while world.queryMapObstacle(heroPos, targetPos) or (heroPos - targetPos).magnitude_squared() < 4.0:
                                victoryPoints.remove(target)
                                if len(victoryPoints) is 0:
                                    target = None
                                    targetPos = None
                                    break
                                else:
                                    target = findClosestEntity(heroPos, victoryPoints)
                                    targetPos = target.getPosition()
                        else:
                            if heroAttr.get("Hitpoints") < heroAttr.get("Hitpoints maximum"):
                                target = base
                                targetPos = basePos
                            else:
                                target = None
                                targetPos = None
            if target is None:
                if heroStatus != "Combat":
                    hero.receiveEvent("Move", randomVector3Rect(1, world.height/3.0, world.width - 1, world.height - 1))
            elif (heroPos - targetPos).magnitude_squared() > 4.0:
                hero.receiveEvent("Move", targetPos + (heroPos - targetPos).normalized()*1.5)
                return