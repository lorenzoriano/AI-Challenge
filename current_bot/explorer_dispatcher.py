import explorer
import logging
import pezz_logging
import random
from math import sqrt
import castar
import itertools
import MyBot
ants = MyBot.ants
import numpy as np
import c_pos_allocator as pos_allocator

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
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"ExplorerDispatcher"},
                self.bot
                )
 
        self.log.info("Food range is %d", self.food_range)
       
        self.availability_map = None
        self.mask = np.ones(self.world.map.shape, 
                dtype=np.int8, order="C")
        self.masked_availability = None
    
    def spawn_likelyhood(self):
        """
        Returns the likelyhood that this spawner will want to create a new
        ant.
        """
        return 0.1

    def random_location(self):
        """
        Generate a random location.
        """
        r = random.randrange(0,self.world.rows)
        c = random.randrange(0,self.world.cols)
        while self.world.map[r,c] == ants.WATER:
            self.log.info("Location %s is water, trying again!", (r,c))
            r = random.randrange(0,self.world.rows)
            c = random.randrange(0,self.world.cols)

        return r,c

    def give_me_new_loc(self, ant):
        """
        Assign a new location to ant. The new location is chosen to be the
        closest unmarked to ant.
        """
        newloc = self.find_available_pos(ant.pos)
        if newloc is None:
            self.log.warning("Sorry %s, couldn't find a new pos for you", ant)
            return ant.area_loc
        else:
            self.log.info("New area @ %s for ant %s", newloc, ant)
            pos = ant.area_loc
            pos_allocator.add_to_mask(self.mask,
                                       pos[0], pos[1],
                                       self.world.viewradius2
                                     )
            pos_allocator.add_to_mask(self.masked_availability,
                                       pos[0], pos[1],
                                       self.world.viewradius2
                                     )

            return newloc

    def create_ant(self, loc):
        """
        Create an Explorer ant if needed.
        Returns the new ant if it has been created, None otherwise    
        """
        ant_loc = self.find_available_pos(loc) 
        if ant_loc is None:
            ant_loc = self.random_location()
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
            
            #popping back the ant area
            pos = ant.area_loc
            pos_allocator.add_to_mask(self.mask,
                                       pos[0], pos[1],
                                       self.world.viewradius2
                                     )
        
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
        self.availability_map = np.logical_not(self.world.visible).astype(np.int8)
        enemy_poses = [e[0] for e in self.world.enemy_ants()]
        if len(enemy_poses):
            pos_allocator.create_availability_map(self.availability_map,
                    np.array(enemy_poses, dtype=np.int, order="C"),
                    self.world.viewradius2
                    )
        
        self.masked_availability = np.logical_and(self.availability_map,
                                    self.mask).astype(np.int8)

    def find_available_pos(self, pos):
        newpos = pos_allocator.closest_pos(self.masked_availability,
                self.world.map,
                pos[0], pos[1],
                )
        if newpos == (-1, -1):
            self.log.warning("Couldn't find a suitable location for %s", pos)
            return None

        #newpos is not longer available
        pos_allocator.remove_from_mask(self.masked_availability,
                                   newpos[0], newpos[1],
                                   self.world.viewradius2
                                 )
        pos_allocator.remove_from_mask(self.mask,
                                   newpos[0], newpos[1],
                                   self.world.viewradius2
                                 )
        return newpos
