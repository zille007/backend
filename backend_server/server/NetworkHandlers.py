from Component import *
from utils import listToVector, nestedTupleToNetworkDict, findClosestEntity, unitQueueHasAvailableSlots, clamp, dictToNestedTuple
import Enums
from StringEnums import *


#####################
## NetworkCommands ##
#####################


def movementStarted(match, eventType, data, entity):
    xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    if mover.hasDestination():
        match.broadcastChannel.sendCommand("E_MOV", {
            "id": entity.id,
            "spos": tuple(xform.getWorldPosition()),
            "epos": tuple(mover.destination),
            "speed": mover.speed
        })
    else:
        match.broadcastChannel.sendCommand("E_MOV_INF", {
            "id": entity.id,
            "spos": tuple(xform.getWorldPosition()),
            "dir": tuple(xform.getWorldDirection()),
            "speed": mover.speed
        })


def movementSpeed(match, eventType, data, entity):
    mover = entity.getComponent(Enums.COMP_TYPE_MOVER)
    if mover.isMoving():
        xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
        if mover.hasDestination():
            match.broadcastChannel.sendCommand("E_MOV", {
                "id": entity.id,
                "spos": tuple(xform.getWorldPosition()),
                "epos": tuple(mover.destination),
                "speed": mover.speed
            })
        else:
            match.broadcastChannel.sendCommand("E_MOV_INF", {
                "id": entity.id,
                "spos": tuple(xform.getWorldPosition()),
                "dir": tuple(xform.getWorldDirection()),
                "speed": mover.speed
            })


def movementEnded(match, eventType, data, entity):
    xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
    match.broadcastChannel.sendCommand("E_STOP", {
        "id": entity.id,
        "pos": tuple(xform.getWorldPosition()),
        "dir": tuple(xform.getWorldDirection())
    })


def movementTeleport(match, eventType, position, entity):
    match.broadcastChannel.sendCommand("E_RELOC", {
        "id": entity.id,
        "pos": tuple(position),
    })


