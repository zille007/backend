import Enums
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector


def defenderDeath(entity, world, args):
    attr = entity.getAttributes()
    timer = entity.getComponent(Enums.COMP_TYPE_TIMER)

    defenders = attr.get("Defenders")
    for i in range(len(defenders)).__reversed__():
        if defenders[i].isDestroyed() or defenders[i].getAttribute("Status") == "Dead":
            del defenders[i]

    if not timer.hasTimer("Spawn timer"):
        timer.addTimer("Spawn timer", "Spawn", Enums.TIMER_ONCE, "Reinforcement period")


def spawnDefender(entity, world, args):
    attr = entity.getAttributes()
    # no spawning if incorrect status
    status = attr.get("Status")
    if status == "Building" or status == "Upgrading" or status == "Freeze" or status == "Unbuilt":
        return

    if (attr.get("Rally point") - entity.getPosition()).magnitude_squared() > attr.get("Rally range")**2:
        attr.set("Rally point", entity.getPosition())
    defenders = attr.get("Defenders")
    for i in xrange(len(defenders)).__reversed__():
        if defenders[i].isDestroyed() or defenders[i].getAttribute("Status") == "Dead":
            del defenders[i]

    cap = attr.get("Defenders maximum")
    if len(defenders) < cap:
        prefab = attr.get("Defender type")

        if world.prefabExists(prefab):
            allincs = []
            for h in world.getHeroesForTeam( attr.get( "Team" ) ):
                u = world.getUserForUnit( h )
                #world.logInfo( "Hero unit %s on team %d owned by user %s" % (h.getName(), attr.get("Team"), u.username ) )
                if u is not None:
                    incs = world.getItemIncreasesForUser( u, h.getComponent( Enums.COMP_TYPE_ATTRIBUTES ).get( "Stats.Level" ) )
                    if incs is not None:
                        allincs.append( incs  )

            if attr.get("OwnerId") is not None:
                level = attr.get(("Stats", "Level"))
                user = world.getUserForUnit(entity)

                defender = world.createGameEntityForUser(
                    prefab,
                    entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
                    Vector3(1, 0, 0),
                    attr.get("OwnerId"),
                    (
                        ("Damage minimum", attr.get("Defender attributes.Damage minimum")),
                        ("Damage maximum", attr.get("Defender attributes.Damage maximum")),
                        ("Hitpoints", attr.get("Defender attributes.Hitpoints")),
                        ("Hitpoints maximum", attr.get("Defender attributes.Hitpoints maximum")),
                        ("Attack period", attr.get("Defender attributes.Attack period")),
                        ("Home", entity.id),
                        ("Team", entity.getAttribute("Team")),
                        ("Rally point", attr.get("Rally point").copy()),
                    )
                )
            else:
                defender = world.createGameEntity(
                    prefab,
                    entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
                    Vector3(1, 0, 0),
                    (
                        ("Damage minimum", attr.get("Defender attributes.Damage minimum")),
                        ("Damage maximum", attr.get("Defender attributes.Damage maximum")),
                        ("Hitpoints", attr.get("Defender attributes.Hitpoints")),
                        ("Hitpoints maximum", attr.get("Defender attributes.Hitpoints maximum")),
                        ("Attack period", attr.get("Defender attributes.Attack period")),
                        ("Home", entity.id),
                        ("Team", entity.getAttribute("Team")),
                        ("Rally point", attr.get("Rally point").copy()),
                    )
                )
            if defender is None:
                return

            if defender is not None:
                for i in allincs:
                    world.addIncreasesToCreep( defender, i )


            defenders.append(defender)
            # rerally units to the building rally point
            rally = attr.get("Rally point")
            eventio = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
            eventio.receiveEvent("Rally", rally)

            if len(defenders) < cap:
                timer = entity.getComponent(Enums.COMP_TYPE_TIMER)
                timer.addTimer("Spawn timer", "Spawn", Enums.TIMER_ONCE, "Reinforcement period")


def healDefenders(entity, world, args):
    attr = entity.getAttributes()
    if attr.get("Status") != "Idle":
        return
    defenders = attr.get("Defenders")
    for d in defenders:
        if d is None or d.isDestroyed() or d.getAttribute("Status") != "Idle" or d.getAttribute("Hitpoints") >= d.getAttribute("Hitpoints maximum"):
            continue
        d.receiveEvent("Heal", (attr.get("Heal amount"), entity.id))


