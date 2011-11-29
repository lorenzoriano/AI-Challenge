import defender
import logging
import pezz_logging

logger = logging.getLogger("pezzant.defender_dispatcher")

class DefenderDispatcher(object):
    """
    Creates Defenders
    """
    def __init__(self, world, bot):
        self.world = world
        self.bot = bot
        self.ants = []
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"DefenderDispatcher"},
                self.bot
                )
        self.assigned_hills = set()
 
    def spawn_likelyhood(self):
        """
        Returns the likelyhood that this spawner will want to create a new
        ant. 
        
        If all the hills have a defender associated then no ant will be created.
        If the number of ants is less than 2*number of hills, then no ant
        will be created.
        Otherwise return a high likelyhood.
        """
        return 0.
        hills_to_assign = set(self.world.my_hills()).difference(
                self.assigned_hills)
        self.log.info("hills to assign: %s", hills_to_assign)
        if len(hills_to_assign) == 0:
            return 0.
        elif len(self.bot.ants) < 2*len(self.world.my_hills()):
            return 0.
        else:
            return 1.        
        
    def create_ant(self, loc):
        """
        Create a Warrior ant if needed.
        Returns the new ant if it has been created, None otherwise    
        """
       
        newant = defender.Defender(loc, self.bot, self.world, self,
                                  )
        self.ants.append(newant)
        self.log.info("Creating new defender %s", newant)
        self.assigned_hills.add(newant.myhill)
            
        return newant

    def remove_ant(self, ant):
        """
        Remove any reference to an ant when it dies
        """
        if type(ant) is not defender.Defender:
            return
        self.assigned_hills.remove(ant.myhill)
        self.log.info("Removing ant %s", ant)
        self.ants.remove(ant)
