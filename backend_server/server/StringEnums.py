import Enums


AttributeEnums = {
    "Tags": Enums.startEnum(),
    "Type": Enums.nextEnum(),
    "Subtype": Enums.nextEnum(),
    "Faction": Enums.nextEnum(),
    "Hero": Enums.nextEnum(),
    "HeroID": Enums.nextEnum(),
    "Team": Enums.nextEnum(),
    "Username": Enums.nextEnum(),
    "Alive": Enums.nextEnum(),
    "Count": Enums.nextEnum(),
    "Customizations": Enums.nextEnum(),
    "Owner name": Enums.nextEnum(),
    "Originator": Enums.nextEnum(),   # for particles, entity ID
    "Items": Enums.nextEnum(),
    "Gems": Enums.nextEnum(),
    "Control type": Enums.nextEnum(),

    "Victory points captured": Enums.nextEnum(),

    "Lifetime": Enums.nextEnum(),
    "Display name": Enums.nextEnum(),

    "Wave interval": Enums.nextEnum(),
    "Wave timer counter": Enums.nextEnum(),
    "Map name": Enums.nextEnum(),

    "Visibility": Enums.nextEnum(),
    "1": Enums.nextEnum(),
    "2": Enums.nextEnum(),
    "3": Enums.nextEnum(),
    "4": Enums.nextEnum(),

    "Stats": Enums.nextEnum(),
    "Strength": Enums.nextEnum(),
    "Dexterity": Enums.nextEnum(),
    "Intelligence": Enums.nextEnum(),

    "Armor": Enums.nextEnum(),
    "Hitpoints maximum": Enums.nextEnum(),
    "Hitpoints": Enums.nextEnum(),
    "Mana": Enums.nextEnum(),
    "Mana maximum": Enums.nextEnum(),
    "Damage total minimum": Enums.nextEnum(),
    "Damage total maximum": Enums.nextEnum(),
    "Damage minimum": Enums.nextEnum(),
    "Damage maximum": Enums.nextEnum(),
    "Damage": Enums.nextEnum(),
    "Attack period": Enums.nextEnum(),
    "Attack time": Enums.nextEnum(),
    "Attack range": Enums.nextEnum(),
    "Attack victims": Enums.nextEnum(),
    "Attack times": Enums.nextEnum(),
    "Haunt time": Enums.nextEnum(),
    "Speed": Enums.nextEnum(),
    "Sight range": Enums.nextEnum(),

    "Target": Enums.nextEnum(),
    "Source": Enums.nextEnum(),
    "Status": Enums.nextEnum(),
    "Respawn time": Enums.nextEnum(),
    "Home": Enums.nextEnum(),

    "Level": Enums.nextEnum(),
    "Level requirement": Enums.nextEnum(),
    "Level maximum": Enums.nextEnum(),
    "Experience": Enums.nextEnum(),
    "Experience total": Enums.nextEnum(),
    "Next level": Enums.nextEnum(),
    "Skill points": Enums.nextEnum(),

    "Collection minimum": Enums.nextEnum(),

    "Resources": Enums.nextEnum(),
    "Tickets": Enums.nextEnum(),
    "Gold": Enums.nextEnum(),
    "Honor": Enums.nextEnum(),

    "Units": Enums.nextEnum(),

    "None": Enums.nextEnum(),

    "Goldmine": Enums.nextEnum(),

    "Northerners": Enums.nextEnum(),

    "Bear": Enums.nextEnum(),
    "Sniper": Enums.nextEnum(),
    "Fyrestein": Enums.nextEnum(),
    "Axeman": Enums.nextEnum(),
    "Hunter": Enums.nextEnum(),
    "Sapper": Enums.nextEnum(),
    "Balloonist": Enums.nextEnum(),
    "Shaman": Enums.nextEnum(),
    "Thief": Enums.nextEnum(),
    "Townhall": Enums.nextEnum(),
    "Fay throne": Enums.nextEnum(),
    "Barracks": Enums.nextEnum(),
    "Garrison": Enums.nextEnum(),
    "Watch tower": Enums.nextEnum(),
    "Artillery": Enums.nextEnum(),

    "Fay": Enums.nextEnum(),

    "Stone elemental": Enums.nextEnum(),
    "Beaver": Enums.nextEnum(),
    "Rogue": Enums.nextEnum(),
    "Satyr": Enums.nextEnum(),
    "Nymph": Enums.nextEnum(),
    "Gnome": Enums.nextEnum(),
    "Ghost": Enums.nextEnum(),
    "Spectre": Enums.nextEnum(),
    "Faun": Enums.nextEnum(),
    "Battlestump": Enums.nextEnum(),
    "Goblin ancestor": Enums.nextEnum(),
    "Pond dragon": Enums.nextEnum(),
    "Thunderwell": Enums.nextEnum(),

    "Parliament": Enums.nextEnum(),

    "Abilities": Enums.nextEnum(),

    "Slot": Enums.nextEnum(),

    "Charge": Enums.nextEnum(),
    "Ready": Enums.nextEnum(),
    "Time": Enums.nextEnum(),
    "Casting time": Enums.nextEnum(),
    "Cooldown": Enums.nextEnum(),
    "Speed increase": Enums.nextEnum(),

    "AoE damage": Enums.nextEnum(),
    "Range": Enums.nextEnum(),
    "Radius": Enums.nextEnum(),
    "Damage radius": Enums.nextEnum(),

    "AoE heal": Enums.nextEnum(),
    "Heal radius": Enums.nextEnum(),
    "Heal time": Enums.nextEnum(),
    "Heal period": Enums.nextEnum(),

    "Smoke": Enums.nextEnum(),
    "Scope": Enums.nextEnum(),
    "Flask": Enums.nextEnum(),

    "Hero heal": Enums.nextEnum(),
    "Heal percentage": Enums.nextEnum(),
    "Duration": Enums.nextEnum(),
    "Tick interval": Enums.nextEnum(),

    "Damage shield": Enums.nextEnum(),
    "Healing ward": Enums.nextEnum(),
    "Amplifier pylon": Enums.nextEnum(),

    "Beaver bolt": Enums.nextEnum(),

    "Summon": Enums.nextEnum(),
    "Summon duck": Enums.nextEnum(),
    "Summon decoy": Enums.nextEnum(),
    "Explode": Enums.nextEnum(),

    "Paralyze": Enums.nextEnum(),
    "Target type": Enums.nextEnum(),

    "Haste": Enums.nextEnum(),

    "Leap": Enums.nextEnum(),

    "Bird carry": Enums.nextEnum(),

    "Bird heal": Enums.nextEnum(),

    "Earthquake": Enums.nextEnum(),

    "Concussion bomb": Enums.nextEnum(),

    "Rocket escape": Enums.nextEnum(),

    "Self destruct": Enums.nextEnum(),

    "Fumes": Enums.nextEnum(),

    "Rage": Enums.nextEnum(),

    "Berserk": Enums.nextEnum(),

    "Bottle 1": Enums.nextEnum(),
    "Bottle 2": Enums.nextEnum(),
    "Bottle 3": Enums.nextEnum(),

    "Alchemist mix": Enums.nextEnum(),
    "Alchemist bottle": Enums.nextEnum(),

    "Damage minimum increase": Enums.nextEnum(),
    "Damage maximum increase": Enums.nextEnum(),

    "Cost": Enums.nextEnum(),
    "Unlock cost": Enums.nextEnum(),
    "Repair cost": Enums.nextEnum(),
    "Upgrade cost": Enums.nextEnum(),
    "Unlocked": Enums.nextEnum(),
    "Building time": Enums.nextEnum(),
    "Upgrade time": Enums.nextEnum(),
    "Offense": Enums.nextEnum(),
    "Defense": Enums.nextEnum(),
    "Description": Enums.nextEnum(),
    "Upgrade descriptions": Enums.nextEnum(),

    "Train period": Enums.nextEnum(),
    "Reinforcement period": Enums.nextEnum(),
    "Defenders maximum": Enums.nextEnum(),
    "Rally point": Enums.nextEnum(),
    "Rally range": Enums.nextEnum(),

    "Unit queue": Enums.nextEnum(),
    "Unit path": Enums.nextEnum(),

    "Gold maximum": Enums.nextEnum(),

    "Capture time": Enums.nextEnum(),
    "Capture counter": Enums.nextEnum(),

    "Heal range": Enums.nextEnum(),
    "Heal minimum": Enums.nextEnum(),
    "Heal maximum": Enums.nextEnum(),
    "Heal": Enums.nextEnum(),

    "Destination": Enums.nextEnum(),

    "Repair per tick": Enums.nextEnum(),
    "Repair interval": Enums.nextEnum(),

    "Color": Enums.nextEnum(),
    "R": Enums.nextEnum(),
    "G": Enums.nextEnum(),
    "B": Enums.nextEnum()

}