def attributesChanged(match, eventType, (key, new, old, changeType), entity):
    attribs = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
    if attribs.get("Type") == "Info":
        if changeType == Enums.ATTR_SET_MULTIPLE:
            scope = attribs.get("Subtype")
            if scope == "User":
                match.broadcastChannel.sendCommand("SET", {
                    "scope": scope,
                    "username": attribs.get("Username"),
                    "type": changeType,
                    "attributes": nestedTupleToNetworkDict(new),
                })
            elif scope == "Team":
                match.broadcastChannel.sendCommand("SET", {
                    "scope": scope,
                    "team": attribs.get("Team"),
                    "type": changeType,
                    "attributes": nestedTupleToNetworkDict(new),
                })
            elif scope == "Match":
                match.broadcastChannel.sendCommand("SET", {
                    "scope": scope,
                    "type": changeType,
                    "attributes": nestedTupleToNetworkDict(new),
                })
        else:
            if new is not None:
                scope = attribs.get("Subtype")
                if isinstance(key, tuple):
                    for k in key:
                        if not AttributeEnums.has_key(k):
                            return
                    if scope == "User":
                        match.broadcastChannel.sendCommand("SET", {
                            "scope": scope,
                            "username": attribs.get("Username"),
                            "type": changeType,
                            "key": [AttributeEnums[k] for k in key],
                            "value": tuple(new) if isinstance(new, Vector3) else new,
                            })
                    elif scope == "Team":
                        match.broadcastChannel.sendCommand("SET", {
                            "scope": scope,
                            "team": attribs.get("Team"),
                            "type": changeType,
                            "key": [AttributeEnums[k] for k in key],
                            "value": tuple(new) if isinstance(new, Vector3) else new,
                            })
                    elif scope == "Match":
                        match.broadcastChannel.sendCommand("SET", {
                            "scope": scope,
                            "type": changeType,
                            "key": [AttributeEnums[k] for k in key],
                            "value": tuple(new) if isinstance(new, Vector3) else new,
                            })
                else:
                    if not AttributeEnums.has_key(key):
                        return
                    if scope == "User":
                        match.broadcastChannel.sendCommand("SET", {
                            "scope": scope,
                            "username": attribs.get("Username"),
                            "type": changeType,
                            "key": AttributeEnums[key],
                            "value": tuple(new) if isinstance(new, Vector3) else new,
                        })
                    elif scope == "Team":
                        match.broadcastChannel.sendCommand("SET", {
                            "scope": scope,
                            "team": attribs.get("Team"),
                            "type": changeType,
                            "key": AttributeEnums[key],
                            "value": tuple(new) if isinstance(new, Vector3) else new,
                        })
                    elif scope == "Match":
                        match.broadcastChannel.sendCommand("SET", {
                            "scope": scope,
                            "type": changeType,
                            "key": AttributeEnums[key],
                            "value": tuple(new) if isinstance(new, Vector3) else new,
                        })
    else:
        if eventType == Enums.COMP_EVENT_USERLOCAL_ATTRIBUTES_CHANGED:
            pass

        if changeType == Enums.ATTR_SET_MULTIPLE:
            match.broadcastChannel.sendCommand("E_SET", {
                "id": entity.id,
                "type": changeType,
                "attributes": nestedTupleToNetworkDict(new),
            })
        else:
            if new is not None:
                if isinstance(key, tuple):
                    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
                    if combatAttr and combatAttr.hasModifiers(key):
                        match.broadcastChannel.sendCommand("E_SET", {
                            "id": entity.id,
                            "type": changeType,
                            "key": [AttributeEnums[k] for k in key],
                            "value": combatAttr.get(key),
                        })
                    else:
                        match.broadcastChannel.sendCommand("E_SET", {
                            "id": entity.id,
                            "type": changeType,
                            "key": [AttributeEnums[k] for k in key],
                            "value": tuple(new) if isinstance(new, Vector3) else new,
                        })
                else:
                    combatAttr = entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES)
                    if combatAttr and combatAttr.hasModifiers(key):
                        match.broadcastChannel.sendCommand("E_SET", {
                            "id": entity.id,
                            "type": changeType,
                            "key": AttributeEnums[key],
                            "value": combatAttr.get(key),
                        })
                    else:
                        match.broadcastChannel.sendCommand("E_SET", {
                            "id": entity.id,
                            "type": changeType,
                            "key": AttributeEnums[key],
                            "value": tuple(new) if isinstance(new, Vector3) else utils.listToNetworkList(new) if isinstance(new, list) else new,
                        })


def combatAttributeAdded(match, eventType, (key, token, mod, modType), entity):
    if isinstance(key, tuple):
        match.broadcastChannel.sendCommand("E_SET", {
            "id": entity.id,
            "type": Enums.ATTR_SET,
            "key": [AttributeEnums[k] for k in key],
            "value": entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES).queryEffectiveAttribute(key)
        })
    else:
        match.broadcastChannel.sendCommand("E_SET", {
            "id": entity.id,
            "type": Enums.ATTR_SET,
            "key": AttributeEnums[key],
            "value": entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES).queryEffectiveAttribute(key)
        })


def combatAttributeRemoved(match, eventType, (key, token, mod, modType), entity):
    if isinstance(key, tuple):
        match.broadcastChannel.sendCommand("E_SET", {
            "id": entity.id,
            "type": Enums.ATTR_SET,
            "key": [AttributeEnums[k] for k in key],
            "value": entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES).queryEffectiveAttribute(key)
        })
    else:
        match.broadcastChannel.sendCommand("E_SET", {
            "id": entity.id,
            "type": Enums.ATTR_SET,
            "key": AttributeEnums[key],
            "value": entity.getComponent(Enums.COMP_TYPE_COMBATATTRIBUTES).queryEffectiveAttribute(key)
        })


def effectLaunched(match, eventType, (effectName, targets), entity):
    # TODO maybe at some point we might want something like this
    #match.broadcastChannel.sendCommand("E_EFFECT", {
    #    "src_id": entity.id,
    #    "tgt_ids": [t.id for t in targets],
    #    "type": EffectEnums[effectName]
    #})
    pass


