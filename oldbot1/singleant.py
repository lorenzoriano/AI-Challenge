import MyBot
ants = MyBot.ants
import castar
import logging
import pezz_logging
import heapq
import sys

logger = logging.getLogger("pezzant.singleant")
loglevel = logging.INFO
logger.setLevel(loglevel)
fh = logging.FileHandler("bot.txt", mode="w")
#fh = logging.StreamHandler(sys.stderr)
fh.setLevel(loglevel)
formatter = logging.Formatter(
                "%(levelname)s "
                "Turn: %(turn)d "
                "%(ant)s - "
                "%(funcName)s:"
                "%(lineno)s >> "
                "%(message)s"
                )
fh.setFormatter(formatter)
logger.addHandler(fh)


ant_ids = 0
class SingleAnt(object):
    """
    This is a generic ant.
    ant = SingleAnt(starting_location, bot, world)
    """
    def __init__(self, pos, bot, world, init_state):

        self.pos = pos
        self.bot = bot
        self.world = world
        self.plan_cache = {}
        self.plan_cache_age = 0
        self.max_cache_age = 10
        self.state = init_state
        
        global ant_ids
        self.id = ant_ids
        ant_ids += 1
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":self},
                self.bot
                )
    
    def transition(self, state):
        """
        Transition to state and immediate execution    
        """
        self.state = state
        self.log.info("Next state (immediate) %s", self.state)
        action = getattr(self, state)
        return action()

    def transition_delayed(self, state):
        """
        Transition to state Execution will be the next turn.    
        """
        self.state = state
        self.log.info("Next state (delayed) %s", self.state)
        return

    def step(self):
        """
        Execute the state the FSM is in
        """
        action = getattr(self, self.state)
        action()
       
    def move_heading(self, direction):
        """
        Move the ant towards a direction.
        A direction is in ['n','s','w','e']
        
        The ant moves if  the destination is unoccupied and no orders 
        have been isued to go to the same loc.

        Returns True if successfull, False otherwise.
        Also the bot gets the orders updated.
        """
        self.log.info("asking to move in direction %s", direction)

        world = self.world
        new_loc = world.destination(self.pos, direction)
        if (world.unoccupied(new_loc) and new_loc not in self.bot.orders):
            world.issue_order((self.pos, direction))
            #update the new position
            self.pos = new_loc
            self.bot.orders[new_loc] = self
            self.log.info("moving to %s", new_loc)
            return True
        else:
            self.log.warning("moving to %s not possible. Map is %d", 
                    new_loc, world.map[new_loc[0], new_loc[1]])
            return False
   
    def reset_cache(self):
        """
        Reset the plans cache and age    
        """
        self.plan_cache = {}
        self.plan_cache_age = 0

    def plan_to(self, loc):
        """
        Plans a path to loc. If a plan had already been found, use it.  
        Otherwise plan using astar. Returns the plan or an
        empty list if no plan was found.    
        """
        if loc == self.pos:
            self.log.info("goal %s is my location!", loc)
            self.reset_cache()
            return []

        if self.plan_cache_age > self.max_cache_age:
            self.log.info("plan cache too old, resetting")
            self.reset_cache()

        if loc in self.plan_cache:
            self.log.info("location %s already in cache", loc)
            self.plan_cache_age += 1
            return self.plan_cache[loc]

        #no plan in the cache, running A*
        self.log.info("planning to %s", loc)
        if loc is None:
            self.log.warning("attempting to move to None!")
            self.reset_cache()
            return []

        #wrapping with the world
        row, col = loc
        row = row % self.world.rows
        col = col % self.world.cols        
        loc = (row, col)

        path = castar.pathfind(self.pos, loc, self.bot, self.world)
        self.plan_cache = {loc:path}
        self.plan_cache_age = 0
        return path

    def move_to(self, loc):
        """
        Move the ant to loc. Uses self.plan_to to find a path.
        Returns True if successfull, False otherwise    
        """
        path = self.plan_to(loc)
        if len(path) == 0:
            self.log.info("There is no path!")
            self.reset_cache()
            return False
        
        next_loc = path.pop(0)
        self.log.info("Plan succeded, next location is %s", next_loc)
        direction = self.world.direction(self.pos, next_loc)
       
        if len(direction) == 0:
            self.log.error("Empty direction!")
            self.reset_cache()
            return False

        direction  = direction[0]
        res = self.move_heading(direction)
        if res:
            return True
        else:
            #something went wrong when moving
            self.reset_cache()
            return False
    
    def check_status(self):
        """
        Check if an ant exist at this location.
        """
        status = self.world.map[self.pos[0], self.pos[1]] == ants.MY_ANT
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