def rallyHandler(entity, world, rally):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get("Status") == "Dead" or attr.get("Status") == "Sold" or attr.get("Status") == "Upgrading":
        return
    if (entity.getPosition() - rally).magnitude_squared() <= attr.get("Rally range")**2:
        attr.set("Rally point", rally.copy())
    else:
        rally = entity.getPosition() + (rally - entity.getPosition()).normalized()*attr.get("Rally range")*.99
        attr.set("Rally point", rally.copy())
    defenders = attr.get("Defenders")
    # a single defender will rally to the rally point
    if len(defenders) == 1 and defenders[0] is not None: #sanity
        d = defenders[0]
        if not d.isDestroyed():
            d.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Rally point", rally.copy())
    else:
        offset = 0.75
        rp_locals = [ Vector3( offset, 0, 0 ), Vector3( -offset, 0, 0 ), Vector3( 0, offset, 0 ), Vector3( 0, -offset, 0 ),
                      Vector3( offset * 1.25, -offset * 1.25, 0 ), Vector3( -offset * 1.25, -offset * 1.25, 0 ),
                      Vector3( offset * 1.25, offset * 1.25, 0), Vector3( -offset * 1.25, offset * 1.25, 0 ) ]
        i = 0
        for d in defenders:
            if not d.isDestroyed():
                d.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Rally point", rally.copy() + rp_locals[i] )
                i += 1
                # lets just not die alright
                if i >= len( rp_locals ):
                    i = 0


def upgradeGarrison(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    base = world.getBaseForTeamID(attr.get("Team"))
    if base is None:
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    baseLevel = base.getAttribute(("Stats", "Level"))
    maxLevel = min(baseLevel + 1, maxLevel)
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    attr.inc(("Stats", "Level"), 1)
    attr.inc(("Stats", "Armor"), 10)
    attr.inc("Hitpoints", 50)
    attr.inc("Hitpoints maximum", 50)
    if attr.get("Subtype") != "Goblin ancestor" and attr.get("Subtype") != "Pond dragon":
        attr.inc("Defenders maximum", 1)
    attr.inc("Rally range", .25)

    level = attr.get(("Stats", "Level"))
    user = world.getUserForUnit(entity)
    #increases = world.getGemIncreasesForUser(user, level, level)
    #world.addIncreasesToBuilding(entity, increases)

    if attr.get( "Status" ) == "Upgrading":
        attr.set("Status", "Idle")

    entity.receiveEvent("Spawn")
    world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADED, None, entity)


def upgradeWatchTower(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    base = world.getBaseForTeamID(attr.get("Team"))
    if base is None:
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    baseLevel = base.getAttribute(("Stats", "Level"))
    maxLevel = min(baseLevel + 1, maxLevel)
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    attr.inc(("Stats", "Level"), 1)
    attr.inc("Defenders maximum", 1)

    level = attr.get(("Stats", "Level"))
    user = world.getUserForUnit(entity)
    #increases = world.getGemIncreasesForUser(user, level, level)
    #world.addIncreasesToBuilding(entity, increases)

    if attr.get("Status" ) == "Upgrading":
        attr.set("Status", "Idle")

    eventIO.receiveEvent("Spawn")
    world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADED, None, entity)


def upgradeDefensiveTower(entity, world, args):
    attr = entity.getAttributes()
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    base = world.getBaseForTeamID(attr.get("Team"))
    if base is None:
        return
    team = world.getTeamEntity(attr.get("Team"))
    teamAttr = team.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    maxLevel = teamAttr.get(("Units", attr.get("Faction"), attr.get("Subtype"), "Level maximum"))
    baseLevel = base.getAttribute(("Stats", "Level"))
    maxLevel = min(baseLevel + 1, maxLevel)
    if attr.get(("Stats", "Level")) >= maxLevel:
        return

    defAttr = attr.get("Defender attributes")
    oldDmgMin = None
    oldDmgMax = None
    oldHitpoints = None
    oldHitpointsMax = None
    oldAttackPeriod = None
    if defAttr:
        oldDmgMin = attr.get("Defender attributes.Damage minimum")
        oldDmgMax = attr.get("Defender attributes.Damage maximum")
        oldHitpoints = attr.get("Defender attributes.Hitpoints")
        oldHitpointsMax = attr.get("Defender attributes.Hitpoints maximum")
        oldAttackPeriod = attr.get("Defender attributes.Attack period")

    attr.inc(("Stats", "Level"), 1)
    increases = attr.get("Stats.Upgrade increases.Level " + str(attr.get("Stats.Level")))
    attr.applyMultiple(increases)

    if defAttr:
        newDmgMin = attr.get("Defender attributes.Damage minimum")
        newDmgMax = attr.get("Defender attributes.Damage maximum")
        newHitpoints = attr.get("Defender attributes.Hitpoints")
        newHitpointsMax = attr.get("Defender attributes.Hitpoints maximum")
        newAttackPeriod = attr.get("Defender attributes.Attack period")
        for d in attr.get("Defenders"):
            dattr = d.getAttributes()
            if d is not None and not d.isDestroyed() and dattr.get("Status") != "Dead":
                dattr.inc("Damage minimum", newDmgMin - oldDmgMin)
                dattr.inc("Damage maximum", newDmgMax - oldDmgMax)
                dattr.inc("Hitpoints", newHitpoints - oldHitpoints)
                dattr.inc("Hitpoints maximum", newHitpointsMax - oldHitpointsMax)
                dattr.inc("Attack period", newAttackPeriod - oldAttackPeriod)

    if attr.get("Status") == "Upgrading":
        attr.set("Status", "Idle")

    eventIO.receiveEvent("Spawn")
    world.networkCommand(Enums.WORLD_EVENT_BUILDING_UPGRADED, None, entity)