def entityCreated(match, eventType, data, entity):
    entity.getComponent(Enums.COMP_TYPE_NETWORK).initialized = True
    attributes = entity.getAttributes()
    xform = entity.getComponent(Enums.COMP_TYPE_TRANSFORM)
    tags = entity.getComponent(Enums.COMP_TYPE_TAGS)
    physical = entity.getComponent(Enums.COMP_TYPE_PHYSICAL)
    attrDict = attributes.getNetworkDictionary()
    if tags:
        attrDict[AttributeEnums["Tags"]] = tags.getList()
    match.broadcastChannel.sendCommand("E_CREAT", {
        "id": entity.id,
        "pos": tuple(xform.getWorldPosition()),
        "dir": tuple(xform.getWorldDirection()),
        "size": float(physical.getSize()) if physical else 0.0,
        "attributes": attrDict
    })


def entityDestroyed(match, eventType, data, entity):
    match.broadcastChannel.sendCommand("E_DESTR", {
        "id": entity.id
    })


def entityDamaged(match, eventType, (damage, originator), entity):
    match.broadcastChannel.sendCommand("E_DMG", {
        "id": entity.id,
        "type": 0,
        "dmg": int(damage),
        "orig_id": 0 if originator is None else originator.id
    })


def entityAttacked(match, eventType, target, entity):
    if entity.isDestroyed() or target.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Attack"],
        "target_id": target.id,
    })


def entityPerformedHeal(match, eventType, target, entity):
    if entity.isDestroyed() or target.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Heal performed"],
        "target_id": target.id,
    })


def entityHealed(match, eventType, (heal, originator), entity):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Heal"],
        "target_id": 0 if originator is None else originator,
        "heal": int(heal)
    })


def entityAoeHealed( match, eventType, targets, entity):
    if entity.isDestroyed():
        return

    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Mass heal"],
        "targets": list(targets)
    })

def entityAoeDamaged( match, eventType, targets, entity):
    if entity.isDestroyed():
        return

    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Mass damage"],
        "targets": list(targets)
    })

def entityCharged(match, eventType, target, entity ):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Charge"]
    })

def entityChargedWithTime(match, eventType, time, entity):
    if entity.isDestroyed():
        return

    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Charge"],
        "time": 0.0 if time is None else float(time)
    })


def entityLeaped(match, eventType, time, entity):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Leap"],
        "time": float(time)
    })


def entityBuffed(match, eventType, time_and_type_and_token, entity):
    if entity.isDestroyed():
        return
    time, attribute, token = time_and_type_and_token
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Buff"],
        "time": float(time),
        "attribute": attribute,
        "token":token
    })

def entityBuffExpired( match, eventType, token_and_type, entity ):
    if entity.isDestroyed():
        return

    token, attribute = token_and_type
    match.log.info( "Entity buff with token %d expired on %s" % (token, entity.getName()))
    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id": entity.id,
        "type":EntityActionEnums["Buff expired"],
        "attribute":attribute,
        "token":token
    })

def buildingUpgrading(match, eventType, time, entity):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Upgrading"],
        "time": time
    })
    pass


def buildingUpgraded(match, eventType, data, entity):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Upgrade done"]
    })
    pass


def buildingReady(match, eventType, data, building):
    if building.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": building.id,
        "type": EntityActionEnums["Ready"],
    })


def building(match, eventType, buildingTime, building):
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": building.id,
        "type": EntityActionEnums["Building"],
        "building_time": buildingTime,
    })


def entityDied(match, eventType, data, entity):
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Death"],
    })


def entitySold(match, eventType, data, entity):
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Sold"],
    })


def entityRespawned(match, eventType, data, entity):
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Respawn"],
    })


def unitReachedBase(match, eventType, enemyBase, entity):
    match.broadcastChannel.sendCommand("SGNL", {
        "type": GameSignalEnums["Reach base"],
        "unit_id": entity.id,
        "base_id": enemyBase.id,
    })


def startWave(match, eventType, nextWave, entity):
    match.broadcastChannel.sendCommand("SGNL", {
        "type": GameSignalEnums["Start wave"],
        "time": nextWave,
    })


def teamEliminated(match, eventType, eliminatedTeam, entity):
    match.broadcastChannel.sendCommand("SGNL", {
        "type" :GameSignalEnums["Team eliminated"],
        "team": eliminatedTeam
    })


