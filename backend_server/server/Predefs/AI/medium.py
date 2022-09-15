import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, randomVector3Rect


def aiMediumIdleUpdate(entity, world, args):
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
            chargeReady = heroAttr.get("Abilities.Charge.Ready")
            chargeCost = heroAttr.get("Abilities.Charge.Cost")
            mana = heroAttr.get("Mana")
            enemyHeroes = world.getEnemyHeroesForTeam(team)
            for enemyHero in enemyHeroes:
                if enemyHero.getAttribute("Status") == "Dead":
                    continue
                enemyHeroPos = enemyHero.getPosition()
                heroToEnemy = enemyHeroPos - heroPos
                if chargeReady and mana >= chargeCost:
                    if damageType == "Magical" and heroToEnemy.magnitude_squared() <= 4.5**2:
                        hero.receiveEvent("Charge", (heroToEnemy.normalized(), 1.0))
                        return
                    if damageType == "Ranged" and heroToEnemy.magnitude_squared() <= 8**2:
                        hero.receiveEvent("Charge", (heroToEnemy.normalized(), 1.0))
                        return
                    if damageType == "Melee" and heroToEnemy.magnitude_squared() < 4.5**2 and not world.queryMapObstacle(heroPos, enemyHeroPos):
                        hero.receiveEvent("Charge", (heroToEnemy.normalized(), 1.0))
                        return
                if damageType == "Magical" and heroToEnemy.magnitude_squared() > (attackRange - 1.0)**2 and heroToEnemy.magnitude_squared() <= heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Target", enemyHero.id)
                    return
                if damageType == "Magical" and heroStatus == "Target" and heroToEnemy.magnitude_squared() > heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Move", heroPos - heroToEnemy.normalized()*3.0)
                    return
                if damageType == "Magical" and heroToEnemy.magnitude_squared() < (attackRange - 1.5)**2:
                    hero.receiveEvent("Move", heroPos - heroToEnemy.normalized()*3.0)
                    return
                if damageType == "Ranged" and heroToEnemy.magnitude_squared() > (attackRange - 1.0)**2 and heroToEnemy.magnitude_squared() <= heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Target", enemyHero.id)
                    return
                if damageType == "Ranged" and heroStatus == "Target" and heroToEnemy.magnitude_squared() > heroAttr.get("Sight range")**2:
                    hero.receiveEvent("Move", heroPos - heroToEnemy.normalized()*3.0)
                    return
                if damageType == "Ranged" and heroToEnemy.magnitude_squared() < (attackRange - 1.5)**2:
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
            ourindex = 1
            if user in world.getMatch().users:
                ourindex = world.getMatch().users.index( user ) + 1

            if team == 2 and ((ourindex % 2) == 0): # hack: only even numbers do goldmines
                goldmines = [b for b in world.getEnemyBuildingsForTeam(team) if b.getAttribute("Subtype") == "Goldmine" and b.getPosition().y >= world.height/2.0]
            else:
                goldmines = [b for b in world.getEnemyBuildingsForTeam(team) if b.getAttribute("Subtype") == "Goldmine" and b.getPosition().y <= world.height/2.0]
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
                if team == 2:
                    victoryPoints = [vp for vp in world.getVictoryPoints() if vp.getPosition().y >= world.height/2.0]
                else:
                    victoryPoints = [vp for vp in world.getVictoryPoints() if vp.getPosition().y <= world.height/2.0]

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
                            if team == 2:
                                victoryPoints = [vp for vp in world.getVictoryPoints() if vp.getPosition().y >= world.height/2.0]
                            else:
                                victoryPoints = [vp for vp in world.getVictoryPoints() if vp.getPosition().y <= world.height/2.0]

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
                            if heroAttr.get("Hitpoints") < heroAttr.get("Hitpoints maximum") or heroAttr.get("Mana") < heroAttr.get( "Mana maximum" ):
                                target = base
                                targetPos = basePos
                            else:
                                heroes = world.getHeroesForTeam( team )
                                nonai = []
                                for h in heroes:
                                    hero_user = world.getUserForUnit( h )
                                    if hero_user is not None:
                                        if hero_user.isFakedUser:
                                            continue
                                        nonai.append( h )

                                if len(nonai) > 0:
                                    sel = random.choice( nonai )
                                    target = sel
                                    targetPos = sel.getPosition()
                                else:
                                    target = base
                                    targetPos = basePos
            if target is None:
                if heroStatus != "Combat":
                    hero.receiveEvent("Move", randomVector3Rect(1, 1, world.width - 1, world.height - 1))
            elif (heroPos - targetPos).magnitude_squared() > 4.0:
                hero.receiveEvent("Move", targetPos + (heroPos - targetPos).normalized()*1.5)
                return


medium_macro_unit_map = {
    "Northerners": {
        "Garrison":"Garrison",
        "Barracks":"Barracks",
        "Axeman":"Axeman",
        "Hunter":"Hunter",
        "Sapper":"Sapper",
        "Balloonist":"Balloonist",
        "Townhall":"Townhall"
    },
    "Fay": {
        "Garrison":"Goblin ancestor",
        "Barracks":"Battlestump",
        "Axeman":"Satyr",
        "Hunter":"Nymph",
        "Sapper":"Ghost",
        "Balloonist":"Spectre",
        "Townhall":"Fay throne"
    }
}

