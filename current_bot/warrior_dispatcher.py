import warrior
import logging
import pezz_logging
import math

logger = logging.getLogger("pezzant.warrior_dispatcher")

class WarriorDispatcher(object):
    """
    Creates Warriors. 
    """
    def __init__(self, world, bot):
        self.world = world
        self.bot = bot
        self.ants = []
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"WarriorDispatcher"},
                self.bot
                )
    
    def spawn_likelyhood(self):
        """
        Returns the likelyhood that this spawner will want to create a new
        ant. The more enemy hills are around, the more it will want to spawn
        a warrior.
        """
        number_of_enemies = len(self.world.enemy_ants())
        self.log.info("Number of enemy_ants: %d", number_of_enemies)
        visible = self.world.visible
        visible_perc = float(visible.sum()) / visible.size
        self.log.info("World visible is %f", visible_perc)
        
        estimated_enemies = (number_of_enemies + 
                (1. - visible_perc) * number_of_enemies/visible_perc)
        self.log.info("Estimated enemies: %f", estimated_enemies)
        if visible_perc < 0.3:
            return 0.00
        if len(self.bot.ants) > estimated_enemies*(len(self.ants)+1):
            self.log.info("OK to make a Warrior")
            return 1.0
        else:
            return 0.00

    def create_ant(self, loc):
        """
        Create a Warrior ant if needed.
        Returns the new ant if it has been created, None otherwise    
        """
       
        newant = warrior.Warrior(loc, self.bot, self.world, self,
                                   )
        self.ants.append(newant)
        self.log.info("Creating new warrior %s", newant)
        return newant

    def remove_ant(self, ant):
        """
        Remove any reference to an ant when it dies
        """
        if type(ant) is not warrior.Warrior:
            return
        
        self.log.info("Removing ant %s", ant)
        self.ants.remove(ant)

    def step(self):
        pass
