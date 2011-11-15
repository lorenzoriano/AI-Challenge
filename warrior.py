import MyBot
ants = MyBot.ants
import singleant
import random
import heapq

class Warrior(singleant.SingleAnt):
    """
    The Warrior ant.

    It will seek out enemy hills
    """
    def __init__(self, loc, bot, world, dispatcher,
                ):
        
        super(Warrior, self).__init__(loc, bot, world, "plan_for_hill_state")
        
        self.goal_hill = None
        self.dispatcher = dispatcher
    
    def plan_for_hill_state(self):
        """
        Plans for the closest hill, or random movement if no hill in sight
        """
        world = self.world
        bot = self.bot

        hills = [(world.distance(self.pos, h),h) for h in bot.enemy_hills]
        if len(hills) == 0:
            self.log.info("No hills, dying")
            self.pos = (-1,-1)
            return None
            
        self.goal_hill = min(hills)[1]
        self.log.info("going for hill %s", self.goal_hill)
        return self.transition("moving_hill_state")

    def moving_hill_state(self):
        """
        Move towards an enemy hill    
        """
        r,c = self.goal_hill
        if self.goal_hill not in self.bot.enemy_hills:
            self.log.info("My goal hill at %s doesn't exist anymore!",
                    self.goal_hill)
            return self.transition("plan_for_hill_state")
        if self.pos == self.goal_hill:
            self.log.info("Goal reached")
            #chances are this was an enemy hill
            self.bot.enemy_hills.discard(self.pos)
            return self.transition_delayed("plan_for_hill_state")

        if not self.move_to(self.goal_hill):
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

        return self.transition_delayed("plan_for_hill_state")