EffectEnums = {
    "Attack": Enums.startEnum(),
}


EntityActionEnums = {
    "Attack": Enums.startEnum(),
    "Charge": Enums.nextEnum(),
    "Timed charge": Enums.nextEnum(),
    "Leap": Enums.nextEnum(),
    "Heal": Enums.nextEnum(),
    "Heal performed": Enums.nextEnum(),
    "Death": Enums.nextEnum(),
    "Sell": Enums.nextEnum(),
    "Respawn": Enums.nextEnum(),
    "Building": Enums.nextEnum(),
    "Upgrading": Enums.nextEnum(),
    "Upgrade done": Enums.nextEnum(),
    "Ready": Enums.nextEnum(),
    "Buff": Enums.nextEnum(),
    "Buff expired": Enums.nextEnum(),
    "Last hit": Enums.nextEnum(),
    "Stun": Enums.nextEnum(),
    "Pick up": Enums.nextEnum(),
    "Scope": Enums.nextEnum(),

    "Cast started": Enums.nextEnum(),
    "Cast success": Enums.nextEnum(),
    "Cast canceled": Enums.nextEnum(),
    "Ability used": Enums.nextEnum(),
    "Ability ended": Enums.nextEnum(),
    "Proc": Enums.nextEnum(),

    "Mass heal": Enums.nextEnum(),
    "Mass damage": Enums.nextEnum(),

    "Teleport": Enums.nextEnum()
}


