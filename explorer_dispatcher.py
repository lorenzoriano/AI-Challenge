import explorer
import logging
import pezz_logging

logger = logging.getLogger("pezzant.explorer_dispatcher")
loglevel = logging.INFO
logger.setLevel(loglevel)
fh = logging.FileHandler("bot.txt", mode="w")
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



class ExplorerDispatcher(object):
    """
    Creates Explorers if needed and keeps track of the food sources.
    """
    def __init__(self, world, bot):
        self.world = world
        self.food_tracking = {}
        self.bot = bot
        self.ants = []
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":self},
                self.bot
                )
 
    def create_ant(self, loc):
        """
        Create an Explorer ant if needed.
        Returns the new ant if it has been created, None otherwise    
        """
        newant = explorer.Explorer(loc, self.bot, self.world, self)
        self.ants.append(newant)
        self.log.info("Creating new ant %s", newant)
        return newant

    def remove_ant(self, ant):
        """
        Remove any reference to an ant when it dies
        """
        self.log.info("Removing ant %s", ant)
        try:
            self.ants.remove(ant)
        except ValueError:
            pass

        loc = [k 
                for k, v in self.food_tracking.iteritems() 
                if v == ant]
        if len(loc):
            del self.food_tracking[loc[0]]

    def check_food(self, loc):
        """
        Checks if the food at loc has already been reserved by
        another ant.
        """
        return self.food_tracking.has_key(loc)

    def reserve_food(self, loc, ant):
        """
        Make ant reserve food at location loc.
        Returns true if the food is reservable, false otherwise.
        """
        if not self.check_food(loc):
            self.food_tracking[loc] = ant
            self.log.info("Reserving food @ %s for ant %s", loc, ant)
            return True
        else:
            return False

    def free_food(self, loc):
        """
        Removes loc from the trakced food    
        """
        if self.food_tracking.has_key(loc):
            self.log.info("Removing food @ %s", loc)
            del self.food_tracking[loc]
