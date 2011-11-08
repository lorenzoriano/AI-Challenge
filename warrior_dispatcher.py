import warrior
import logging
import pezz_logging
import random
import sys

logger = logging.getLogger("pezzant.warrior_dispatcher")
loglevel = logging.INFO
logger.setLevel(loglevel)
fh = logging.FileHandler("bot.txt", mode="w")
#fh = logging.StreamHandler(sys.stderr)
fh.setLevel(loglevel)
formatter = logging.Formatter(
                "%(levelname)s "
                "Turn: %(turn)d "
                "ExplorerDispatcher - "
                "%(funcName)s:"
                "%(lineno)s >> "
                "%(message)s"
                )
fh.setFormatter(formatter)
logger.addHandler(fh)


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
