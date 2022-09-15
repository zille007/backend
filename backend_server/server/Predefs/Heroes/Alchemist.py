import Enums
import random
from euclid import Vector3
from utils import angleToUnitVector3

def alchemistChargeHandler( entity, world, (charge_dir, charge_power, mix_list) ):
    attr = entity.getAttributes()
    cost = 999
    mana = 0

    if type(mix_list) is list and len(mix_list) == 3:
        mana = attr.get("Mana")
        cost = attr.get(( "Abilities", "Charge", "Cost" ) )   #baseline
        for i in range( 0, 3 ):
            bi = mix_list[i]
            ab = "Bottle %d" % (i+1,)
            cost += attr.get( ("Abilities", ab, "Cost") )

    if attr.get("Status") is not "Dead" and cost <= mana:
        if type(mix_list) is list and len(mix_list) == 3:
            attr.inc("Mana", -cost)
            attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            user = world.getUserForUnit(entity)
            maxdist = 10.0
            pos = entity.getPosition() + (charge_dir * (maxdist * charge_power))

            colordict = {
                "Health potion": ( 1.0, 0.0, 0.0),
                "Mana potion": ( 0.0, 0.0, 1.0 ),
                "Speed": ( 1.0, 0.8, 0.0 ),
                "Teleport": ( 1.0, 0.2, 1.0 ),
                "Knockback": ( 1.0, 0.5, 1.0 ),
                "Mine": ( 1.0, 1.0, 0.0 ),
                "Gold": ( 0.0, 0.2, 0.8 )
            }

            mix_results = (
                ( (1,1,1), "Health potion" ),
                ( (2,2,2), "Mana potion" ),
                ( (3,3,3), "Armor"  ),

                ( (1,1,2), "Health potion" ),
                ( (1,2,1), "Health potion" ),
                ( (2,1,1), "Health potion" ),

                ( (1,1,3), "Mana potion" ),
                ( (1,3,1), "Mana potion" ),
                ( (3,1,1), "Mana potion" ),

                ( (2,2,3), "Speed" ),
                ( (2,3,2), "Speed" ),
                ( (3,2,2), "Speed" ),

                ( (2,2,1), "Teleport" ),
                ( (2,1,2), "Teleport" ),
                ( (1,2,2), "Teleport" ),

                ( (3,3,1), "Knockback" ),
                ( (3,1,3), "Knockback" ),
                ( (1,3,3), "Knockback" ),

                ( (3,3,2), "Mine" ),
                ( (3,2,3), "Mine" ),
                ( (2,3,3), "Mine" ),

                ( (1,2,3), "Gold" ),
                ( (1,3,2), "Gold" ),
                ( (2,1,3), "Gold" ),
                ( (2,3,1), "Gold" ),
                ( (3,1,2), "Gold" ),
                ( (3,2,1), "Gold" ),
            )

            effect = "None"
            usecolor = (1.0, 1.0, 1.0)
            for r in mix_results:
                match = True
                for i in range(0,3):
                    if r[0][i] != mix_list[i]:
                        match = False
                        break
                if match:
                    effect = r[1]
                    usecolor = colordict[effect]

            color = { "R": random.random(), "G": random.random(), "B": random.random() }
            bottle = world.createGameEntityForUser(
                "Alchemist bottle",
                entity.getPosition(),
                (entity.getPosition() - pos).normalized(),
                user,
                (
                    ("Team", attr.get("Team")),
                    ("Destination", pos),
                    ("Originator", entity.id),
                    ("Effect", effect ),
                    ("Color", ( ("R", usecolor[0] ),
                                ("G", usecolor[1] ),
                                ("B", usecolor[2] ), ) ),
                )
            )

            b_mover = bottle.getComponent( Enums.COMP_TYPE_MOVER )
            b_mover.setDestination( pos )

            world.networkCommand( Enums.WORLD_EVENT_ABILITY_USED, ("Charge", 0.0, -1, Vector3( 0, 0, 0 )), entity )


