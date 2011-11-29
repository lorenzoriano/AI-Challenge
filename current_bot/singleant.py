import MyBot
ants = MyBot.ants
import castar
import logging
import pezz_logging
import heapq
import sys
from fsm import FSM

logger = logging.getLogger("pezzant.singleant")

ant_ids = 0
class SingleAnt(FSM):
    """
    This is a generic ant. Every subclass will implement the state
    machine, i.e. the actual behaviour. The Ant keeps track of the 
    current state, and manages the movements.
    """
    def __init__(self, pos, bot, world, init_state):
        """

        Parameters:
        pos: the (row,col) initial location of the ant.
        bot: the bot object
        world: the Ant object
        init_state: a string representing the initial state. Usually 
                    provided by a subclass.
        """
        super(SingleAnt, self).__init__(init_state)
        self.pos = pos
        self.bot = bot
        self.world = world
        self.mover = bot.mover
        self.plan_cache = {}
        self.plan_cache_age = 0
        self.max_cache_age = 0
        self.current_heading = 'n'
        self.planner = castar

        global ant_ids
        self.id = ant_ids
        ant_ids += 1
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":self},
                self.bot
                )
    
    def move_immediate_pos(self, loc):
        """
        Move the ant towards to an adjacent square. 
        Warning: there is no check that loc is adjacent!
        
        The ant can move if the Mover says so. Note that the final
        movement will depend on the movements of all the ants. Check
        the Mover class for details.

        Returns True if successfull, False otherwise.
        """
        
        direction = self.world.direction(self.pos, loc)
        if len(direction) == 0:
            self.log.error("Empty direction!")
            self.reset_cache()
            return
        direction  = direction[0]
        self.current_heading = direction
        
        world = self.world
        if (self.mover.ask_to_move(self, loc)):
            return True
        else:
            self.log.warning("moving to %s not possible. Map is %d", 
                    loc, world.map_value(loc))
            return False
 
    def move_heading(self, direction):
        """
        Expands direction in one location and calls move_immediate_pos.
        
        Parameters:
        direction: one among 'n', 's', 'e', 'w'
    
        Return:
        True is success, False otherwise
        """
        self.log.info("moving towards heading %s", direction)
        loc = self.world.destination(self.pos, direction)
        return self.move_immediate_pos(loc)

    def movement_failure(self, loc):
        """
        The ant can't move to the desired location. There's nothing it
        can do now, it will not move. Subclasses might take action here
        (e.g. change state).
        
        Parameters:
        None
    
        Return:
        None
        """
        self.log.warning("Moving to %s failed", loc)

    def movement_success(self, loc):
        """
        Update the ant location and issue a movement order.
        """
        #remove the first element from the plan cache, we are
        #actiually moving!

        direction = self.world.direction(self.pos, loc)
        if len(direction) == 0:
            self.log.error("Empty direction when going to %s", loc)
            self.reset_cache()
            return 

        direction  = direction[0]
        
        #update the new position
        self.world.issue_order((self.pos, direction))
        self.log.info("moving to %s in direction %s", loc, direction)
        self.pos = loc

    def reset_cache(self):
        """
        Reset the plans cache and age    
        """
        self.plan_cache.clear()
        self.plan_cache_age = 0

    def __plan_to(self, loc):
        """
        Plans a path to loc. If a plan had already been found, use it.  
        Otherwise plan using astar. Returns the plan or an
        empty list if no plan was found.    
        """
        if loc is None:
            self.log.warning("attempting to move to None!")
            self.reset_cache()
            return []
        
        if loc == self.pos:
            self.log.info("goal %s is my location!", loc)
            return []

        if self.plan_cache_age >= self.max_cache_age:
            self.log.info("plan cache too old, resetting")
            self.reset_cache()

        if loc in self.plan_cache:
            plan = self.plan_cache[loc]
            try:
                #checking if my pos is in the cache
                i = plan.index(self.pos)
            except ValueError:
                i = -1;
            if i < 0:
                self.log.info("My pos is not in the plan %s", plan)
            else:
                self.log.info("location %s already in cache", loc)
                self.plan_cache_age += 1
                #return the path from the next position on
                return plan[i+1:]

        #no plan in the cache, running A*
        self.log.info("planning to %s", loc)

        path = self.planner.pathfind(self.pos, loc, self.bot, self.world)
        self.plan_cache[loc] = path
        self.plan_cache_age = 0
        return path

    def move_to(self, loc):
        """
        Move the ant to loc. Uses self.plan_to to find a path.
        Returns True if successfull, False otherwise    
        """
        loc = self.world.wrap_coords(loc)
        path = self.__plan_to(loc)
        if len(path) == 0:
            self.log.info("There is no path!")
            return False
        
        next_loc = path[0]
        self.log.info("Plan succeded, next location is %s", next_loc)
       
        res = self.move_immediate_pos(next_loc)
        if res:
            return True
        else:
            #something went wrong when moving, probably the plan is wrong!
            self.reset_cache()
            return False
    
    def check_status(self):
        """
        Check if an ant exist at this location.
        """
        status = self.world.map_value(self.pos) == ants.MY_ANT
        if not status:
            self.log.info("I am dead or lost!")
            return False
        else:
            return True

    def __repr__(self):
        return (self.__class__.__name__ +
                "(" +
                str(self.id) + 
                ") @ " + 
                str(self.pos)
                )
    def food_in_range(self, r):
        """
        Returns an ordered list of (dist, location) of all the food 
        locations whose distance is <= r
        """
        world = self.world
        food = []
        for f in world.food():
            d = world.distance(self.pos, f)
            if d <= r:
                heapq.heappush(food, (d,f) )

        return food

    def enemy_in_range(self, r):
        """
        Returns True if an enemy is less than r distant from the ant.
        """

        world = self.world
        for e in world.enemy_ants():
            d = world.distance(self.pos, e[0])
            if d <= r:
                self.log.info("Enemy %s in range, distance: %s",e[0],d)
                return True
        return False
    
    def enemies_in_range(self, r):
        """
        Returns an ordered list of (dist, location) of all the enemy 
        locations whose distance is <= r
        """

        world = self.world

        enemies = []
        for e in world.enemy_ants():
            d = world.distance(self.pos, e[0])
            if d <= r:
                heapq.heappush(enemies,(d,e[0]) )

        return enemies
    
    def unseen_locations(self, r=1000):
        """
        Returns a NON-ordered list of (dist, location) of all the enemy 
        locations whose distance is <= r
        """

        world = self.world

        unseen_locs = []
        for loc in self.bot.unseen:
            d = world.distance(self.pos, loc)
            if d <= r:
                unseen_locs.append((d,loc) )

        return unseen_locs

    def my_hills(self, r=1000):
        """
        Returns a NON-ordered list of (dist, location) of all the enemy 
        locations whose distance is <= r
        """

        world = self.world

        my_hills = []
        for loc in self.world.my_hills():
            d = world.distance(self.pos, loc)
            if d <= r:
                my_hills.append((d,loc) )

        return my_hills
