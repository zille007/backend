import Enums
from euclid import Vector3

def tutorialAdvanceToStep( entity, world, step ):
    attr = entity.getAttributes()

    step_type = attr.get( "Steps.%s.Type" % (step,))
    next_step = attr.get( "Steps.%s.Next" % (step,))

    attr.set( "Current step", step )
    attr.set( "Next step", next_step )

    #world.logInfo( "Tutorial advancing to step %s (type=%s, next step: %s)" % (step, step_type, next_step))

    position = None
    tgt_id = -1

    if step_type == "Message":
        text = attr.get( "Steps.%s.Text" % (step,) )
        space = attr.get( "Steps.%s.Space" %  (step,) )

        if space == "World":
            position = list( attr.get( "Steps.%s.Position" %  (step,) ) )

        if space == "World slot":
            space = "World"
            slots = world.getBuildingSlotsForTeamID( 1 )
            index = attr.get( "Steps.%s.Slot index" % (step,) )
            position = list( slots[index].getPosition() )

        if space == "UI":
            position = attr.get( "Steps.%s.Position anchor" % (step,) )

        if space == "Entity":
            reqent = attr.get( "Steps.%s.Entity" % (step,) )
            reqteam = attr.get( "Steps.%s.Entity team" % (step,) )

            ents = []
            if reqteam is None:
                ents = [e for e in world.getEntities() if e.getAttribute("Subtype") == reqent]
            else:
                ents = [e for e in world.getEntities() if e.getAttribute("Subtype") == reqent and e.getAttribute( "Team") == reqteam]

            if len(ents) > 0:
                position = ents[0].id
                #world.logInfo( "Tutorial message in space entity with position id %d" % (position,) )
                if reqent == "Victory point":
                    # must do it like this because Entity space requires an ID but the client has no
                    # entity IDs for victory points...
                    space = "World"
                    position = list( ents[0].getPosition() )
                    tgt_id = ents[0].id
                    pass

        if space == "None":
            pass

        clear_cond = attr.get( "Steps.%s.Clear condition" % (step,) )
        clear_flag = attr.get( "Steps.%s.Clear" % (step,) )

        control_flag = attr.get( "Steps.%s.Control flag" % (step, ) )
        menu_flag = attr.get( "Steps.%s.Menu flag" % (step, ))

        clear_extra_arguments = { "control_flag":control_flag if control_flag is not None else True,
                                  "menu_flag":menu_flag if control_flag is not None else True }

        clear_target = attr.get( "Steps.%s.Clear target" % (step,))
        if clear_target is not None:
            if clear_target == "Goldmine":
                goldmines = [b for b in world.getEntities() if b.getAttribute("Subtype") == "Goldmine"]
                if len( goldmines ) > 0:
                    tgt_id = goldmines[0].id
            elif clear_target == "Barracks":
                barracks = [b for b in world.getEntities() if b.getAttribute("Subtype") == "Barracks"]
                if len( barracks ) > 0:
                    tgt_id = barracks[0].id
            elif clear_target == "Townhall":
                th = world.getBaseForTeamID( 1 )
                tgt_id = th.id

        if clear_cond in ( "Collect gold", "Upgrade", "Capture" ):
            clear_extra_arguments["clear_id"] = tgt_id
            #world.logInfo( "Clear condition for tutorial is %s with target id %d" % (clear_cond, tgt_id))
            if clear_cond == "Capture":
                team = world.getTeamEntity( 1 )
                ta = team.getAttributes()
                ta.set( "Control toggles.Can capture", True )

        if clear_cond in ( "Upgrade ability" ):
            abls = ( "Charge", "Rage", "Hero heal", "Summon" )
            phero = world.getHeroesForTeam( 1 )[0]
            if phero is None:
                for a in abls:
                    lvl = phero.getAttribute( "Abilities.%s.Level" % (a,))
                    if lvl is not None and lvl > 1:
                        clear_cond = "Immediate"

        if clear_cond in ( "Build to" ):
            clear_extra_arguments["clear_building"] = clear_target

            if clear_target == "Barracks":
                team = world.getTeamEntity( 1 )
                ta = team.getAttributes()
                ta.set( "Control toggles.Can build Barracks", True )
                ta.set( "Control toggles.Can build Garrison", False )

            if clear_target == "Garrison":
                team = world.getTeamEntity( 1 )
                ta = team.getAttributes()
                ta.set( "Control toggles.Can build Barracks", False )
                ta.set( "Control toggles.Can build Garrison", True )

            world.getBuildingSlotsForTeamID( 1 )

        if clear_cond in ( "Add units" ):
            clear_extra_arguments["clear_id"] = tgt_id
            clear_extra_arguments["clear_count"] = int( attr.get( "Steps.%s.Clear count" % (step,)) )
            team = world.getTeamEntity( 1 )
            ta = team.getAttributes()
            ta.set( "Control toggles.Can build Barracks", True )
            ta.set( "Control toggles.Can build Garrison", True )

        if clear_cond in ( "Destroy units" ):
            clear_extra_arguments["clear_units"] = list( attr.get( "Spawned units") )
            #world.logInfo( "Clear condition: destroy units. Unit list = %s" % (str( list( attr.get( "Spawned units" ) ) ) ) )


        world.networkCommand( Enums.WORLD_EVENT_TUTORIAL_MESSAGE, (text,space,position,clear_cond,clear_flag, clear_extra_arguments), entity )
    elif step_type == "UI":
        state = attr.get( "Steps.%s.State" % (step,) )
        multistates = attr.get( "Steps.%s.Elements" % (step,) )
        if multistates is None:
            state = attr.get( "Steps.%s.Element" % (step,))
            multistates = [state]

        for elem in multistates:
            ui_element = elem
            world.networkCommand( Enums.WORLD_EVENT_TUTORIAL_UI, (ui_element, state), entity )

        tutorialAdvanceToStep( entity, world, next_step )

    elif step_type == "Spawn":
        offset = 1.0
        rp_locals = [ Vector3( offset, 0, 0 ), Vector3( -offset, 0, 0 ), Vector3( 0, offset, 0 ), Vector3( 0, -offset, 0 ),
                      Vector3( offset * 1.25, -offset * 1.25, 0 ), Vector3( -offset * 1.25, -offset * 1.25, 0 ),
                      Vector3( offset * 1.25, offset * 1.25, 0), Vector3( -offset * 1.25, offset * 1.25, 0 ) ]

        unit_list = attr.get( "Steps.%s.Units" % (step,) )
        pos = attr.get( "Steps.%s.Position" % (step,) )

        tutuser = world.getUserForUnit( world.getHeroesForTeam(2)[0] )

        i = 0
        id_list = []
        for u_name in unit_list:
            unit = world.createGameEntityForUser(
                u_name,
                pos + rp_locals[i],
                Vector3(1, 0, 0),
                tutuser,
                (
                    ("Damage minimum", 5),
                    ("Damage maximum", 7),
                    ("Hitpoints", 100),
                    ("Hitpoints maximum", 100),
                    ("Attack period", 1.5),

                    ("Speed", 2.0),
                    ("Team", 2),
                    ("Rally point", pos + rp_locals[i]),
                )
            )
            if unit is None:
                world.logInfo( "Tutorial trying to spawn unit but couldn't???")
            i += 1
            id_list.append( unit.id )

        attr.set( "Spawned units", id_list )

        tutorialAdvanceToStep( entity, world, next_step )

    elif step_type == "Create AI":
        tuthero = world.getHeroesForTeam( 2 )
        if len(tuthero) == 1:
            tuthero[0].getComponent( Enums.COMP_TYPE_MOVER ).teleport( world.teamBaseLocations[2].copy() )

        world.addAI( "easy", world.getUserForUnit(tuthero[0]), 2 )
        team = world.getTeamEntity( 1 )
        oppo = world.getTeamEntity( 2 )

        oppo_a = oppo.getAttributes()
        ta = team.getAttributes()
        ta.set( "Resources.Tickets minimum", -1 )
        oppo_a.set( "Resource.Tickets minimum", -1 )

        tutorialAdvanceToStep( entity, world, next_step )

    elif step_type == "Start waves":
        match = world.getMatchEntity()
        ma = match.getAttributes()
        ma.set( "Wave timer active", True )
        ma.set( "Wave timer counter", 5 )
        tutorialAdvanceToStep( entity, world, next_step )

    elif step_type == "Level up":
        phero = world.getHeroesForTeam( 1 )[0]
        if phero is not None:
            ha = phero.getAttributes()
            if ha.get( "Stats.Level") < 2:
                phero.getComponent( Enums.COMP_TYPE_EVENTIO ).receiveEvent( "Level up" )
        tutorialAdvanceToStep( entity, world, next_step )


