import explorer
import logging
import pezz_logging
import random

logger = logging.getLogger("pezzant.explorer_dispatcher")

class ExplorerDispatcher(object):
    """
    Creates Explorers if needed and keeps track of the food sources. 
    Allocates explorers on a grid. If the grid is full no more explorers are
    needed.
    """
    def __init__(self, world, bot):
        self.world = world
        self.food_tracking = {}
        self.bot = bot
        self.ants = []
        self.food_range = 10
        
        self.locations = [(r,c) for r in xrange(0,world.rows,self.food_range)
                                  for c in xrange(0,world.cols,self.food_range)]
        #self.all_locations = locations
        self.available_locations = self.locations[:]
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"ExplorerDispatcher"},
                self.bot
                )
 
        self.log.info("Food range is %d", self.food_range)
    
    def spawn_likelyhood(self):
        """
        Returns the likelyhood that this spawner will want to create a new
        ant.
        """
        return float(len(self.available_locations)) /  (10+len(self.locations))


    def create_ant(self, loc):
        """
        Create an Explorer ant if needed.
        Returns the new ant if it has been created, None otherwise    
        """
        if len(self.available_locations) == 0:
            self.log.info("Explorer to random location")
            r = random.randrange(0,self.world.rows)
            c = random.randrange(0,self.world.cols)
            ant_loc = (r,c)
        else: 
            i = random.randrange(len(self.available_locations))
            ant_loc = self.available_locations.pop(i)

        newant = explorer.Explorer(loc, self.bot, self.world, self,
                                  ant_loc, self.food_range)
        self.ants.append(newant)
        self.log.info("Creating new explorer %s", newant)
        return newant

    def remove_ant(self, ant):
        """
        Remove any reference to an ant when it dies
        """
        if type(ant) is not explorer.Explorer:
            return
        
        self.log.info("Removing ant %s", ant)
        self.ants.remove(ant)
        
        #setting the food as available
        for k,v in self.food_tracking.iteritems():
            if v == ant:
                del self.food_tracking[k]
                break

        #popping back the ant location
        self.available_locations.append(ant.area_loc)

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