def alchemistBottleAtDestination( entity, world, args ):
    attr = entity.getAttributes()
    eventIO = entity.getComponent( Enums.COMP_TYPE_EVENTIO )

    effect = attr.get( "Effect" )

    if effect == "None":
        pass
    elif effect == "Mana potion":
        alchemistEffectSpawnPotion( entity, world, (entity.getPosition(), "Mana") )
    elif effect == "Health potion":
        alchemistEffectSpawnPotion( entity, world, (entity.getPosition(), "Health") )
    elif effect == "Molotov":
        alchemistEffectMolotov( entity, world, (entity.getPosition(),) )
    elif effect == "Knockback":
        alchemistEffectKnockback( entity, world, (entity.getPosition(), ) )
    elif effect == "Teleport":
        alchemistEffectSpawnPotion( entity, world, (entity.getPosition(), "Alchemist teleport") )
    elif effect == "Armor":
        alchemistEffectSpawnPotion( entity, world, (entity.getPosition(), "Alchemist armor") )
    elif effect == "Speed":
        alchemistEffectSpawnPotion( entity, world, (entity.getPosition(), "Alchemist speed") )
    elif effect == "Gold":
        alchemistEffectSpawnPotion( entity, world, (entity.getPosition(), "Alchemist gold") )
    elif effect == "Mine":
        alchemistEffectSpawnPotion( entity, world, (entity.getPosition(), "Alchemist mine") )
    else:
        world.logError( "Unknown alchemist effect %s for %s!" % (effect, entity.getName()))

    eventIO.receiveImmediateEvent("_destroy", world)


def alchemistEffectSpawnPotion( entity, world, (position, potion_type) ):
    position.z = 0.0  # insurance so the pot wont spawn below ground, making it impossible to pick up
    attrs = [ ("Subtype", "Alchemist potion"),
                                  ("Originator", entity.getAttribute( "Originator" ) ),
                                  ("Color", ( ("R", entity.getAttribute( "Color.R" ) ),
                                              ("G", entity.getAttribute( "Color.G" ) ),
                                              ("B", entity.getAttribute( "Color.B" ) ), ) ),
                                ]
    if potion_type == "Gold":
        attrs.append( ("Gold amount", random.randint( 5, 10 )) )
    e = world.createGameEntity( "%s potion" % (potion_type,), position.copy(), Vector3(1, 0, 0),
                                tuple( attrs ) )


def alchemistEffectMolotov( entity, world, (position,) ):
    attr = entity.getAttributes()
    user = world.getUserForUnit(entity)
    dmgMin = 10
    dmgMax = 20
    dmgType = "Magical"
    pierceAmount = 0.25
    bottle = world.createGameEntityForUser(
        "Fyre area",
        position,
        Vector3(1, 0, 0),
        user,
        (
            ("Team", attr.get("Team")),
            ("Originator", attr.get( "Originator") ),
            ("Radius", 3.0),
            ("Team", attr.get("Team")),
            ("Damage minimum", dmgMin),
            ("Damage maximum", dmgMax),
            ("Damage type", dmgType),
            ("Pierce amount", pierceAmount),

        )
    )

def alchemistEffectKnockback( entity, world, (position, ) ):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    eventIO = entity.getComponent( Enums.COMP_TYPE_EVENTIO )
    teamID = attr.get("Team")

    radius = 4.0

    targets = world.queryEnemyUnitsByCircle(
        teamID,
        entity.getPosition(),
        radius,
        lambda e: e.getAttribute("Status") != "Dead" and
                  e.hasTag("Targetable")
    )
    for t in targets:
        target = t
        eventIO.sendEvent(target, "Knockback", (7, -((t.getPosition() - entity.getPosition()).normalized()), .2, 0.5))
        # FX?


def alchemistEffectGenerateGold( entity, world, (position, ) ):
    pass