RequestEnums = {
    "PONG": Enums.PONG,
    "AUTH": Enums.AUTH,
    "JOIN_REQ": Enums.JOIN_REQ,
    "REQ": Enums.REQ,
    "E_CREAT_REQ": Enums.E_CREAT_REQ,
    "E_DESTR_REQ": Enums.E_CREAT_REQ,
    "E_ATTR_GET_REQ": Enums.E_ATTR_GET_REQ,
    "E_ATTR_SET_REQ": Enums.E_ATTR_SET_REQ,
    "E_MOV_REQ": Enums.E_MOV_REQ,
    "E_ACT_REQ": Enums.E_ACT_REQ,
    "READY_REQ": Enums.READY_REQ,
    "SURR_REQ": Enums.SURR_REQ
}


TypeEnums = {
    "Unit": Enums.startEnum(),
    "Item": Enums.nextEnum(),
    "Projectile": Enums.nextEnum(),
    "Area": Enums.nextEnum()
}


SubtypeEnums = {
    "Building slot": Enums.startEnum(),
    "Victory point": Enums.nextEnum(),
    "Goldmine": Enums.nextEnum(),
    "Bear": Enums.nextEnum(),
    "Axeman": Enums.nextEnum(),
    "Hunter": Enums.nextEnum(),
    "Sapper": Enums.nextEnum(),
    "Balloonist": Enums.nextEnum(),
    "Townhall": Enums.nextEnum(),
    "Fay throne": Enums.nextEnum(),
    "Barracks": Enums.nextEnum(),
    "Garrison": Enums.nextEnum(),
    "Watch tower": Enums.nextEnum(),
    "Artillery": Enums.nextEnum(),

    "Smoke cloud": Enums.nextEnum()
}


FactionEnums = {
    "Northerners": Enums.startEnum(),
    "Fay": Enums.nextEnum(),
    "Parliament": Enums.nextEnum(),
}


GameSignalEnums = {
    "Reach base": Enums.startEnum(),
    "Start wave": Enums.nextEnum(),
    "End game": Enums.nextEnum(),
    "Team eliminated": Enums.nextEnum(),
    "Player surrendered": Enums.nextEnum(),
    "Tutorial information": Enums.nextEnum(),
    "Tutorial UI": Enums.nextEnum(),
    "Tutorial end": Enums.nextEnum()
}

GameEndReasonEnums = {
    "VictoryToTeam": Enums.startEnum(),
    "Draw": Enums.nextEnum(),
    "Abnormal termination": Enums.nextEnum()
}
