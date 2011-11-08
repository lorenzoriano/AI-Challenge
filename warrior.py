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
        
        self.goal_pos = None
        self.dispatcher = dispatcher
    
    def plan_for_hill_state(self):
        """
        Plans for the closest hill, or random movement if no hill in sight
        """
        world = self.world
        bot = self.bot

        hills = [(world.distance(self.pos, h),h) for h in bot.enemy_hills]
        if len(hills) == 0:
            return self.transition("explore_state")
        
        self.goal_pos = min(hills)[1]
        return self.transition("moving_state")

    def moving_state(self):
        """
        Move towards an enemy hill    
        """
        if self.pos == self.goal_pos:
            self.log.info("Goal reached")
            #chances are this was an enemy hill
            self.bot.enemy_hills.discard(self.pos)
            return self.transition_delayed("plan_for_hill_state")

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

        return self.transition_delayed("plan_for_hill_state")

    def explore_state(self):
        """
        Move to the closest unseen location
        """
        world = self.world
        unseen = []
        for u in self.bot.unseen:
            d = world.distance(self.pos, u)
            heapq.heappush(unseen, (d,u))
        
        if len(unseen) == 0:
            #no more hidden locations
            return self.transition("move_random_state")
        
        self.goal = unseen[0][1]
        return self.transition("moving_state")