def endGameWithWin(match, eventType, winningTeam, entity):
    match.broadcastChannel.sendCommand("SGNL", {
        "type": GameSignalEnums["End game"],
        "reason": GameEndReasonEnums["VictoryToTeam"],
        "winner": winningTeam
    })
    match.resolveMatchWithWinner( winningTeam )


def heroPerformedLastHit(match, eventType, target, entity):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Last hit"],
        "target_id": target.id
    })


def unitStunned(match, eventType, data, entity):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Stun"]
    })


def itemPickedUp(match, eventType, itemtype, entity):
    #match.log.info( "Item pickup: entity %d type %s" % (entity.id, itemtype))
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Pick up"],
        "item_type":itemtype
    })


def entityUsedScope(match, eventType, data, entity):
    if entity.isDestroyed():
        return
    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Scope"]
    })


def heroCastStarted( match, eventType, (ability_name, cast_time), entity ):
    if entity.isDestroyed():
        return

    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id":entity.id,
        "type": EntityActionEnums[ "Cast started" ],
        "ability":ability_name,
        "time":float(cast_time)
    })


def heroCastFinished( match, eventType, ability_name, entity ):
    if entity.isDestroyed():
        return

    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id":entity.id,
        "type": EntityActionEnums[ "Cast success" ],
        "ability":ability_name
    })


def heroCastCanceled( match, eventType, ability_name, entity ):
    if entity.isDestroyed():
        return()

    # consider canceling none to mean that all ongoing casts
    # should be canceled
    if ability_name is None:
        ability_name = "ALL"

    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id":entity.id,
        "type":EntityActionEnums[ "Cast canceled" ],
        "ability":ability_name
    })


def unitAbilityUsed(match, eventType, (ability_name, duration, target_id, position), entity):
    if entity.isDestroyed():
        return

    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Ability used"],
        "ability": ability_name,
        #"casting_time": float(casting_time),
        "time": float(duration),
        "position": list(position),
        "target_id": int(target_id)
    })


def unitAbilityEnded(match, eventType, ability_name, entity):
    if entity.isDestroyed():
        return

    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Ability ended"],
        "ability": ability_name,
    })


def procHappened(match, eventType, (procEvent, procEffect, procParams, procEventParams), entity):
    match.broadcastChannel.sendCommand("E_ACTION", {
        "id": entity.id,
        "type": EntityActionEnums["Proc"],
        "proc_event": procEvent,
        "proc_effect": procEffect,
        "proc_params": procParams,
    })

def tutorialMessageDisplayed(match, eventType, (text, space, position, clear_condition, clear_flag, clear_extra_arguments), entity):
    data = {
        "type": GameSignalEnums[ "Tutorial information" ],
        "text": text,
        "space": space,
        "clear_condition": clear_condition,
        "clear_flag": clear_flag,
        "position": position
    }

    data = dict( data.items() + clear_extra_arguments.items() )

    match.log.info( "Sending tutorial message (on space %s pos %s): %s" % (space, str(position), text))
    match.broadcastChannel.sendCommand( "SGNL", data)

def tutorialUIControlled(match, eventType, (ui_element, state), entity):
    match.broadcastChannel.sendCommand( "SGNL", {
        "type": GameSignalEnums[ "Tutorial UI" ],
        "ui_element": ui_element,
        "state": state
    })

def tutorialEnded(match,eventType, args, entity ):
    match.broadcastChannel.sendCommand( "SGNL", {
        "type": GameSignalEnums[ "Tutorial end" ]
    })

def entityTeleported( match, eventType, position, entity ):
    match.broadcastChannel.sendCommand( "E_ACTION", {
        "id":entity.id,
        "type":EntityActionEnums[ "Teleport" ],
        "position": position
    })



#####################
## NetworkRequests ##
#####################

def playerTutorialAdvanceRequest(user, seq_no, **kwargs):
    pass

