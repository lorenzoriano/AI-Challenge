import MyBot
ants = MyBot.ants
import singleant
import random
#import ants
import explorers_flock 
import defenders_flock
from math import sqrt
import drawcircle
import itertools

class Explorer(singleant.SingleAnt):
    """
    The Explorer ant.

    This ant will move to random locations and it will head for food
    if it sees any. It will head away from enemies
    """
    def __init__(self, loc, bot, world, dispatcher,
                area_loc, food_range = 15):
        
        super(Explorer, self).__init__(loc, bot, world, "explore_state")
        
        self.goal_pos = None
        self.danger_radius = 3 + int(sqrt(world.attackradius2))
        #self.danger_radius = 1.5 * world.attackradius2
        self.dispatcher = dispatcher
        self.area_loc = area_loc
        self.food_gather_range = food_range
        self.map = world.map
        self.food = None
        self.enemies = None
        self.free = True
        self.gathering_radius = 8

    def generate_random_goal(self):
        """
        Generate a new random location around the assigned area.
        If it can't find a suitable location within 10 trials, go to completely
        random location.
        """
        r = self.food_gather_range
        area_loc = self.area_loc

        row = random.randint(area_loc[0]-r, area_loc[0]+r)
        col = random.randint(area_loc[1]-r, area_loc[1]+r)
        newpos = self.world.wrap_coords((row,col))
        
        self.log.info("random movement to %s", newpos)
        return  newpos

    def check_reserve_food(self):
        """
        Returns a food loc if it finds a reachable and reservable food,
        False otherwise.
        """        
        food = self.food_in_range(self.food_gather_range)
        for f in food:
            loc = f[1]
            if self.dispatcher.reserve_food(loc, self):
                self.food = loc
                self.log.info("Reserving food at %s", loc)
                return True
        return False

    def command_food(self, loc):
        """
        This ant will be commanded to gather food at loc.
        State will change accordingly. 
        If the ant is not free it will return False, True otherwise.
        """
        if not self.free:
            return False
        if self.dispatcher.reserve_food(loc, self):
            self.food = loc
            self.log.info("Commanding food at %s", loc)
            self.transition_delayed("forage_state")
            return True
        else:
            self.log.error("First I get commanded for %s, then I can't???", loc)
            return False
    	

    def check_if_run(self, enemy_loc, food_loc=None):
        """
        An ant will run from an enemy unless it's close to its hill or if food
        is closer.
        """
        world = self.world
        mypos = self.pos
        if food_loc is None:
            return True
        if world.distance(mypos, food_loc) < world.distance(mypos,enemy_loc):
            return False
        return True

    def explore_state(self):
        """
        Generate a random goal then transition to move_to_goal.
        If it sees an enemy or food then transition accordingly.
        """
        self.free = True
        #checking for enemies
        if len(self.enemies):
            if self.check_if_run(self.enemies[0][1]):
                return self.transition("escape_state")

        #checking for food
        if self.check_reserve_food():
            return self.transition("forage_state")

        #generating a random goal
        self.goal_pos = self.generate_random_goal()
        return self.transition("moving_state")

    def moving_state(self):
        """
        Move towards self.goal_pos if no enemies or food. 
        Transition to explore_state if goal reached
        """
        self.free = True
        #checking for enemies
        if len(self.enemies):
            if self.check_if_run(self.enemies[0][1]):
                return self.transition("escape_state")

        #checking for food
        if self.check_reserve_food():
            return self.transition("forage_state")

        if self.pos == self.goal_pos:
            self.log.info("Goal reached")
            return self.transition("explore_state")

        if not self.move_to(self.goal_pos):
            return self.transition("move_random_state")
    
    def move_random_state(self):
        """
        Move to a random direction, then transition to explore.
        """
        self.free = True
        directions = ['n','s','w','e']
        random.shuffle(directions)

        for d in directions:
            if self.move_heading(d):
                break

        return self.transition_delayed("explore_state")

    def forage_state(self):
        """
        Move towards food. Transition to enemy. Transition to explore
        if the food has been reached or if it doesn't exist anymore.    
        """
        self.free = False
        if self.food is None:
		    return self.transition("explore_state")
        food_loc = self.food
       	 
        #checking for enemies
        if len(self.enemies):
            if self.check_if_run(self.enemies[0][1], food_loc):
                self.dispatcher.free_food(self.food)
                self.food = None
                return self.transition("escape_state")
        
        if food_loc not in self.world.food():
            self.log.info("No more food at %s", food_loc)
            self.dispatcher.free_food(self.food)
            self.food = None
            return self.transition("explore_state")
       
        if self.world.distance(self.pos, food_loc) <= 1:
            self.log.info("Food is already close, not moving")
            return self.transition_delayed("explore_state")

        if not self.move_to(food_loc):
            self.dispatcher.free_food(self.food)
            self.food = None
            return self.transition("move_random_state")

    def escape_state(self):
        """
        Tries to escape from the closest enemy. Transition to explore if
        no enemy is close anymore
        """
        self.free = False
        
        if len(self.enemies) == 0:
            self.log.info("Danger is gone")
            return self.transition("explore_state")
        
        if not self.check_if_run(self.enemies[0][1]):
            return self.transition("explore_state")
        
        #checking if it can turn into an aggregator
        hills = self.my_hills(10)
        if (len(hills) and len(self.enemies) and
               self.world.distance(self.enemies[0][1], min(hills)[1]) < 
	           defenders_flock.DefendersFlock.danger_radius) : 
            #things are harsh, better create a defendersflock
            self.myhill = min(hills)[1]
            self.log.info("My hill is at %s, number of enemies is %d",
                    self.myhill, len(self.enemies))
            if defenders_flock.create(self, 10, len(self.enemies)):
                self.log.info("creating a DefendersFlock")
                return self.transition_delayed("forage_state")
            else:
                self.log.info("No DefendersFlock will be created")
        
        enemies_pos = [e[1] for e in self.enemies]
        if explorers_flock.create(self, self.gathering_radius, 
		                            enemies_pos):
            self.transition_delayed("explore_state")
            self.aggregator.need_a_step = self
            return

        #go in the same direction an enemy would go if it wants
        #to catch me. Randomly break the ties
        no_zones = set(itertools.chain.from_iterable(
                        drawcircle.can_attack(e[1], self.world.attackradius2)
                        for e in self.enemies))
        self.log.info("Hot zones are: %s", no_zones)
        choices = (p for p in self.world.neighbours(self.pos)
                    if p not in no_zones)
        for c in choices:
            if self.move_immediate_pos(c):
                self.log.info("Escaping to %s", c)
                break

    def step(self):
        """Calculate the number of nearby enemies before giving control to 
            the FSM
        """
        self.enemies = self.enemies_in_range(self.danger_radius)
        return super(Explorer, self).step()

    def controlled(self):
        """
        Set the ant as non-free and release the food
        """
        self.free = False
        if self.food:
            self.dispatcher.free_food(self.food)

