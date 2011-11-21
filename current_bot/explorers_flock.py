import aggregator
import fsm
import numpy as np
import heapq
import castar

class ExplorerFlock(aggregator.Aggregator, fsm.FSM):
    """
    An Aggregator that tries first to cluster the belonging
    ants, then move them towards the closest enemy.
    """

    clustering_std = 1.0
    min_attacking_steps = 5

    def __init__(self, leader, antlist):
        """
        Parameters:
    
        leader: the ants on which many computations might be based.
        antlist: a list of ants to add to this aggregator
    
        """
        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "group")
        self.current_ant = leader
        self.centroid = None
        self.grouping_step = 0
        self.attacking_step = 0
        self.attack_pos = None
        self.grouping = 0
        self.previous_poses = None
        self.current_poses = None

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
        self.previous_poses = self.current_poses
        self.current_poses = [ant.pos for ant in self.controlled_ants]
        arr = np.array(self.current_poses)
        m = np.mean(arr,0)
        self.centroid = (int(round(m[0])),
                         int(round(m[1]))
                        )
        self.log.info("New centroid: %s", self.centroid)
        #grouping_steps is measured per turn
       
        self.grouping = np.max(np.std(arr,0))
        self.log.info("Grouping value of %f", self.grouping)

        #the steps are calculated once per turn
        #self.grouping_step += 1
        self.attacking_step += 1

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
        If it has spent more than max_grouping_steps in this state, or if
        the ants are compact enough, it transits to attack
        transit to max_grouping_steps.

        """
        self.attacking_step = 0
        #if self.grouping_step > self.max_grouping_steps:
        #    self.log.info("After speing %d turns in grouping, time to attack",
        #                self.grouping_step)
        #    return self.transition("attack")
        
        if self.previous_poses == self.current_poses:
            self.log.info("Ants didn't move, stepping out of grouping")
            return self.transition("attack")
        
        if self.grouping <= self.clustering_std:
            self.log.info("Grouping value %, time to attack")
            return self.transition("attack")

        self.log.info("moving ant %s towards the centre", self.current_ant)
        self.current_ant.move_to(self.centroid)

    def attack(self):
        """
        Move the ants towards the enemies
        """
        self.grouping_step = 0
        
        if (self.grouping > self.clustering_std and 
                self.attacking_step > self.min_attacking_steps):
            self.log.info("Grouping value %, time to regroup")
            return self.transition_delayed("group")

        self.log.info("ant %s attacks towards %s", self.current_ant,
                self.attack_pos)
        self.current_ant.move_to(self.attack_pos)

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
    close_locations = castar.find_near(calling_ant.pos, neighbour_dist)
    ant_list = [calling_ant]
    bot = calling_ant.bot
    
    for loc in close_locations:
        ant = bot.find_ant(loc)
        if ant is None:
            continue
        #don't steal other ants
        if not hasattr(ant, 'aggregator'):
            ant_list.append(ant)
    
    if len(ant_list) >= neighbour_size:
        #create the Aggregator, which will store an instance of itself in each
        #controlled ant
        ExplorerFlock(calling_ant, ant_list)
        return True
    else:
        return False