def playerSurrenderRequest(user, seq_no, **kwargs):
    user.match.networkRequestReply(user, seq_no, "SURR_RES", {"res": 1})
    user.match.broadcastChannel.sendCommand("SGNL", {
        "type": GameSignalEnums["Player surrendered"],
        "username": user.username
    })
    user.processSurrender()
    user.forceCloseConnection()


def playerReadyRequest(user, seq_no, **kwargs):
    match = user.match
    user.ready = True
    match.log.info("Player " + user.username + " (" + user.userType + ") reports ready...")
    if match.countReadyUsers() >= match.playersRequiredToStart and match.state != Enums.MATCH_STATE_RUNNING:
        match.log.info( "Will send all players ready..." )
        match.sendReady()


def entityCreateRequest(user, seq_no, prefab, pos, dir, user_id, attributes=None, **kwargs):
    user.match.world.createGameEntityForUser( prefab, listToVector(pos), listToVector(dir), user_id, dictToNestedTuple(attributes) )
    #user.match.world.createGameEntity(prefab, listToVector(pos), listToVector(dir), dictToNestedTuple(attributes))
    user.match.log.info("User " + user.username + " sent en E_CREAT_REQ and created a " + prefab + ".")


def entityDestroyRequest(user, seq_no, entityID, **kwargs):
    entity = user.match.world.getEntityByID(entityID)
    if entity:
        entity.receiveEvent("_destroy")
        user.match.log.info("User " + user.username + " sent en E_DESTR_REQ with entityID " + str(entityID) + ".")


def entityAttributeGetRequest(user, seq_no, entityID, key, **kwargs):
    entity = user.match.world.getEntityByID(entityID)
    if entity:
        value = entity.getAttribute(key)
        if value:
            user.match.networkRequestReply(user, seq_no, "E_ATTR_GET_RES", {
                "res": 1,
                "entityID": entityID,
                "key": key,
                "value": value,
            })
        else:
            user.match.networkRequestReply(user, seq_no, "E_ATTR_GET_RES", {
                "res": 0,
            })


def entityAttributeSetRequest(user, seq_no, entityID, key, value, **kwargs):
    entity = user.match.world.getEntityByID(entityID)
    if entity:
        attr = entity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        if isinstance(key, list):
            attr.set(tuple(key), value)
        elif isinstance(key, str):
            attr.set(key, value)
        elif isinstance(key, unicode):
            attr.set(str(key), value)