def aiThinkMacroMediumHandler(entity, world, args):
    attr = entity.getAttributes()
    user = world.getMatch().findUserById( attr.get( "OwnerId") )

    # no macroing if we are not the master on our team
    if user.userType != "Master":
        return

    faction = "Northerners" if user.requestedFaction is 0 else "Fay" if user.requestedFaction is 1 else "Parliament"
    unitmap = medium_macro_unit_map[faction]

    team = attr.get("Team")
    teamEntity = world.getTeamEntity(team)
    teamAttr = teamEntity.getAttributes()
    gold = teamEntity.getAttribute("Resources.Gold")
    base = world.getBaseForTeamID(team)
    basePos = base.getPosition()
    baseLevel = base.getAttribute("Stats.Level")
    buildings = world.getBuildingsForTeam(team)
    garrisons = [b for b in buildings if b.getAttribute("Subtype") == unitmap["Garrison"] ]
    barracks = [b for b in buildings if b.getAttribute("Subtype") == unitmap["Barracks"] ]
    towers = garrisons + barracks
    victoryPoints = world.getVictoryPointsForTeamID(team)
    buildingSlots = world.getBuildingSlotsForTeamID(team)

    goldmineUpgradeCost = teamAttr.get("Units.None.Goldmine.Upgrade cost")
    if gold >= goldmineUpgradeCost:
        goldmines = [b for b in buildings if b.getAttribute("Subtype") == "Goldmine"]
        for gm in goldmines:
            if gm.getAttribute("Stats.Level") <= baseLevel and gm.getAttribute("Status") != "Upgrading":
                gm.receiveEvent("Upgrade start")
                return

    axemanCost = teamAttr.get("Units.%s.%s.Cost" % (faction, unitmap["Axeman"]) )
    hunterCost = teamAttr.get("Units.%s.%s.Cost" % (faction, unitmap["Hunter"]) )
    if len(barracks) > 0:
        for b in barracks:
            bLevel = b.getAttribute("Stats.Level")
            bStatus = b.getAttribute("Status")
            if bStatus == "Building" or bStatus == "Upgrading":
                continue
            if bLevel is 1:
                unitQueue = b.getAttribute("Unit queue")
                if "" in unitQueue and gold >= axemanCost:
                    teamAttr.inc("Resources.Gold", -axemanCost)
                    b.receiveEvent("Enqueue", unitmap["Axeman"] )
                    return
            else:
                unitQueue = b.getAttribute("Unit queue")
                if "" in unitQueue and gold >= hunterCost:
                    teamAttr.inc("Resources.Gold", -hunterCost)
                    b.receiveEvent("Enqueue", unitmap["Hunter"] )
                    return
            barracksUpgradeCost = teamAttr.get("Units.%s.%s.Upgrade cost" % (faction, unitmap["Barracks"]))
            waveTimerCounter = world.getMatchEntity().getAttribute("Wave timer counter")
            if gold >= barracksUpgradeCost and bLevel <= baseLevel and (30 < waveTimerCounter < 50):
                b.receiveEvent("Upgrade start")
                return

    garrisonUpgradeCost = teamAttr.get("Units.%s.%s.Upgrade cost" % (faction, unitmap["Garrison"] ))
    if len(victoryPoints) > 0:
        for gr in garrisons:
            if gr.getAttribute("Status") != "Idle":
                continue
            vp = findClosestEntity(gr.getPosition(), victoryPoints)
            gr.receiveEvent("Rally", vp.getPosition())
            if gold >= garrisonUpgradeCost and gr.getAttribute("Stats.Level") < 2:
                gr.receiveEvent("Upgrade start")

    if len(buildingSlots) > 0:
        garrisonCost = teamAttr.get("Units.%s.%s.Cost" % (faction, unitmap["Garrison"]))
        if gold >= garrisonCost:
            for vp in victoryPoints:
                vpPos = vp.getPosition()
                slot = findClosestEntity(vpPos, buildingSlots)
                slotPos = slot.getPosition()
                if (slotPos - vpPos).magnitude_squared() < 7.5**2:
                    for gr in garrisons:
                        grPos = gr.getPosition()
                        if (grPos - vpPos).magnitude_squared() < 7.5**2:
                            break
                    else:
                        teamAttr.inc("Resources.Gold", -garrisonCost)
                        #world.logInfo( "Medium think macro on unit %s (faction %s) will build Garrison; unitmap=%s" % (entity.getName(), faction, str(unitmap)))
                        entity.receiveEvent("Build", (unitmap["Garrison"], slotPos))
                        return

        barracksCost = teamAttr.get("Units.%s.%s.Cost" % (faction, unitmap["Barracks"]))
        if gold >= barracksCost and len(garrisons) > 0:
            leftFlank = basePos + Vector3(-12.5, -5.0, 0.0)
            leftCovered = False
            rightFlank = basePos + Vector3(12.5, -5.0, 0.0)
            rightCovered = False
            if len(towers) > 0:
                leftTower = findClosestEntity(leftFlank, towers)
                if (leftFlank - leftTower.getPosition()).magnitude_squared() <= 12.5**2:
                    leftCovered = True
                rightTower = findClosestEntity(rightFlank, towers)
                if (rightFlank - rightTower.getPosition()).magnitude_squared() <= 12.5**2:
                    rightCovered = True
            if baseLevel > len(barracks):
                flank = "Left"
                if leftCovered:
                    flank = "Right"
                    if rightCovered:
                        flank = "Left" if random.random() < .5 else "Right"
                teamAttr.inc("Resources.Gold", -barracksCost)
                entity.receiveEvent("Build", (unitmap["Barracks"], flank))
                return

    townhallUpgradeCost = teamAttr.get("Units.%s.%s.Upgrade cost" % (faction, unitmap["Townhall"]))
    if gold >= townhallUpgradeCost and baseLevel < 2:
        base.receiveEvent("Upgrade start")