import MyBot
ants = MyBot.ants
import singleant
import warriors_flock
import random

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
        d, self.goal = random.choice(unseen_locs)
        self.log.info("going for unseen loation")
        self.move_to(self.goal)

        return self.transition_delayed("planning_state")