def request(user, seq_no, type=None, unit=None, pos=None, t=-1, **kwargs):
    world = user.match.world
    if user.userType != "Master":
        user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})
        return
    if type == "Build":
        bcks = False
        teamAttr = world.getTeamEntity(user.teamId).getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        cbb = teamAttr.get( "Control toggles.Can build Barracks" )
        cbg = teamAttr.get( "Control toggles.Can build Garrison" )

        if unit == "Barracks" and cbb is not None and cbb == False:
            return

        if unit == "Garrison" and cbg is not None and cbg == False:
            return

        if (user.requestedFaction is 0 and unit == "Barracks") or (user.requestedFaction is 1 and unit == "Battlestump"):
            bcks = True
            base = world.getBaseForTeamID(user.teamId)
            barracksCap = base.getAttribute("Stats.Level")

            faction = world.getUserEntityForUser(user).getAttribute("Faction")
            barracksCount = teamAttr.get(("Units", faction, unit, "Count"))
            if barracksCount >= barracksCap:
                user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})
                return

        slots = world.queryPhysicalsByPoint(
            listToVector(pos),
            lambda p: p.entity.getAttribute("Subtype") == "Building slot" and
                      p.entity.getAttribute("Team") is user.teamId and
                      p.entity.getAttribute("Status") == "Open"
        )
        if len(slots) is 0:
            user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})
            return

        slot = findClosestEntity(listToVector(pos), map(lambda p: p.entity, slots))

        if not world.prefabExists(unit):
            user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})
            return

        teamEntity = world.getTeamEntityForUser(user)
        userEntity = world.getUserEntityForUser(user)
        faction = userEntity.getAttribute("Faction")
        gold = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Resources", "Gold"))
        cost = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Units", faction, unit, "Cost"))
        unlocked = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Units", faction, unit, "Unlocked"))
        levelReq = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Units", faction, unit, "Level requirement"))
        baseAttr = world.getBaseForTeamID(user.teamId).getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        hqLevel = baseAttr.get(("Stats", "Level"))
        if gold >= cost and cost and unlocked and hqLevel >= levelReq:
            workers = baseAttr.get("Workers")
            worker = None
            for w in workers:
                if w.getAttribute("Task") == "None":
                    worker = w
                    break
            if worker:
                user.match.networkRequestReply(user, seq_no, "RES", {"res": 1})
            else:
                user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})
                return
            if bcks:
                teamAttr.inc(("Units", faction, unit, "Count"), 1)
            teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(("Resources", "Gold"), -cost)
            slot.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set("Status", "Closed")
            increases = world.getGemIncreasesForUser(user, 1)
            building = world.createGameEntityForUser(
                unit,
                listToVector(pos),
                Vector3(0, -1, 0),
                user,
                (
                    ("Team", user.teamId),
                    ("Status", "Unbuilt"),   # will be set to building once the worker arrives
                ),
                increases
            )
            buildingFsm = building.getComponent(Enums.COMP_TYPE_FSM)
            if buildingFsm:
                buildingFsm.setState("Unbuilt")
            worker.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Build", building.id)
        else:
            user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})

    elif type == "Unlock":
        teamEntity = world.getTeamEntityForUser(user)
        userEntity = world.getUserEntityForUser(user)
        faction = userEntity.getAttribute("Faction")
        buildingTime = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Units", faction, unit, "Building time"))
        if buildingTime is None:
            resourceType = "Honor"
        else:
            resourceType = "Gold"
        resource = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Resources", resourceType))
        cost = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Units", faction, unit, "Unlock cost"))
        unlocked = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).get(("Units", faction, unit, "Unlocked"))
        if resource >= cost and cost and not unlocked:
            user.match.networkRequestReply(user, seq_no, "RES", {"res": 1})
            teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(("Resources", resourceType), -cost)
            teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).set(("Units", faction, unit, "Unlocked"), True)
        else:
            user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})

    elif type == "Advance tutorial":
        tutorial = world.getTutorialEntity()
        if tutorial is not None:
            eio = tutorial.getComponent( Enums.COMP_TYPE_EVENTIO )
            eio.receiveEvent( "Next step", None )


def entityMovementRequest(user, seq_no, id=-1, tpos=None, path=None, t=-1, **kwargs):
    if user.userType == "Observer":
        user.match.networkRequestReply(user, seq_no, "E_MOV_RES", {"res":0})
        return
    world = user.match.world
    e = world.getEntityByID(id)
    if e and e.getAttribute("Team") is user.teamId and e.getAttribute("Status") != "Charge" and e.getAttribute("Status") != "Dead":
        eventIO = e.getComponent(Enums.COMP_TYPE_EVENTIO)
        if path is not None:
            eventIO.receiveEvent("Move", [world.clipWorldPositionToMap(listToVector(wp)) for wp in path])
        else:
            eventIO.receiveEvent("Move", world.clipWorldPositionToMap(listToVector(tpos)))
        user.match.networkRequestReply(user, seq_no, "E_MOV_RES", {"res":1, "id":e.id})
    else:
        user.match.networkRequestReply(user, seq_no, "E_MOV_RES", {"res":0})


def entityStopRequest(user, seq_no, id=-1, t=-1, **kwargs):
    if user.userType == "Observer":
        user.match.networkRequestReply(user, seq_no, "E_STOP_RES", {"res":0})
        return
    world = user.match.world
    e = world.getEntityByID(id)
    if e and e.getAttribute("Team") is user.teamId and e.getAttribute("Status") != "Charge":
        eventIO = e.getComponent(Enums.COMP_TYPE_EVENTIO)
        eventIO.receiveEvent("Stop")
        user.match.networkRequestReply(user, seq_no, "E_STOP_RES", {"res":1, "id":e.id})
    else:
        user.match.networkRequestReply(user, seq_no, "E_STOP_RES", {"res":0})


