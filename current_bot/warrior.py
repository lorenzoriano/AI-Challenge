import MyBot
ants = MyBot.ants
import singleant
import warriors_flock
import random
import math

class Warrior(singleant.SingleAnt):
    """
    The Warrior ant.

    It will seek out enemy hills. This ant is usually controlled by a 
    WarriorsFlock
    """
    def __init__(self, loc, bot, world, dispatcher,
                ):
        
        super(Warrior, self).__init__(loc, bot, world, "planning_state")
        
        self.goal = None
        self.dispatcher = dispatcher
        self.food = None
        self.food_gather_range = int(math.sqrt(world.viewradius2))
   
    def planning_state(self):
        """
        The Warrior will go either towards an unseen location, or towards
        an enemy_hill
        """
        bot = self.bot
        if self.goal in bot.enemy_hills:
            return self.transition("attack_hill_state")
        
        world = self.world
        hills = [(world.distance(self.pos, h),h) for h in bot.enemy_hills]
        if len(hills) == 0:
            #checking for food
            if self.check_reserve_food():
                self.log.info("Food nearby, going for it!")
                return self.transition("forage_state")
            self.log.info("No enemy hills, exploring")
            return self.transition("explore_state")

        self.goal = min(hills)[1]
        self.log.info("going for hill %s", self.goal)
        return self.transition("attack_hill_state")


    def attack_hill_state(self):
        """
        Move towards an enemy hill, copting ants in the meantime   
        """
        if warriors_flock.create(self, 10):
            return self.transition_delayed("planning_state")
        if self.goal not in self.bot.enemy_hills:
            self.log.info("My goal hill at %s doesn't exist anymore!",
                    self.goal)
            return self.transition("planning_state")
        if self.pos == self.goal:
            self.log.info("Goal reached")
            #chances are this was an enemy hill
            self.bot.enemy_hills.discard(self.pos)
            return self.transition("planning_state")

        self.move_to(self.goal)
        return self.transition_delayed("planning_state")
    
    def explore_state(self):
        """
        The Warrior will move towards the closest unseen location.
        """
        unseen_locs = self.unseen_locations()
        self.goal = random.choice(unseen_locs)
        self.log.info("going for unseen loation")
        self.move_to(self.goal)

        return self.transition_delayed("planning_state")


    def check_reserve_food(self):
        """
        Returns True if it finds a reachable and reservable food,
        False otherwise.
        """        
        food = self.food_in_range(self.food_gather_range)
        for f in food:
            self.log.info("Is food @ %s free?", f)
            if self.bot.explorer_dispatcher.reserve_food(f, self):
                self.food = f
                self.log.info("Reserving food at %s", f)
                return True
        return False

    def forage_state(self):
        """
        Goes for food
        """
        if self.food is None:
		    return self.transition("planning_state")
        food_loc = self.food
        
        if food_loc not in self.world.food():
            self.log.info("No more food at %s", food_loc)
            self.bot.explorer_dispatcher.free_food(self.food)
            self.food = None
            return self.transition("planning_state")

        if self.world.distance(self.pos, food_loc) <= 1:
            self.log.info("Food is already close, not moving")
            return self.transition_delayed("planning_state")

        if not self.move_to(food_loc):
            self.bot.explorer_dispatcher.free_food(self.food)
            self.food = None
            return self.transition("planning_state")

    def remove_food(self):
        """Somebody from above commands I shouldn't follow food anymore"""
        self.log.info("I don't follow food at %s anymore", self.food)
        self.food = None
        self.transition_delayed("planning_state")

    def controlled(self):
        """
        Release the food
        """
        if self.food:
            self.bot.explorer_dispatcher.free_food(self.food)

