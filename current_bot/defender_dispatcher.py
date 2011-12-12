import logging
import pezz_logging
import castar
import defenders_flock

logger = logging.getLogger("pezzant.defender_dispatcher")

class DefenderDispatcher(object):
    """
    Creates Defenders
    """
    danger_radius = 15
    def __init__(self, world, bot):
        self.world = world
        self.bot = bot
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"DefenderDispatcher"},
                self.bot
                )
        self.assigned_hills = set()
        self.my_hills = set()
        self.ants = []
 
    def spawn_likelyhood(self):
        """
        Returns 0, as the dispatcher always creates DefendersFlock
        """
        return 0.
                
    def create_ant(self, loc):
        """
        Create a Warrior ant if needed.
        Returns the new ant if it has been created, None otherwise    
        """
        pass
      
    def remove_ant(self, ant):
        """
        Remove any reference to an ant when it dies
        """
        pass

    def remove_hill(self, hill):
        self.log.info("Hill %s is no longer protected", hill)
        self.assigned_hills.discard(hill)

    def create_flock(self, hill, enemies):
        if hill in self.assigned_hills:
            self.log.info("Hill %s already assigned", hill)
            return
        d = defenders_flock.create(self.bot, hill, enemies, self)
        if d:
            self.assigned_hills.add(hill)
            self.log.info("Assigning %s to hill %s. Good luck boys!",
                          d, hill)
        else:
            self.log.error("No ants??? Am I alive??")
        
    def step(self):
        """
        Creates a DefendersFlock for each threatened hill, if it has not been
        assigned yet.
        """
        self.my_hills = set(self.world.my_hills())

        for h in self.my_hills:
            enemies = list( e[0] for e in self.world.enemy_ants()
                            if castar.pathdist(e[0], h, self.danger_radius))
            if len(enemies):
                self.create_flock(h, enemies)
