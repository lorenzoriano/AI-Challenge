import aggregator
import fsm
import heapq
import castar
import defenders_flock

class ExplorerFlock(aggregator.Aggregator, fsm.FSM):
    """
    An Aggregator that tries first to cluster the belonging
    ants, then move them towards the closest enemy.
    """

    clustering_std = 1.0
    max_group_size = 3

    def __init__(self, leader, antlist):
        """
        Parameters:
    
        leader: the ants on which many computations might be based.
        antlist: a list of ants to add to this aggregator
    
        """
        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "group")
        self.current_ant = leader
        self.attack_pos = None

    def step(self, ant):
        """
        Simply invokes the FSM step method. 
        """
        aggregator.Aggregator.step(self, ant)
        if self.destroyed:
            return
        self.current_ant = ant
        fsm.FSM.step(self)

    def newturn(self):
        """
        Calculates the centroid and grouping of all the ants. This function
        also controls the transitions of the FSM
        """
        super(ExplorerFlock, self).newturn()
        self.calculate_grouping()
        
        if self.previous_poses == self.current_poses:
            self.log.info("Ants didn't move, stepping out of grouping")
            self.setup_planner(False)
            return self.transition_delayed("attack")
        
        if (self.grouping > self.clustering_std): 
            self.log.info("Grouping value %f, time to regroup", self.grouping)
            self.setup_planner(True)
            return self.transition_delayed("group")

    def check_status(self):
        """
        If the number of controlled ants is less than 3, or the 
        number of enemies in range is 0, then the Aggregator
        dismantles.
        """
        if len(self.controlled_ants) < 3:
            self.log.info("No more enough controlled ants")
            return False
        
        #calculating the distance between the enemies and all the ants
        r = 1.5 * self.leader.world.attackradius2
        all_enemies = []
        for ant in self.controlled_ants:
            enemies_list = ant.enemies_in_range(r)
            all_enemies = list(heapq.merge(enemies_list, all_enemies))

        if len(all_enemies) == 0:
            self.log.info("No more enemies in range")
            return False

        self.attack_pos = all_enemies[0][1]
        return True

    def group(self):
        """
        Moves all the ants towards the current centroid. 
        """
        
        self.log.info("moving ant %s towards the centre", self.current_ant)
        self.current_ant.move_to(self.centroid)

    def attack(self):
        """
        Move the ants towards the enemies
        """

        self.log.info("ant %s attacks towards %s", self.current_ant,
                self.attack_pos)
        self.current_ant.move_to(self.attack_pos)
    
    @staticmethod
    def check_if_grab(ant):
        """
        Return true if it can grab an ant
        """
        if hasattr(ant, "aggregator"):
            return False
        else:
            return True

def create(calling_ant, neighbour_size, neighbour_dist):
    """
    Create a new ExplorerFlock if the number of friendly ants
    whose distance (calculated using the A*) is closer than neighbour_dist.

    Parameters:
    calling_ant: The ant that has requested to form the aggregator.
    neighbour_dist: The max distance from the other ants to add to the
    aggregator.
    neighbour_size: The minimum number of ants to aggregate.

    Return:
    True if the Aggregator could be formed, False if less than neighbout_size
    ants are closer than neighbour_dist.
    """
    #TODO this can be optimized, see the other flocks
    close_locations = castar.find_near(calling_ant.pos, neighbour_dist)
    ant_list = [calling_ant]
    bot = calling_ant.bot
    
    for loc in close_locations:
        ant = bot.find_ant(loc)
        if ant is None:
            continue
        #don't steal other ants
        if ExplorerFlock.check_if_grab(ant):
            ant_list.append(ant)
            if len(ant_list) >= ExplorerFlock.max_group_size:
                break
    
    if len(ant_list) >= neighbour_size:
        #create the Aggregator, which will store an instance of itself in each
        #controlled ant
        ExplorerFlock(calling_ant, ant_list)
        return True
    else:
        return False