def alchemistItemPickupHandler( entity, world, heroID ):
    hero = world.getEntityByID( heroID )
    if hero and not hero.isDestroyed() and hero.getAttribute("Status") != "Dead":
        attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        attr.set("Status", "Picked up")
        effectType = attr.get("Effect type")

        if effectType == "Teleport":
            # pick a random POI and teleport the pickupee there
            pois = world.getVictoryPoints() + world.getBases() + world.getGoldMines()
            selected = random.choice( pois )
            world.logInfo( "%s will teleport to %s at %s" % (hero.getName(), selected.getName(), selected.getPosition()))
            timer = hero.getComponent( Enums.COMP_TYPE_TIMER )
            eventIO = hero.getComponent( Enums.COMP_TYPE_EVENTIO )

            heroattr = hero.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
            heroattr.set( "Status", "Teleporting" )
            localpos = angleToUnitVector3( random.randint( 0, 360 ), None ) * ((random.random() * 2.0) + 1.5 )
            final_pos = selected.getPosition() + localpos

            fsm = hero.getComponent(Enums.COMP_TYPE_FSM)
            if fsm:
                fsm.setState("Stunned")
            timer = hero.getComponent(Enums.COMP_TYPE_TIMER)
            timer.addTimer("Stun timer", "Stun end", 1, 0.6)
            waypointMover = hero.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
            mover = hero.getComponent(Enums.COMP_TYPE_MOVER)
            if waypointMover:
                waypointMover.pause()
                if mover.isMoving():
                    mover.stop()
            elif mover:
                mover.stop()

            world.networkCommand(Enums.WORLD_EVENT_TELEPORT, list( final_pos ), hero)
            timer.addTimer("Teleport timer", "Teleport", Enums.TIMER_ONCE, 0.5, final_pos )
            # FX?
        elif effectType == "Mine":
            e = world.createGameEntity( "Explosion area", entity.getPosition(), Vector3(1, 0, 0),
                                        ( ( "Originator", attr.get( "Originator") ),
                                          ( "Damage minimum", 40 ),
                                          ( "Damage maximum", 60 )
                                        ) )
            pass
        elif effectType == "Gold":
            amount = entity.getAttribute( "Gold amount" )
            heroattr = hero.getComponent( Enums.COMP_TYPE_ATTRIBUTES )
            team = world.getTeamEntity( heroattr.get( "Team" ) )
            team.getAttributes().inc(("Resources", "Gold"), amount )
            # TODO maybe send world event


        world.networkCommand(Enums.WORLD_EVENT_ITEM_PICKUP, entity.getAttribute( "Subtype" ), hero)
        world.destroyEntity(entity)


def mineExplosionDamage( entity, world, args ):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    world.logInfo( "Mine explosion area dealing damage" )
    victims = world.queryEntitiesByCircle( entity.getPosition(), attr.get( "Damage radius" ), None )
    originatorUnit = world.getEntityByID( attr.get( "Originator" ) )
    user = world.getUserForUnit( originatorUnit )
    for v in victims:
        # no damage to units in the originator team
        if v.getAttribute( "Team" ) == originatorUnit.getAttribute( "Team" ) and v is not originatorUnit:
            continue

        dmgMin = attr.get( "Damage minimum" )
        dmgMax = attr.get( "Damage maximum" )
        dmgType = attr.get( "Damage type" )
        pierceAmount = attr.get( "Pierce amount" )

        eio = entity.getComponent( Enums.COMP_TYPE_EVENTIO )
        eio.receiveImmediateEvent("Damage inflict", world, (dmgMin, dmgMax, dmgType, pierceAmount, v.id))

        flames = attr.get( "Extra flames" )
        if flames is not None and flames > 0:
            flame_dmgmin = attr.get( "Extra flame damage minimum" )
            flame_dmgmax = attr.get( "Extra flame damage maximum" )
            flame_radius = attr.get( "Extra flame radius" )

            for i in range( 0, flames ):
                localpos = angleToUnitVector3( random.randint( 0, 360 ), None ) * (random.random() * attr.get( "Radius" ) )
                flame_pos = entity.getPosition() + localpos
                flame = world.createGameEntityForUser(
                    "Fyre area",
                    flame_pos,
                    Vector3(1, 0, 0),
                    user,
                    (
                        ("Team", attr.get("Team")),
                        ("Originator", attr.get( "Originator") ),
                        ("Radius", flame_radius),
                        ("Team", attr.get("Team")),
                        ("Damage minimum", flame_dmgmin),
                        ("Damage maximum", flame_dmgmax),
                        ("Damage type", "Magical"),
                        ("Pierce amount", 0.25),
                    )
                )

