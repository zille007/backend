import Enums
import random
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector
from Intersection import circleToCircle


def townhallProcess(entity, world, args):
    """
    townhallProcess
    """
    attr = entity.getAttributes()
    teamID = attr.get("Team")

    unitFilter = (lambda e: circleToCircle(e.getPosition(), e.getSize(), entity.getPosition(), .75))
    units = filter(unitFilter, world.getEnemyHeroesForTeam(teamID) + world.getEnemyCreepsForTeam(teamID))

    for u in units:
        u.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Reach base", entity)
    workers = attr.get("Workers")
    if len(workers) < attr.get( "Worker count" ):
        user = world.getUserForUnit(entity)
        workerprefab = attr.get( "Worker prefab" )
        if workerprefab is None:
            world.logError( "HQ %s tried to create a worker but has no worker prefab set!" % (entity.getName(), ))
            return
        if user:
            worker = world.createGameEntityForUser(
                workerprefab,
                entity.getPosition(),
                Vector3(1, 0, 0),
                user,
                (
                    ("Team", attr.get("Team")),
                )
            )
            workers.append(worker)
        else:
            worker = world.createGameEntity(
                workerprefab,
                entity.getPosition(),
                Vector3(1, 0, 0),
                (
                    ("Team", attr.get("Team")),
                )
            )
            workers.append(worker)


def healHeroes(entity, world, args):
    attr = entity.getAttributes()
    pos = entity.getPosition()

    # requested; see DTEA-53
    #if attr.get("Status") == "Upgrading":
    #    return

    teamID = attr.get("Team")

    unitFilter = (lambda e: circleToCircle(e.getPosition(), e.getSize(), entity.getPosition(), attr.get("Heal range")) and
                            not e.isDestroyed() and
                            e.getAttribute("Status") == "Idle")
    heroes = filter(unitFilter, world.getHeroesForTeam(teamID))

    if len(heroes) > 0:
        effect = entity.getComponent(Enums.COMP_TYPE_EFFECT)
        effect.launchEffect("Heal heroes", world, heroes)

        for h in heroes:
            h.receiveEvent("Mana", 5)
        world.networkCommand(Enums.WORLD_EVENT_AOE_HEAL_PERFORMED, [e.id for e in heroes], entity)

    enemyHeroes = world.getEnemyHeroesForTeam(teamID)
    dmgMin = attr.get("Damage minimum")
    dmgMax = attr.get("Damage maximum")
    dmg = int(dmgMin + random.random()*(dmgMax - dmgMin))
    dmgRadius = attr.get("Damage radius")
    dmg_enemies = []
    for h in enemyHeroes:
        if (h.getPosition() - pos).magnitude_squared() <= dmgRadius**2:
            h.receiveEvent("Damage", (dmg, 1.0, entity.id, None))
            dmg_enemies.append( h.id )
    if len(dmg_enemies) > 0:
        world.networkCommand(Enums.WORLD_EVENT_AOE_DAMAGE_PERFORMED, dmg_enemies, entity)



def upgradeTownhall(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    user = world.getUserForUnit(entity)
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    attr.inc(("Stats", "Level"), 1)
    attr.inc("Hitpoints", 100)
    attr.inc("Hitpoints maximum", 100)
    attr.inc(("Stats", "Armor"), 10)

    if attr.get( "Status" ) == "Upgrading":
        attr.set( "Status", "Idle" )

    level = attr.get("Stats.Level")
    buildings = world.getBuildingsForTeam(entity.getAttribute("Team"))
    increases = world.getGemIncreasesForUser(user, level, level)
    for b in buildings:
        world.addIncreasesToBuilding(b, increases)

    world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADED, None, entity)
