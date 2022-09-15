import Enums
from euclid import Vector3
from utils import findClosestEntity, areOnSameTeam, angleToUnitVector3, addJitterToVector


def sniperCharge(entity, world, (dir, power)):
    attr = entity.getAttributes()
    status = attr.get("Status")
    if status != "Idle" and status != "Moving" and status != "Target" and status != "Combat" and status != "Casting Charge":
        return
    dir = dir.normalized()
    cost = attr.get(("Abilities", "Charge", "Cost"))
    mana = attr.get("Mana")
    if attr.get("Status") is not "Dead" and attr.get(("Abilities", "Charge", "Ready")) and cost <= mana:
        fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
        if status == "Casting Charge":
            attr.set("Status", "Idle")
            fsm.setState("Idle")
            world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Charge", entity)
        mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
        waypointMover = entity.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
        if waypointMover:
            waypointMover.clearWaypoints()
        mover.stop()
        attr.set(("Abilities", "Charge", "Ready"), False)
        attr.inc("Mana", -cost)
        projectile = world.createGameEntityForUser(
            "Sniper bullet",
            entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
            dir.copy(),
            attr.get( "OwnerId" ),
            (
                ("Home", entity.id),
                ("Team", attr.get("Team")),
                ("Damage minimum", attr.get(("Abilities", "Charge", "Damage minimum"))),
                ("Damage maximum", attr.get(("Abilities", "Charge", "Damage maximum"))),
                ("Originator", entity.id)
            )
        )
        if projectile is None:
            return
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        lifetime = attr.get(("Abilities", "Charge", "Time"))
        projectile.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Lifetime timer", "_destroy", Enums.TIMER_ONCE, lifetime)
        projectile.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(dir)

        world.networkAbilityImmediateSuccess( "Charge", entity )
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Charge", 0.0, -1, Vector3( 0, 0, 0 )), entity )


def sniperBulletDamage(entity, world, targets):
    if targets is None:
        return

    attributes = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
    if isinstance(targets, list):
        for t in targets:
            if attributes and eventIO:
                damage = attributes.get("Damage")
                target = t
                eventIO.sendEvent(target, "Damage", (damage, "Ranged", 0.0, entity.id))
                if attributes.get("Penetrate") is False:
                    world.destroyEntity(entity)
        return
    else:
        if attributes and eventIO:
            damage = attributes.get("Damage")
            target = targets
            eventIO.sendEvent(target, "Damage", (damage, "Ranged", 0.0, entity.id))

            if attributes.get("Penetrate") is False:
                world.destroyEntity(entity)


def sniperBulletIdleUpdate(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)

    physicals = sensor.queryPhysicals(
        "Damage",
        world,
        lambda p: p.entity.hasTag("Targetable") and
                  p.entity.getAttribute("Status") != "Dead" and
                  p.entity.getAttribute("Team") is not attr.get("Team"))
    targets = map(lambda p: p.entity, physicals)
    victims = entity.getAttribute("Victims")
    targets = [t for t in targets if t not in victims]
    if len(targets) is 0:
        return
    for t in targets:
        victims.append(t)
    dmgMin = attr.get("Damage minimum")
    dmgMax = attr.get("Damage maximum")
    dmgType = attr.get("Damage type")
    pierceAmount = attr.get("Pierce amount")
    for t in targets:
        eventIO.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, t.id))
    ## TODO: this probably should be receiveImmediateEvent, but I'm afraid to try it
    eventIO.receiveEvent("_destroy")


def AoEhealHandler(entity, world, pos):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    heal = attr.get(("Abilities", "AoE heal", "Heal"))
    targets = world.queryEntitiesByCircle(pos, attr.get(("Abilities", "AoE heal", "Heal radius")), lambda e: e.getAttribute("Team") is entity.getAttribute("Team") and e.getAttribute("Status") != "Dead")
    for t in targets:
        if t.hasComponent( Enums.COMP_TYPE_EVENTIO):
            if t.hasComponent( Enums.COMP_TYPE_EVENTIO ):
                t.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Heal", (heal, entity.id))
    world.createGameEntity("Area particle", pos, Vector3(1, 0, 0), (
        ("Effect name", "AoE heal"),
        ("Radius", attr.get(("Abilities", "AoE heal", "Heal radius"))),
    ))
    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("AoE heal", 0.0, -1, pos), entity )


