import Enums
from euclid import Vector3


ENTITY_PREFABS = {
    "User": (
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Info"),
            ("Subtype", "User"),
            ("User instance", None),
            ("Username", ""),
            ("Screenname", ""),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Faction", ""),
        ),),
        (Enums.COMP_TYPE_TAGS, ("User",),),
        (Enums.COMP_TYPE_EVENTIO, None),
        (Enums.COMP_TYPE_PROCESS, (("User process", "userProcess", 1),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Team": (
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Info"),
            ("Subtype", "Team"),
            ("Team instance", None),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Resources", (
                ("Tickets", 250),
                ("Gold", 500),
                ("Honor", 0),
            ),),
            ("Units", (
                ("None", (
                    ("Goldmine", (
                        ("Repair cost", 200),
                        ("Upgrade cost", 250),
                        ("Level maximum", 4),
                    ),),
                ),),
                ("Northerners", (
                    ("Axeman", (
                        ("Cost", 100),
                        ("Unlock cost", 100),
                        ("Unlocked", True),
                    ),),
                    ("Hunter", (
                        ("Cost", 125),
                        ("Unlock cost", 200),
                        ("Unlocked", False),
                    ),),
                    ("Sapper", (
                        ("Cost", 150),
                        ("Unlock cost", 225),
                        ("Unlocked", False),
                    ),),
                    ("Townhall", (
                        ("Upgrade cost", 400),
                        ("Repair cost", 250),
                        ("Level maximum", 4),
                    ),),
                    ("Barracks", (
                        ("Cost", 200),
                        ("Unlock cost", 100),
                        ("Upgrade cost", 250),
                        ("Repair cost", 150),
                        ("Unlocked", True),
                        ("Building time", 6.0),
                        ("Level maximum", 4),
                    ),),
                    ("Garrison", (
                        ("Cost", 250),
                        ("Unlock cost", 200),
                        ("Upgrade cost", 300),
                        ("Repair cost", 150),
                        ("Unlocked", False),
                        ("Building time", 10.0),
                        ("Level maximum", 4),
                    ),),
                    ("Watch tower", (
                        ("Cost", 275),
                        ("Unlock cost", 250),
                        ("Upgrade cost", 300),
                        ("Repair cost", 150),
                        ("Unlocked", False),
                        ("Building time", 10.0),
                        ("Level maximum", 4),
                    ),),
                    ("Artillery", (
                        ("Cost", 250),
                        ("Unlock cost", 300),
                        ("Upgrade cost", 350),
                        ("Repair cost", 200),
                        ("Unlocked", False),
                        ("Building time", 7.5),
                        ("Level maximum", 4),
                    ),),
                ),),
                ("Fay", (
                ),),
                ("Parliament", (
                ),),
            ),),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Team",),),
        (Enums.COMP_TYPE_EVENTIO, None),
        (Enums.COMP_TYPE_PROCESS, (("Team process", "teamProcess", 1),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Match": (
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Info"),
            ("Subtype", "Match"),
            ("Match instance", None),
            ("Name", ""),
            ("Wave interval", 30.0),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Match",),),
        (Enums.COMP_TYPE_TIMER, (
            ("Wave timer", "Start wave", Enums.TIMER_INFINITE, "Wave interval"),
            ("Initial wave", "Start wave", Enums.TIMER_ONCE, 1.0/25.0),
        ),),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Start wave", "startWave"),
        )),
        (Enums.COMP_TYPE_PROCESS, (("Match process", "matchProcess", 25),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Building slot": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Map element"),
            ("Subtype", "Building slot"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Open"),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Ground",),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .1),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Victory point": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Map element"),
            ("Subtype", "Victory point"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Alignment", 0),
            ("Sight range", 5.0),
            ("Build range", 6.0),
            ("Capture range", 4.0),
            ("Capture time", 10),
            ("Capture counter", 10),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Ground", "Capturable"),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Capture", Vector3(0, 0, 0), "Capture range"),
        ),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .5),),),
        (Enums.COMP_TYPE_PROCESS, (("Victory point process", "vpProcess", 25),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Goldmine": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Goldmine"),
            ("Faction", "None"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Stats", (
                ("Armor", 2),
                ("Magic resist", 2),
                ("Level", 1),
            )),
            ("Sight range", 5.0),
            ("Capture range", 4.0),
            ("Capture time", 15),
            ("Capture counter", 15),
            ("Gold", 0),
            ("Gold maximum", 250),
            ("Generation interval", 1.15),
            ("Generation amount", 5),
            ("Hitpoints", 120),
            ("Hitpoints maximum", 120),
        ),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Building", "Capturable"),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Capture", Vector3(0, 0, 0), "Capture range"),
        ),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .5),),),
        (Enums.COMP_TYPE_TIMER, (("Generation timer", "Generate", Enums.TIMER_INFINITE, "Generation interval",),),),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Generate", "generateHandler"),
            ("Collect", "goldCollectionHandler"),
            ("Upgrade", "upgradeGoldmine"),
            ("Repair", "repairHandler"),
            ("Damage", "damageHandler"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("Goldmine process", "goldmineProcess", 25),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Bear": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_WAYPOINTMOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Bear"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Username", ""),
            ("Status", "Idle"),
            ("Speed", 1.8),
            ("Visible to enemy", False),
            ("Stats", (
                ("Strength", 5),
                ("Dexterity", 5),
                ("Intelligence", 5),
                ("Armor", 1),
                ("Magic resist", 0),
                ("Level", 1),
                ("Experience", 0),
                ("Next level", 100),
                ("Experience total", 0),
            ),),
            ("Hitpoints maximum", 35),
            ("Hitpoints", 35),
            ("Damage minimum", 4),
            ("Damage maximum", 7),
            ("Attack period", 1.5),
            ("Attack time", .25),
            ("Attack range", 1.25),
            ("Sight range", 5.0),
            ("Respawn time", 10.0),
            ("Charge", (
                ("Ready", True),
                ("Time", 1.0),
                ("Cooldown", 15.0),
                ("Speed increase", 8.0),
                ("Damage", 12),
                ("Range", .5),
                ("Victims", []),
            ),),
            ("Target", Enums.NULL_ID),
            ("Target tags", ["Targetable", "Ground"]),
            ("Ignore tags", ["Capturable"]),
            ("Experience reward", 50),
            ("Honor reward", 25),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Melee", "Hero"),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .5),),),
        (Enums.COMP_TYPE_EFFECT, (
            ("Attack", "basicAttack"),
            ("Charge", "bearChargeAttack"),
        ),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Attack", Vector3(0, 0, 0), "Attack range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Charge", Vector3(0, 0, 0), ("Charge", "Range"),),
            (Enums.SHAPE_TYPE_CIRCLE, "Experience", Vector3(0, 0, 0), 4.0),
        ),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Attack", "attackHandler"),
            ("Damage", "damageHandler"),
            ("Death", "heroDeathHandler"),
            ("Heal", "healHandler"),
            ("Respawn", "respawnHandler"),
            ("Experience", "experienceHandler"),
            ("Level up", "bearLevelUpHandler"),
            ("Move", "moveHandler"),
            ("Stop", "stopHandler"),
            ("Target", "targetHandler"),
            ("Charge", "bearCharge"),
            ("Charge end", "chargeEnd"),
            ("Charge ready", "chargeReady"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("AI", "basicHeroAI", 1),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Sniper": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_WAYPOINTMOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Sniper"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Username", ""),
            ("Status", "Idle"),
            ("Speed", 2.1),
            ("Visible to enemy", False),
            ("Stats", (
                ("Strength", 5),
                ("Dexterity", 5),
                ("Intelligence", 5),
                ("Armor", 0),
                ("Magic resist", 0),
                ("Level", 1),
                ("Experience", 0),
                ("Next level", 100),
                ("Experience total", 0),
            ),),
            ("Hitpoints maximum", 25),
            ("Hitpoints", 25),
            ("Damage minimum", 9),
            ("Damage maximum", 12),
            ("Attack period", 2.25),
            ("Attack time", .25),
            ("Attack range", 4.5),
            ("Sight range", 6.0),
            ("Respawn time", 10.0),
            ("Charge", (
                ("Ready", True),
                ("Time", 1.0),
                ("Cooldown", 20.0),
                ("Damage", 16),
                ("Range", .5),
            ),),
            ("Target", Enums.NULL_ID),
            ("Target tags", ["Targetable"]),
            ("Ignore tags", ["Capturable"]),
            ("Experience reward", 50),
            ("Honor reward", 25),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Ranged", "Hero"),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .5),),),
        (Enums.COMP_TYPE_EFFECT, (
            ("Attack", "basicAttack"),
        ),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Attack", Vector3(0, 0, 0), "Attack range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Experience", Vector3(0, 0, 0), 4.0),
        ),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Attack", "attackHandler"),
            ("Damage", "damageHandler"),
            ("Death", "heroDeathHandler"),
            ("Heal", "healHandler"),
            ("Respawn", "respawnHandler"),
            ("Experience", "experienceHandler"),
            ("Level up", "sniperLevelUpHandler"),
            ("Move", "moveHandler"),
            ("Stop", "stopHandler"),
            ("Target", "targetHandler"),
            ("Charge", "sniperCharge"),
            ("Charge ready", "chargeReady"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("AI", "basicHeroAI", 1),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Axeman": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_WAYPOINTMOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Axeman"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Speed", 1.5),
            ("Stats", (
                ("Armor", 0),
                ("Magic resist", 0),
            )),
            ("Hitpoints maximum", 20),
            ("Hitpoints", 20),
            ("Damage minimum", 3),
            ("Damage maximum", 5),
            ("Attack period", 1.6),
            ("Attack time", .25),
            ("Attack range", 1.0),
            ("Sight range", 5.0),
            ("Target", Enums.NULL_ID),
            ("Target tags", ["Targetable", "Ground"]),
            ("Ignore tags", ["Building", "Capturable"]),
            ("Experience reward", 8),
            ("Honor reward", 10),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Melee", "Creep"),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .375),),),
        (Enums.COMP_TYPE_EFFECT, (("Attack", "basicAttack"),),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Attack", Vector3(0, 0, 0), "Attack range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Experience", Vector3(0, 0, 0), 4.0),
        ),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Reach base", "reachBaseHandler"),
            ("Attack", "attackHandler"),
            ("Damage", "damageHandler"),
            ("Death", "deathHandler"),
            ("Heal", "healHandler"),
            ("Target", "targetHandler"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("AI", "basicCreepAI", 7),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Axeman defender": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Axeman"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Speed", 1.5),
            ("Stats", (
                ("Armor", 0),
                ("Magic resist", 0),
            )),
            ("Hitpoints maximum", 20),
            ("Hitpoints", 20),
            ("Damage minimum", 3),
            ("Damage maximum", 5),
            ("Attack period", 1.6),
            ("Attack time", .25),
            ("Attack range", 1.0),
            ("Sight range", 5.0),
            ("Target", Enums.NULL_ID),
            ("Target tags", ["Targetable", "Ground"]),
            ("Ignore tags", ["Building", "Capturable"]),
            ("Rally point", Vector3(0, 0, 0)),
            ("Home", Enums.NULL_ID),
            ("Experience reward", 8),
            ("Honor reward", 10),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Melee", "Defender", "Creep"),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .375),),),
        (Enums.COMP_TYPE_EFFECT, (("Attack", "basicAttack"),),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Attack", Vector3(0, 0, 0), "Attack range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Experience", Vector3(0, 0, 0), 4.0),
        ),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Attack", "attackHandler"),
            ("Damage", "damageHandler"),
            ("Death", "deathHandler"),
            ("Heal", "healHandler"),
            ("Target", "targetHandler"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("AI", "aggroAI", 7),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Hunter": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_WAYPOINTMOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Hunter"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Speed", 1.75),
            ("Stats", (
                ("Armor", 0),
                ("Magic resist", 0),
            )),
            ("Hitpoints maximum", 14),
            ("Hitpoints", 14),
            ("Damage minimum", 7),
            ("Damage maximum", 12),
            ("Attack period", 2.25),
            ("Attack time", .25),
            ("Attack range", 4.5),
            ("Sight range", 6.0),
            ("Target", Enums.NULL_ID),
            ("Target tags", ["Targetable"]),
            ("Ignore tags", ["Building", "Capturable"]),
            ("Experience reward", 10),
            ("Honor reward", 10),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Ranged", "Creep"),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .375),),),
        (Enums.COMP_TYPE_EFFECT, (("Attack", "basicAttack"),),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Attack", Vector3(0, 0, 0), "Attack range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Experience", Vector3(0, 0, 0), 5.0),
        ),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Reach base", "reachBaseHandler"),
            ("Attack", "attackHandler"),
            ("Damage", "damageHandler"),
            ("Death", "deathHandler"),
            ("Heal", "healHandler"),
            ("Target", "targetHandler"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("AI", "basicCreepAI", 7),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Hunter defender": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Hunter"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Speed", 1.75),
            ("Stats", (
                ("Armor", 0),
                ("Magic resist", 0),
            )),
            ("Hitpoints maximum", 14),
            ("Hitpoints", 14),
            ("Damage minimum", 7),
            ("Damage maximum", 12),
            ("Attack period", 2.25),
            ("Attack time", .25),
            ("Attack range", 4.5),
            ("Sight range", 6.5),
            ("Target", Enums.NULL_ID),
            ("Target tags", ["Targetable"]),
            ("Ignore tags", ["Building", "Capturable"]),
            ("Rally point", Vector3(0, 0, 0)),
            ("Home", Enums.NULL_ID),
            ("Experience reward", 10),
            ("Honor reward", 10),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Ranged", "Defender", "Creep"),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .375),),),
        (Enums.COMP_TYPE_EFFECT, (("Attack", "basicAttack"),),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Attack", Vector3(0, 0, 0), "Attack range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Experience", Vector3(0, 0, 0), 5.0),
        ),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Attack", "attackHandler"),
            ("Damage", "damageHandler"),
            ("Death", "deathHandler"),
            ("Heal", "healHandler"),
            ("Target", "targetHandler"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("AI", "aggroAI", 7),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Sapper": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_WAYPOINTMOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Sapper"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Speed", 1.25),
            ("Stats", (
                ("Armor", 1),
                ("Magic resist", 0),
            )),
            ("Hitpoints maximum", 30),
            ("Hitpoints", 30),
            ("Damage minimum", 10),
            ("Damage maximum", 13),
            ("Attack period", 1.75),
            ("Attack time", .25),
            ("Attack range", 1.5),
            ("Sight range", 4.0),
            ("Target", Enums.NULL_ID),
            ("Target tags", ["Targetable", "Building"]),
            ("Ignore tags", ["Capturable", "Base"]),
            ("Experience reward", 15),
            ("Honor reward", 12),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Melee", "Creep"),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .5),),),
        (Enums.COMP_TYPE_EFFECT, (("Attack", "basicAttack"),),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Attack", Vector3(0, 0, 0), "Attack range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Experience", Vector3(0, 0, 0), 4.0),
        ),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Reach base", "reachBaseHandler"),
            ("Attack", "attackHandler"),
            ("Damage", "damageHandler"),
            ("Death", "deathHandler"),
            ("Heal", "healHandler"),
            ("Target", "targetHandler"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("AI", "sapperAI", 7),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Townhall": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Townhall"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Stats", (
                ("Armor", 2),
                ("Magic resist", 2),
                ("Level", 1),
            )),
            ("Sight range", 5.0),
            ("Heal range", 3.0),
            ("Heal minimum", 2),
            ("Heal maximum", 3),
            ("Hitpoints", 100),
            ("Hitpoints maximum", 100),
        ),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_TAGS, ("Ground", "Building", "Base"),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), 1.0),),),
        (Enums.COMP_TYPE_EFFECT, (("Heal heroes", "basicHeal"),),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Sight", Vector3(0, 0, 0), "Sight range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Heal", Vector3(0, 0, 0), "Heal range"),
            (Enums.SHAPE_TYPE_CIRCLE, "Reach base", Vector3(0, 0, 0), .75),
        ),),
        (Enums.COMP_TYPE_TIMER, (("Heal timer", "Heal heroes", Enums.TIMER_INFINITE, 1.0),),),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Heal heroes", "healHeroes"),
            ("Upgrade", "upgradeTownhall"),
            ("Repair", "repairHandler"),
            ("Damage", "damageHandler"),
        ),),
        (Enums.COMP_TYPE_PROCESS, (("Townhall process", "townhallProcess", 20),),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Barracks": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Barracks"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Stats", (
                ("Armor", 1),
                ("Magic resist", 0),
                ("Level", 1),
            )),
            ("Sight range", 5.0),
            ("Unit queue", ["Axeman", "Axeman", "Axeman", "", ""]),
            ("Queue index", 0),
            ("Unit path", []),
            ("Hitpoints", 75),
            ("Hitpoints maximum", 75),
            ("Spawn period", 1.25),
            ("Experience reward", 25),
            ("Gold reward", 50),
        ),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Building"),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .75),),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Wave", "waveHandler"),
            ("Spawn", "spawnQueuedUnit"),
            ("Enqueue", "enqueueUnit"),
            ("Clear slot", "clearUnitSlot"),
            ("Swap slots", "swapUnitSlots"),
            ("Upgrade", "upgradeBarracks"),
            ("Sell", "sellHandler"),
            ("Repair", "repairHandler"),
            ("Ready", "buildingReady"),
            ("Damage", "damageHandler"),
        ),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Garrison": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Garrison"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Stats", (
                ("Armor", 1),
                ("Magic resist", 0),
                ("Level", 1),
            )),
            ("Sight range", 5.0),
            ("Aggro range", 7.0),
            ("Defender type", "Axeman defender"),
            ("Defenders", []),
            ("Defenders maximum", 2),
            ("Hitpoints", 75),
            ("Hitpoints maximum", 75),
            ("Reinforcement period", 10.0),
            ("Rally point", Vector3(0, 0, 0)),
            ("Rally range", 3.0),
            ("Experience reward", 35),
            ("Gold reward", 25),
        ),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Building"),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Aggro", Vector3(0, 0, 0), "Aggro range"),
        ),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .75),),),
        (Enums.COMP_TYPE_TIMER, (("Reinforcement timer", "Spawn", Enums.TIMER_INFINITE, "Reinforcement period"),),),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Upgrade", "upgradeGarrison"),
            ("Repair", "repairHandler"),
            ("Sell", "sellHandler"),
            ("Spawn", "spawnDefender"),
            ("Rally", "rallyHandler"),
            ("Ready", "buildingReady"),
            ("Damage", "damageHandler"),
        ),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),

    "Watch tower": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Unit"),
            ("Subtype", "Watch tower"),
            ("Faction", "Northerners"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Status", "Idle"),
            ("Stats", (
                ("Armor", 1),
                ("Magic resist", 0),
                ("Level", 1),
            )),
            ("Sight range", 8.0),
            ("Aggro range", 10.0),
            ("Defender type", "Hunter defender"),
            ("Defenders", []),
            ("Defenders maximum", 2),
            ("Hitpoints", 65),
            ("Hitpoints maximum", 65),
            ("Reinforcement period", 10.0),
            ("Rally point", Vector3(0, 0, 0)),
            ("Rally range", 2.25),
            ("Experience reward", 35),
            ("Gold reward", 25),
        ),),
        (Enums.COMP_TYPE_COMBATATTRIBUTES, None),
        (Enums.COMP_TYPE_TAGS, ("Targetable", "Ground", "Building"),),
        (Enums.COMP_TYPE_SENSOR, (
            (Enums.SHAPE_TYPE_CIRCLE, "Aggro", Vector3(0, 0, 0), "Aggro range"),
        ),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .75),),),
        (Enums.COMP_TYPE_TIMER, (("Reinforcement timer", "Spawn", Enums.TIMER_INFINITE, "Reinforcement period"),),),
        (Enums.COMP_TYPE_EVENTIO, (
            ("Upgrade", "upgradeWatchTower"),
            ("Repair", "repairHandler"),
            ("Sell", "sellHandler"),
            ("Spawn", "spawnDefender"),
            ("Rally", "rallyHandler"),
            ("Ready", "buildingReady"),
            ("Damage", "damageHandler"),
        ),),
        (Enums.COMP_TYPE_NETWORK, None),
    ),
                  
                  
                  
    "Sniper bullet": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Ability projectiles"),
            ("Subtype", "Sniper bullet"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Speed", 30.0),
            ("Projectile lifetime", 2.0),
            ("Damage", 20),
            ("Level", 1),
            ("Penetrate", True),
            ("Victims", []),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Projectile",),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .25),),),
        (Enums.COMP_TYPE_SENSOR, ((Enums.SHAPE_TYPE_CIRCLE, "Damage", Vector3(0, 0, 0), 0.5),),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_PROCESS, (("AI", "bulletAI", 1),),),
        (Enums.COMP_TYPE_EVENTIO, (
             ("Charge", "sniperCharge"),
             ("Lifetime end", "sniperprojectileEnd"),
        ),),
        (Enums.COMP_TYPE_EFFECT, (
            ("Charge", "sniperBulletDamage"),
        ),),  
        (Enums.COMP_TYPE_NETWORK, None),
    ), 
             
             
                
  

    "SteamGrenade": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Ability projectiles"),
            ("Subtype", "Steam grenade"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Speed", 7.0),
            ("Damage", 20),
            ("Level", 1),
            ("Penetrate", False),
            ("Victims", []),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Mine","Projectile"),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .25),),),
        (Enums.COMP_TYPE_SENSOR, ((Enums.SHAPE_TYPE_CIRCLE, "Damage", Vector3(0, 0, 0), 2),),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_PROCESS, (("AI", "mineAI", 1),),),
        (Enums.COMP_TYPE_EVENTIO, (
             ("Charge", "granadierCharge"),
        ),),
        (Enums.COMP_TYPE_EFFECT, (
            ("Charge", "steamGranadeDamage"),
        ),),  
        (Enums.COMP_TYPE_NETWORK, None),
    ), 
                  
                  
                  
    "HealingTotem": (
        (Enums.COMP_TYPE_TRANSFORM, None),
        (Enums.COMP_TYPE_MOVER, None),
        (Enums.COMP_TYPE_ATTRIBUTES, (
            ("Type", "Ability projectiles"),
            ("Subtype", "Healing totem"),
            ("Team", Enums.MATCH_TEAM_NULL),
            ("Speed", 1.0),
            ("Heal value", 20),
            ("Level", 1),
            ("Penetrate", False),
            ("Victims", []),
        ),),
        (Enums.COMP_TYPE_TAGS, ("Mine","Projectile"),),
        (Enums.COMP_TYPE_PHYSICAL, ((Enums.SHAPE_TYPE_CIRCLE, Vector3(0, 0, 0), .25),),),
        (Enums.COMP_TYPE_SENSOR, ((Enums.SHAPE_TYPE_CIRCLE, "Damage", Vector3(0, 0, 0), 1.5),),),
        (Enums.COMP_TYPE_TIMER, None),
        (Enums.COMP_TYPE_PROCESS, (("AI", "healingTotemAI", 1),),),
        (Enums.COMP_TYPE_EVENTIO, (
             ("Charge", "healingTotemCharge"),
        ),),
        (Enums.COMP_TYPE_EFFECT, (
            ("Charge", "healingTotemEffect"),
        ),),  
        (Enums.COMP_TYPE_NETWORK, None),
    ),      
                  
                  
                  
                  
                  
                  
                  
}


ENTITY_PREFAB_COUNT = len(ENTITY_PREFABS)