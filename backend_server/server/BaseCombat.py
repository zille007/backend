class Actor:
    def gainedEffect( self, effect ):
        self.actionList.append( CombatAction( effect.currentTick, "GAINED_EFFECT", self, effect.identifier ) )

    def expiredEffect( self, effect ):
        self.actionList.append( CombatAction( effect.currentTick, "EXPIRED_EFFECT", self, effect.identifier ) )

    def tickEffect( self, effect ):
        self.actionList.append( CombatAction( effect.currentTick, "EFFECT_ACTION", self, effect.identifier ) ) 
    
    def act(self, combatState):
        # should modify action list appropriately here
        self.actionList.append( CombatAction( self.currentTick, "ABSTRACT_ACTION", self, "" ) )
        return self.ticksUntilNextAction + self.baseActionDelay

    def tick( self, count, combatState ):
        # can't have zero delays or we'll end up in an infinite loop
        self.actionList = []
        assert( self.baseActionDelay > 0 )
        
        # run effects first
        res = [effect for effect in self.activeEffects if effect.tick(count) == False]
        self.activeEffects = res

        self.ticksUntilNextAction -= count
        while( self.ticksUntilNextAction <= 0 ):
            self.currentTick = combatState.currentTick + self.ticksUntilNextAction
            self.ticksUntilNextAction = self.act( combatState )

        return self.actionList

    def assignGroup( self, group ):
        self.combatGroup = group

    def __init__(self, identifier, baseStats, activeEffects = [] ):
        self.baseStats = baseStats
        self.effectiveStats = self.baseStats
        self.activeEffects = activeEffects
        self.baseActionDelay = 1   # should be calculated
        self.currentTick = 0
        self.ticksUntilNextAction = self.baseActionDelay
        self.identifier = identifier
        self.combatGroup = ""
        self.actionList = []

class MonsterActor( Actor ):
    def __init__(self):
        Actor.__init__(self)

class HeroActor( Actor ):
    def __init__(self):
        Actor.__init__(self)


class CombatAction:
    def __repr__(self):
        return "(%s on tick %d)" % (self.actionIdentifier, self.combatTick)
    
    def __init__(self, tick, identifier, actor, data ):
        self.combatTick = tick
        self.actionIdentifier = identifier
        self.actor = actor
        self.data = data
        self.resultList = []


class Effect:
    def grant(self, actor):
        if actor is not None:
            actor.gainedEffect( self )
        self.target = actor

    def expire(self):
        if self.target is not None:
            self.target.expiredEffect( self )
            
        self.expiryTick = self.currentTick
        return True

    def tickEffect( self ):
        if self.target is not None:
            self.target.effectTick( self )

    def preTick( self ):
        return True

    def postTick( self ):
        return True

    def tick(self, count = 1):
        """
        Passes time on the effect for count ticks.

        Return true if the effect expired, false otherwise.
        """
        while( self.currentTick + effectDelay <= self.currentTick + count ):
            self.currentTick += effectDelay
            shouldExpire = self.preTick()

            if( shouldExpire == False ):

                self.tickEffect()
                
                if( self.currentTick == self.endTick ):
                    shouldExpire = True
                else:
                    shouldExpire = self.postTick()

        if( shouldExpire ):
            return self.expire()
        
        return False
        
    def maxDuration(self):
        return self.endTick - self.currentTick

    def hasExpired(self):
        return (self.currentTick != -1 and self.expiryTick != -1)

    def start(self, currentTick):
        self.currentTick = currentTick
        self.grant( self.target )
    
    def __init__(self):
        self.target = None     # must be an actor if set
        self.identifier = ""

        self.currentTick = -1
        self.startTick = 0
        self.endTick = 0
        self.effectDelay = 1
        self.expiryTick = -1
        self.stacks = 1


class Damage:
    # This might be a bit of a misnomer: a typical attack or ability use
    # does result in damage, but this class encapsulates other attack
    # results as well, such as misses, blocks and evades.
    def __init__(self):
        pass


class Combat:
    def addGroup( self, group ):
        if self.groups.has_key( group ):
            return

        self.groups[group] = set( [] )
    
    def addActor( self, actor, group ):
        assert( isinstance( actor, Actor ) )
        assert( actor not in self.allActors )

        self.allActors.append( actor )

        if( group not in self.groups.keys() ):
            self.addGroup( group )

        self.groups[group].add( actor )

    def removeActorFromGroup( self, actor, group ):
        assert( isinstace( actor, Actor ) )
        assert( actor in self.allActors )
        assert( group in self.groups.keys() )
        assert( actor in self.groups[group] )

        self.groups[group].remove( actor )

    def recalculateTimeline( self ):
        pass

    def tick( self, count = 1 ):
        self.currentTick += count 
        target = self.currentTick + count
        results = [actor.tick( count, self ) for actor in self.allActors]
        self.recalculateTimeline()

        self.currentTick += count
        self.totalTicks += count
        return results

    def hasEnded( self ):
        if( self.totalTicks >= self.maxTicks ):
            return True
        
        nonempty_groups = 0

        for k in self.groups.keys():
            group = self.groups[k]
            nonempty_groups += 1 if len(group) == 0 else 0

        return True if nonempty_groups == 1 else False
        

    def __init__(self):
        self.currentTick = 0
        self.totalTicks = 0
        self.groups = {}
        self.allActors = []
        self.timeline = []
        self.completedActions = []
        self.nextActionTick = -1
        self.maxTicks = 10000
        pass
    
if __name__ == "__main__":
    c = Combat()
    a = Actor( "TEST", {} )
    c.addActor( a, "player" )
    print c.tick( 10 )
