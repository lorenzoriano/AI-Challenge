import singleant
import random
import ants


class Explorer(singleant.SingleAnt):
    """
    The Explorer ant.

    This ant will move to random locations and it will head for food
    if it sees any. It will head away from enemies
    """
    def __init__(self, loc, bot, world, dispatcher):
        super(Explorer, self).__init__(loc, bot, world)
        self.state = "explore_state"
        self.goal_pos = None
        self.danger_radius = 1.5 * world.attackradius2
        self.dispatcher = dispatcher

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
    
    def generate_random_goal(self):
        """
        Generate a new random location
        """
        row = random.randint(0, self.world.rows)
        col = random.randint(0, self.world.cols)
        self.log.info("random movement to %s", (row,col))
        return  (row, col)

    def check_reserve_food(self):
        """
        Returns a food loc if it finds a reachable and reservable food,
        False otherwise.
        """        
        food = self.food_in_range(10)
        for f in food:
            loc = f[1]
            if self.dispatcher.reserve_food(loc, self):
                self.food = loc
                self.log.info("Reserving food at %s", loc)
                return True
        return False
    
    def explore_state(self):
        """
        Generate a random goal then transition to move_to_goal.
        If it sees an enemy or food then transition accordingly.
        """
        #checking for food
        if self.check_reserve_food():
            return self.transition("forage_state")

        #checking for enemies
        self.enemies = self.enemies_in_range(5)
        if len(self.enemies):
            return self.transition("escape_state")

        #generating a random goal
        self.goal_pos = self.generate_random_goal()
        return self.transition("moving_state")

    def moving_state(self):
        """
        Move towards self.goal_pos if no enemies or food. 
        Transition to explore_state if goal reached
        """
        #checking for food
        if self.check_reserve_food():
            return self.transition("forage_state")

        #checking for enemies
        self.enemies = self.enemies_in_range(self.danger_radius)
        if len(self.enemies):
            return self.transition("escape_state")

        if self.pos == self.goal_pos:
            self.log.info("Goal reached")
            return self.transition("explore_state")

        if not self.move_to(self.goal_pos):
            return self.transition_delayed("explore_state")

    def forage_state(self):
        """
        Move towards food. Transition to enemy. Transition to explore
        if the food has been reached or if it doesn't exhist anymore.    
        """
        #checking for enemies
        self.enemies = self.enemies_in_range(self.danger_radius)
        if len(self.enemies):
            self.dispatcher.free_food(self.food)
            self.food = None
            return self.transition("escape_state")
        
        food_loc = self.food
        if self.world.map[food_loc[0]][food_loc[1]] != ants.FOOD:
            self.log.info("No more food at %s", food_loc)
            self.dispatcher.free_food(self.food)
            self.food = None
            return self.transition("explore_state")
        
        if not self.move_to(food_loc):
            self.dispatcher.free_food(self.food)
            self.food = None
            return self.transition_delayed("explore_state")

    def escape_state(self):
        """
        Tries to escape from the closest enemy. Transition to explore if
        no enemy is close anymore
        """
        #checking for enemies
        self.enemies = self.enemies_in_range(self.danger_radius)
        if len(self.enemies) == 0:
            self.log.info("Danger is gone")
            return self.transition("explore_state")

        #go in the same direction an enemy would go if it wants
        #to catch me. Randomly break the ties
        
        epos = self.enemies[0][1]
        dir = self.world.direction(epos, self.pos)
        if not self.move_heading(random.choice(dir)):
            #desperate random move
            dir = random.choice(['n', 's', 'w', 'e'])
            self.move_heading(dir)

    def step(self):
        """
        Execute the state the Explorer is in
        """
        action = getattr(self, self.state)
        action()
    
