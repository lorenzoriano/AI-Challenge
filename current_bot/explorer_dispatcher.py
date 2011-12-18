import explorer
import logging
import pezz_logging
import random
from math import sqrt
import castar
import itertools
import MyBot
ants = MyBot.ants

logger = logging.getLogger("pezzant.explorer_dispatcher")

class ExplorerDispatcher(object):
    """
    Creates Explorers if needed and keeps track of the food sources. 
    Allocates explorers on a grid. If the grid is full no more explorers are
    needed.
    """
    def __init__(self, world, bot):
	#TODO ant a location for each hill
        self.world = world
        self.food_tracking = {}
        self.allocated_food = set()
        self.bot = bot
        self.ants = []
        self.food_range = 2*int(sqrt(world.viewradius2)) + 1
        
        radius = self.food_range
        self.locations = set((r,c) for r in xrange(radius, world.rows, radius)
                                  for c in xrange(radius, world.cols, radius))
        #self.all_locations = locations
        self.available_locations = list(self.locations.copy())
        
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
        return float(len(self.available_locations)) /  (len(self.locations))

    def random_location(self, pos):
        """
        Generate a random location based on the previously equally spaced grid.
        If there are no available locations, a random one is generated.
        """
        if len(self.available_locations) == 0:
            self.log.info("Explorer to random location")
            r = random.randrange(0,self.world.rows)
            c = random.randrange(0,self.world.cols)
            while self.world.map[r,c] == ants.WATER:
                self.log.info("Location %s is water, trying again!", (r,c))
                r = random.randrange(0,self.world.rows)
                c = random.randrange(0,self.world.cols)
            ant_loc = (r,c)
        else: 
            
            def keyfun(loc):
                #return castar.pathlen(pos, loc)
                return self.world.distance(pos, loc)
            
            self.available_locations.sort(key=keyfun)
            ant_loc = self.available_locations.pop(0)

        return ant_loc

    def give_me_new_loc(self, ant):
        """
        Assign a new location to ant. The new location is chosen to be the
        closest to ant. Unseen locations are given priority.
        """
        #locs = itertools.ifilterfalse(self.world.cell_visible,
        #                              self.available_locations)

        if len(self.available_locations) == 0:
            self.log.info("No more locations!")
            return ant.area_loc
        
        locs = (loc for loc in self.available_locations 
                if not self.world.cell_visible(loc))

        def keyfun(loc):
            return self.world.distance(ant.pos, loc)

        try:
            newloc = min(locs, key=keyfun)
        except ValueError:
            #no more not visible locations
            self.log.info("No more invisible locatios",)
            
            return ant.area_loc

        self.available_locations.remove(newloc)
        if ant.area_loc is not None:
            self.available_locations.append(ant.area_loc)
        self.log.info("Assigning new location %s to ant %s",newloc, ant)

        return newloc

    def create_ant(self, loc):
        """
        Create an Explorer ant if needed.
        Returns the new ant if it has been created, None otherwise    
        """
        ant_loc = self.random_location(loc) 
        newant = explorer.Explorer(loc, self.bot, self.world, self,
                                  ant_loc, self.food_range)
        self.ants.append(newant)
        self.log.info("Creating new explorer %s with area %s", newant, ant_loc)
        return newant

    def remove_ant(self, ant):
        """
        Remove any reference to an ant when it dies
        """
        if type(ant) is explorer.Explorer:
            self.log.info("Removing ant %s", ant)
            self.ants.remove(ant)
            #popping back the ant location
            if ant.area_loc in self.locations:
                self.log.info("Re-adding locations %s", ant.area_loc)
                self.available_locations.append(ant.area_loc)
        
        #setting the food as available
        for k,v in self.food_tracking.copy().iteritems():
            if v == ant:
                del self.food_tracking[k]
                self.allocated_food.remove(k)
                break

    def check_food(self, loc):
        """
        Checks if the food at loc has already been reserved by
        another ant.
        """
        return loc in self.allocated_food
        #return self.food_tracking.has_key(loc)

    def reserve_food(self, loc, ant):
        """
        Make ant reserve food at location loc.
        Returns true if the food is reservable, false otherwise.
        """
        stealing = False
        preallocated = False
        if loc in self.allocated_food:
            preallocated = True
            owner = self.food_tracking[loc]
            d_ant = castar.pathlen(ant.pos, loc)
            d_owner = castar.pathlen(owner.pos, loc)
            if d_ant < d_owner:
                self.log.info("Removing food @ %s from %s", loc, owner)
                owner.remove_food()
                stealing = True

        if (not preallocated) or stealing:
            self.food_tracking[loc] = ant
            self.allocated_food.add(loc)
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
            self.allocated_food.remove(loc)
    
    def step(self):
        pass