def flaskHandler(entity, world, targetID):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    status = attr.get("Status")
    target = world.getEntityByID(targetID)
    if target and target.getAttribute("Status") != "Dead":
        if status == "Casting Flask":
            attr.set("Status", "Idle")
            fsm.setState("Idle")
            world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Flask", entity)
        attr = entity.getAttributes()
        eventIO = entity.getComponent(Enums.COMP_TYPE_EVENTIO)
        amount = attr.get("Abilities.Flask.Heal amount")
        eventIO.receiveEvent("Heal", (amount, entity.id))
        world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Flask", 0.0, targetID, Vector3( 0.0, 0.0, 0.0 ) ), entity )


def smokeAI(entity, world, args):
    sensor = entity.getComponent(Enums.COMP_TYPE_SENSOR)
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)

    # smoke affects both our units and enemy units equally
    physicals = sensor.queryPhysicals( "Area", world,
                                       lambda p: p.entity.hasTag("Targetable") and p.entity.getAttribute("Status") != "Dead" )

    old_affected = attr.get( "Affected units" )
    now_affected = map(lambda p: p.entity, physicals )
    entered = [e for e in now_affected if e not in old_affected]
    exited = [e for e in old_affected if e not in now_affected]

    # world.logInfo( "%s update: phys = %s affected = %s  entered = %s exited = %s" % (entity.getName(), str(physicals), str(now_affected), str(entered), str(exited) ))

    attr.set( "Affected units", tuple(now_affected) )

    for e in entered:
        t = e.getComponent( Enums.COMP_TYPE_TAGS )
        t.add( "In smoke" )

    for e in exited:
        t = e.getComponent( Enums.COMP_TYPE_TAGS )
        t.remove( "In smoke" )


def smokeDespawnHandler(entity, world, pos):
    affected = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get("Affected units")
    for e in affected:
        # we can safely do this; if two smoke clouds overlap, the other smoke will reapply the tag
        # And this will happen regardless of where the smoke is, even if the Smoke is On The Water.
        e.getComponent(Enums.COMP_TYPE_TAGS).remove("In smoke")
    world.destroyEntity(entity)


def smokeAbilityHandler(entity, world, pos):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    status = attr.get("Status")
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    if status == "Casting Smoke":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Smoke", entity)
    duration = entity.getAttribute("Abilities.Smoke.Duration")
    radius = entity.getAttribute("Abilities.Smoke.Radius")
    smoke = world.createGameEntity("Smoke cloud", pos, Vector3(1, 0, 0), (("Team", 1),))
    smoke.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Radius", radius)
    smoke.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Smoke timer", "Smoke despawn", Enums.TIMER_ONCE, duration)
    world.networkCommand(Enums.WORLD_EVENT_ABILITY_USED, ("Smoke", 0.0, -1, pos), entity)


def scopeExpireHandler(entity, world, args):
    attr = entity.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
    combatAttr = entity.getComponent( Enums.COMP_TYPE_COMBATATTRIBUTES )
    scope_tokens = attr.get( ("Abilities", "Scope", "Tokens") )
    map( lambda i: combatAttr.removeModifier( i ), scope_tokens )


def scopeAbilityHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    fsm = entity.getComponent(Enums.COMP_TYPE_FSM)
    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)

    status = attr.get("Status")

    if status == "Casting Scope":
        attr.set("Status", "Idle")
        fsm.setState("Idle")
        world.networkCommand(Enums.WORLD_EVENT_CAST_SUCCESS, "Scope", entity)

    scope_tokens = []

    duration = attr.get( ("Abilities", "Scope", "Duration" ) )
    sight_inc = attr.get( ("Abilities", "Scope", "Sight increase" ) )
    range_inc = attr.get( ("Abilities", "Scope", "Range increase" ) )
    charge_cost_inc = attr.get( ("Abilities", "Scope", "Charge cost increase") )
    attack_period_inc = attr.get( ("Abilities", "Scope", "Attack period increase") )

    scope_tokens.append( combatAttr.addModifier( "Sight range", sight_inc, Enums.MOD_TYPE_ADD ) )
    scope_tokens.append( combatAttr.addModifier( "Attack range", range_inc, Enums.MOD_TYPE_ADD ) )
    scope_tokens.append( combatAttr.addModifier( ("Abilities", "Charge", "Cost"), charge_cost_inc, Enums.MOD_TYPE_ADD ) )
    scope_tokens.append( combatAttr.addModifier( "Attack period", attack_period_inc, Enums.MOD_TYPE_ADD ) )

    attr.set( ( "Abilities", "Scope", "Tokens"), tuple(scope_tokens) )
    entity.getComponent( Enums.COMP_TYPE_TIMER ).addTimer( "Scope timer", "Scope expire", Enums.TIMER_ONCE, duration )

    world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Scope", 0.0, entity.id, Vector3( 0, 0, 0 )), entity )
    #world.networkCommand( Enums.WORLD_EVENT_SCOPE, None, entity )


def sniperLevelUpHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Stats", "Level"), 1)
    attr.inc(("Stats", "Skill points"), 1)
    strengthIncrease = attr.get(("Stats", "Strength increase"))
    dexterityIncrease = attr.get(("Stats", "Dexterity increase"))
    intelligenceIncrease = attr.get(("Stats", "Intelligence increase"))
    hitpointIncrease = attr.get(("Stats", "Hitpoint increase"))
    if hitpointIncrease:
        attr.inc("Hitpoints", hitpointIncrease)
        attr.inc("Hitpoints maximum", hitpointIncrease)
    if strengthIncrease:
        attr.inc(("Stats", "Strength"), strengthIncrease)
    if dexterityIncrease:
        attr.inc(("Stats", "Dexterity"), dexterityIncrease)
    if intelligenceIncrease:
        attr.inc(("Stats", "Intelligence"), intelligenceIncrease)
    attr.inc("Attack range", .1)
    attr.inc("Sight range", .1)
    user = world.getUserEntity(attr.get("Username")).getAttribute("User instance")
    heroLevel = attr.get(("Stats", "Level"))
    increases = world.getItemIncreasesForUser(user, heroLevel, heroLevel)
    if increases:
        world.addIncreasesToHero(entity, increases)


def sniperChargeUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Charge", "Level"), 1)
    attr.inc(("Abilities", "Charge", "Damage"), 40)
    attr.inc(("Abilities", "Charge", "Cooldown"), -1)


def smokeUpgradeHandler( entity, world, pos ):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "Smoke", "Level"), 1)
    attr.inc(("Abilities", "Smoke", "Cooldown"), -1)
    attr.inc(("Abilities", "Smoke", "Duration"), 2.0)
    attr.inc(("Abilities", "Smoke", "Radius"), 0.5)


def scopeUpgradeHandler( entity, world, args ):
    attr = entity.getAttributes()
    attr.inc( ("Abilities", "Scope", "Level"), 1 )
    attr.inc( ("Abilities", "Scope", "Cooldown"), -5 )
    attr.inc( ("Abilities", "Scope", "Duration"), 2.5 )
    attr.inc( ("Abilities", "Scope", "Charge cost increase"), -5 )


def AoEhealUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "AoE heal", "Cooldown"), -1)
    attr.inc(("Abilities", "AoE heal", "Heal"), 10)
    attr.inc(("Abilities", "AoE heal", "Range"), .25)
    attr.inc(("Abilities", "AoE heal", "Heal radius"), .2)
    attr.inc(("Abilities", "AoE heal", "Level"), 1)