def tutorialNextStep( entity, world, args ):
    attr = entity.getAttributes()
    next_step = attr.get( "Next step" )

    if next_step != "END":
        tutorialAdvanceToStep( entity, world, next_step )
    else:
        world.networkCommand( Enums.WORLD_EVENT_TUTORIAL_END, None, entity )

def tutorialIdleUpdate( entity, world, args ):

    attr = entity.getAttributes()
    current_step = attr.get( "Current step" )
    if current_step == "":
        # do some adjustments on our team attributes for the tutorial...
        team = world.getTeamEntity( 1 )
        oppo = world.getTeamEntity( 2 )

        oppo_a = oppo.getAttributes()
        ta = team.getAttributes()
        ta.set( "Resources.Gold", 1000 )
        ta.set( "Resources.Tickets minimum", 200 )
        oppo_a.set( "Resource.Tickets minimum", 200 )

        ta.set( "Units.Northerners.Barracks.Building time", 1.0 )
        ta.set( "Units.Northerners.Garrison.Building time", 1.0 )
        ta.set( "Units.None.Goldmine.Upgrade time", 1.0 )
        ta.set( "Units.Northerners.Barracks.Upgrade time", 1.0 )
        ta.set( "Units.Northerners.Townhall.Upgrade time", 1.0 )
        ta.set( "Units.None.Goldmine.Upgrade time", 1.0 )

        ta.set( "Control toggles.Can capture", False )
        ta.set( "Control toggles.Can lose tickets", False )
        ta.set( "Control toggles.Can build", False )
        ta.set( "Control toggles.Can move heroes", True )
        ta.set( "Control toggles.Can build Barracks", False )
        ta.set( "Control toggles.Can build Garrison", False )

        match = world.getMatchEntity()
        ma = match.getAttributes()
        ma.set( "Wave timer active", False )

        tuthero = world.getHeroesForTeam( 2 )
        if len(tuthero) == 1:
            tuthero[0].getComponent( Enums.COMP_TYPE_MOVER ).teleport( Vector3( 9000.0, 9000.0, 0.0 ) )

        tutorialAdvanceToStep( entity, world, attr.get( "Initial step") )


