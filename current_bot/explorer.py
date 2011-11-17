import MyBot
ants = MyBot.ants
import singleant
import random
#import ants
import explorers_flock 


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
        self.danger_radius = 1.5 * world.attackradius2
        self.dispatcher = dispatcher
        self.area_loc = area_loc
        self.food_gather_range = food_range
        self.map = world.map
        self.food = None
        self.enemies = None

    def generate_random_goal(self):
        """
        Generate a new random location around the assigned area.
        If it can't find a suitable location within 10 trials, go to completely
        random location.
        """
        r = self.food_gather_range
        area_loc = self.area_loc
        maxrow = self.world.rows
        maxcol = self.world.cols

        row = random.randint(area_loc[0]-r, area_loc[0]+r)
        if row < 0:
            row = maxrow + row
        elif row > maxrow:
            row = row - maxrow

        col = random.randint(area_loc[1]-r, area_loc[1]+r)
        if col < 0:
            col = maxcol + col
        elif col > maxcol:
            col = col - maxcol 
        
        self.log.info("random movement to %s", (row,col))
        return  (row, col)

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
    
    def check_if_run(self, enemy_loc, food_loc=None):
        """
        An ant will run from an enemy unless it's close to its hill or if food
        is closer.
        """
#        self.log.warning("No fleeing from enemies!")
#        return False
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
        
        #checking for enemies
        self.enemies = self.enemies_in_range(self.danger_radius)
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
        #checking for enemies
        self.enemies = self.enemies_in_range(self.danger_radius)
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
        directions = ['n','s','w','e']
        random.shuffle(directions)

        for d in directions:
            if self.move_heading(d):
                break

        return self.transition_delayed("explore_state")

    def forage_state(self):
        """
        Move towards food. Transition to enemy. Transition to explore
        if the food has been reached or if it doesn't exhist anymore.    
        """
        food_loc = self.food
        
        #checking for enemies
        self.enemies = self.enemies_in_range(self.danger_radius)
        if len(self.enemies):
            if self.check_if_run(self.enemies[0][1], food_loc):
                self.dispatcher.free_food(self.food)
                self.food = None
                return self.transition("escape_state")
        
        if self.world.map_value(food_loc) != ants.FOOD:
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
        #checking if it can turn into an aggregator
        if explorers_flock.create(self, 3, 10):
            return self.transition("explore_state")
        #checking for enemies
        self.enemies = self.enemies_in_range(self.danger_radius)
        if len(self.enemies) == 0:
            self.log.info("Danger is gone")
            return self.transition("explore_state")

        if not self.check_if_run(self.enemies[0][1]):
            return self.transition("explore_state")
        
        #go in the same direction an enemy would go if it wants
        #to catch me. Randomly break the ties
        epos = self.enemies[0][1]
        dir = self.world.direction(epos, self.pos)
        if not self.move_heading(random.choice(dir)):
            #desperate random move
            dir = random.choice(['n', 's', 'w', 'e'])
            self.move_heading(dir)
