from euclid import Vector3
import Enums

from Predefs.General import *
from Predefs.AbilityEffects import *
from Predefs.Procs import *
from Predefs.Processes import *
from Predefs.Units import *

from Predefs.Worker import *

from Predefs.Heroes.Bear import *
from Predefs.Heroes.Sniper import *
from Predefs.Heroes.Fyrestein import *
from Predefs.Heroes.Rogue import *
from Predefs.Heroes.StoneElemental import *
from Predefs.Heroes.Beaver import *
from Predefs.Heroes.Alchemist import *

from Predefs.Creeps.Summon import *
from Predefs.Creeps.Sapper import *
from Predefs.Creeps.Balloonist import *
from Predefs.Creeps.Shaman import *
from Predefs.Creeps.Thief import *
from Predefs.Creeps.Spectre import *
from Predefs.Creeps.Ghost import *
from Predefs.Creeps.Gnome import *
from Predefs.Creeps.Wolf import *
from Predefs.Creeps.Decoy import *
from Predefs.Creeps.Cloud import *

from Predefs.Buildings.Barracks import *
from Predefs.Buildings.HQ import *
from Predefs.Buildings.Artillery import *
from Predefs.Buildings.DefensiveTower import *
from Predefs.Buildings.GoldMine import *

from Predefs.AI.easy import *
from Predefs.AI.medium import *
from Predefs.AI.hard import *
from Predefs.AI.general import *
from Predefs.AI.tutorial import *

from Predefs.Predicates import *

from Predefs.TestFunctions import *

## TODO: these are leftovers and/or unused funcs, left here for posterity.
## If there is actual use for them, please move them to their appropriate
## files.


def AoEdamageUpgradeHandler(entity, world, args):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    attr.inc(("Abilities", "AoE damage", "Cooldown"), -1)
    attr.inc(("Abilities", "AoE damage", "Damage"), 30)
    attr.inc(("Abilities", "AoE damage", "Range"), .25)
    attr.inc(("Abilities", "AoE damage", "Damage radius"), .1)
    attr.inc(("Abilities", "AoE damage", "Level"), 1)


def AoEdamageHandler(entity, world, pos):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    damage = attr.get(("Abilities", "AoE damage", "Damage"))
    targets = world.queryEntitiesByCircle(pos, attr.get(("Abilities", "AoE damage", "Damage radius")), lambda e: e.getAttribute("Team") is not entity.getAttribute("Team"))
    for t in targets:
        if t.hasComponent( Enums.COMP_TYPE_EVENTIO ):
            t.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Damage", (damage, "Magical", 0.0, entity.id))
    world.createGameEntity("Area particle", pos, Vector3(1, 0, 0), (
        ("Effect name", "AoE damage"),
        ("Radius", attr.get(("Abilities", "AoE damage", "Damage radius"))),
    ))



def granadierCharge(entity, world, (dir, power)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get("Status") is not "Dead" and attr.get(("Abilities", "Charge", "Ready")):
        
        attr.set(("Abilities", "Charge", "Ready"), False)
    
        projectile = world.createGameEntityForUser(
            "SteamGrenade",
            entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
            Vector3(1, 0, 0),
            attr.get( "OwnerId" ),
            (
                ("Home", entity.id),
                ("Team", entity.getAttribute("Team")),
                ("Level", entity.getAttribute(("Stats", "Level"))),
            )
        )
        if projectile is None:
            return
        cooldown = attr.get(("Abilities", "Charge", "Cooldown"))
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, cooldown)
        projectile.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(dir * power)
        world.networkCommand(Enums.WORLD_EVENT_CHARGE, None, projectile)


def healingTotemCharge(entity, world, (dir, power)):
    attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attr.get("Status") is not "Dead" and attr.get(("Abilities", "Charge", "Ready")):
        
        attr.set(("Abilities", "Charge", "Ready"), False)
    
        projectile = world.createGameEntityForUser(

            "HealingTotem",

            entity.getComponent(Enums.COMP_TYPE_TRANSFORM).getWorldPosition(),
            Vector3(1, 0, 0),
            attr.get( "OwnerId" ),
            (
                ("Home", entity.id),
                ("Team", entity.getAttribute("Team")),
                ("Level", entity.getAttribute(("Stats", "Level"))),
            )
        )

        if projectile is None:
            return
        
        entity.getComponent(Enums.COMP_TYPE_TIMER).addTimer("Charge cooldown", "Charge ready", Enums.TIMER_ONCE, ("Abilities", "Charge", "Cooldown"))
        projectile.getComponent(Enums.COMP_TYPE_MOVER).setDirectionAndMove(dir)
        world.networkCommand(Enums.WORLD_EVENT_CHARGE, None, entity)