def entityActionRequest(user, seq_no, id=-1, type=None, t=-1, **kwargs):
    if user.userType == "Observer":
        user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
        return
    world = user.match.world
    if type == "Collect":
        goldmine = world.getEntityByID(id)
        if goldmine and goldmine.getAttribute("Team") is user.teamId:
            goldmine.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Collect")
            world.getMatch().playerStatIncEvent( "gold_collected", user.username, goldmine.getAttribute( "Gold" ) )
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    elif type == "Target":
        unit = world.getEntityByID(id)
        eventIO = None
        if unit:
            eventIO = unit.getComponent(Enums.COMP_TYPE_EVENTIO)
        if eventIO and kwargs.has_key("tgt_id"):
            eventIO.receiveEvent("Target", kwargs["tgt_id"])
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    elif type == "Charge":
        hero = world.getEntityByID(id)
        if hero:
            attr = hero.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
        status = attr.get("Status")
        if status.split(" ")[0] == "Casting":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
        chargeLevel = attr.get(("Abilities", "Charge", "Level"))
        if chargeLevel is None:
            chargeLevel = 1
        if attr.get(("Abilities", "Charge", "Ready")) and chargeLevel > 0:
            casttime = attr.get("Abilities.Charge.Casting time")
            if casttime is None or casttime == 0.0:
                charge_type = attr.get( "Abilities.Charge.Type" )
                world.networkAbilityImmediateSuccess("Charge", hero)
                world.logInfo( "Immediate charge precast... charge_type=%s" % (charge_type,))

                if charge_type == "Alchemist mix":
                    # need bottles for alchemist mix
                    bottles = kwargs["bottles"]
                    world.logInfo( "Alchemist mixing: bottles %s  dir %s  all kwargs=%s" % (bottles, kwargs["dir"], str(kwargs) ) )
                    hero.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Charge", (listToVector(kwargs["dir"]).normalized(), clamp(kwargs["amount"], 0.0, 1.0), bottles))
                else:
                    hero.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Charge", (listToVector(kwargs["dir"]).normalized(), clamp(kwargs["amount"], 0.0, 1.0)))
            else:
                fsm = hero.getComponent(Enums.COMP_TYPE_FSM)
                timer = hero.getComponent(Enums.COMP_TYPE_TIMER)
                mover = hero.getComponent(Enums.COMP_TYPE_MOVER)
                waypointMover = hero.getComponent(Enums.COMP_TYPE_WAYPOINTMOVER)
                charge_type = attr.get( "Abilities.Charge.Type" )
                if waypointMover:
                    waypointMover.clearWaypoints()
                mover.stop()
                # set up timer to launch the ability properly
                attr.set("Status", "Casting Charge")
                fsm.setState("Casting")
                world.logInfo( "Charge precast... charge_type=%s" % (charge_type,))
                if charge_type == "Alchemist mix":
                    # need bottles for alchemist mix
                    bottles = kwargs["Bottles"]
                    world.logInfo( "Alchemist mixing: bottles %s  dir %s" % (bottles, kwargs[dir] ) )
                    timer.addTimer("Charge casting timer", "Charge", Enums.TIMER_ONCE, casttime, (listToVector(kwargs["dir"]).normalized(), clamp(kwargs["amount"], 0.0, 1.0)))
                else:
                    timer.addTimer("Charge casting timer", "Charge", Enums.TIMER_ONCE, casttime, (listToVector(kwargs["dir"]).normalized(), clamp(kwargs["amount"], 0.0, 1.0)))
                world.networkCommand(Enums.WORLD_EVENT_CAST_STARTED, ("Charge", casttime), hero)
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    elif type == "Ability":
        unit = world.getEntityByID(id)
        if unit and unit.getAttribute("Status") != "Dead":
            attr = unit.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            if kwargs.has_key("name"):
                name = kwargs["name"]
                if attr.get(("Abilities", name)) is None:
                    user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
                    return
                abilityLevel = attr.get(("Abilities", name, "Level"))
                if abilityLevel is None:
                    abilityLevel = 1
                if attr.get(("Abilities", name, "Ready")) and abilityLevel > 0:
                    try:
                        pos = kwargs["pos"]
                        pos = listToVector(pos)
                    except KeyError:
                        pos = None
                    try:
                        targetID = kwargs["tgt_id"]
                        if isinstance(targetID, str) or isinstance(targetID, unicode):
                            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
                            return
                    except KeyError:
                        targetID = None

                    unit.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Ability", (name, pos, targetID))
                else:
                    user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
                    return
            else:
                unit.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Berserk")
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    elif type == "Ability upgrade":
        unit = world.getEntityByID(id)
        if unit and unit.getAttribute(("Stats", "Skill points")) > 0 and kwargs.has_key("name"):
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            unit.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Ability upgrade", kwargs["name"])
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    elif type == "Upgrade":
        if user.userType != "Master":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
        e = world.getEntityByID(id)
        if e and e.getAttribute("Team") is user.teamId:
            eventIO = e.getComponent(Enums.COMP_TYPE_EVENTIO)
            eventIO.receiveEvent("Upgrade start")
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":1, "id":e.id})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
    elif type == "Repair":
        if user.userType != "Master":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            world.logInfo( "Will ignore repair request: requester is not Master user")
            return
        e = world.getEntityByID(id)
        if e and e.getAttribute("Team") is user.teamId:
            worker = world.getIdleWorkerForTeamID(user.teamId)
            if worker:
                user.match.networkRequestReply(user, seq_no, "RES", {"res": 1})
                eventIO = worker.getComponent(Enums.COMP_TYPE_EVENTIO)
                eventIO.receiveEvent("Repair", e.id )
                user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":1, "id":e.id})
            else:
                user.match.networkRequestReply(user, seq_no, "RES", {"res": 0})
                world.logInfo( "Will ignore repair request on team %d: no worker" % (user.teamId,))
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
    elif type == "Sell":
        if user.userType != "Master":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
        e = world.getEntityByID(id)
        if e and e.getAttribute("Team") is user.teamId:
            eventIO = e.getComponent(Enums.COMP_TYPE_EVENTIO)
            eventIO.receiveEvent("Sell")
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":1, "id":e.id})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
    elif type == "Rally":
        if user.userType != "Master":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
        e = world.getEntityByID(id)
        if e and e.getAttribute("Team") is user.teamId:
            eventIO = e.getComponent(Enums.COMP_TYPE_EVENTIO)
            eventIO.receiveEvent("Rally", listToVector(kwargs["pos"]))
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":1, "id":e.id})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
    elif type == "Enqueue unit":
        if user.userType != "Master":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
        unit = kwargs["unit"]
        barracks = world.getEntityByID(id)
        if barracks and barracks.getAttribute("Team") is user.teamId and world.prefabExists(unit) and unitQueueHasAvailableSlots(barracks.getAttribute("Unit queue")):
            teamEntity = world.getTeamEntityForUser(user)
            teamAttr = teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES)
            gold = teamAttr.get(("Resources", "Gold"))
            faction = barracks.getAttribute("Faction")
            cost = teamAttr.get(("Units", faction, unit, "Cost"))
            unlocked = teamAttr.get(("Units", faction, unit, "Unlocked"))
            levelReq = teamAttr.get(("Units", faction, unit, "Level requirement"))
            barracksLevel = barracks.getAttribute("Stats.Level")
            if gold < cost or unlocked is not True or barracksLevel < levelReq:
                user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
                return
            teamEntity.getComponent(Enums.COMP_TYPE_ATTRIBUTES).inc(("Resources", "Gold"), -cost)
            barracks.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Enqueue", unit)
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    elif type == "Clear slot":
        if user.userType != "Master":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
        barracks = world.getEntityByID(id)
        if barracks and barracks.getAttribute("Team") is user.teamId:
            barracks.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Clear slot", kwargs["slot"])
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    elif type == "Swap slots":
        if user.userType != "Master":
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res":0})
            return
        barracks = world.getEntityByID(id)
        if barracks and barracks.getAttribute("Team") is user.teamId:
            barracks.getComponent(Enums.COMP_TYPE_EVENTIO).receiveEvent("Swap slots", (kwargs["slot"], kwargs["slot_tgt"]))
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 1})
            return
        else:
            user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
            return
    else:
        user.match.networkRequestReply(user, seq_no, "E_ACT_RES", {"res": 0})
        return