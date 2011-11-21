import aggregator
import fsm
import numpy as np
import heapq
import castar
import random
import warrior

class WarriorsFlock(aggregator.Aggregator, fsm.FSM):
    """
    An Aggregator that tries first to cluster the belonging
    ants, then move them towards the closest enemy hill.

    The WarriorsFlock first gathers surronding Warriors (gather state), 
    and keeps doing this all the time. When the number of controlled ants is
    sufficient, it will group (grouping state) and 
    drive them towards an enemy hill (attack state).
    If the number of ants falls below half the original attacking group size,
    it will switch back to the gather state. Every time the group is not
    compact it will fall back to the grouping state.

    Only non-aggreagated Warriors will be added to this group. 
    If there are no visible enemy hills the group dibands.
    """

    clustering_std = 1.5
    min_attacking_steps = 5
    min_group_size = 5

    def __init__(self, leader, antlist, neighbour_dist):
        """
        Parameters:
    
        leader: the ants on which many computations might be based.
        antlist: a list of ants to add to this aggregator
        neighbout_dist: the max dist to gather new elements
        """
        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "group")
        self.current_ant = leader
        self.centroid = None
        self.attacking_step = 0
        self.attack_pos = None
        self.grouping = 0
        self.previous_poses = None
        self.current_poses = None
        self.neighbour_dist = neighbour_dist
        self.danger_radius = 1.5 * leader.world.attackradius2

    def step(self, ant):
        """
        Simply invokes the FSM step method. 
        """
        aggregator.Aggregator.step(self, ant)
        if self.destroyed:
            return
        self.current_ant = ant
        fsm.FSM.step(self)

    def calculate_grouping(self):
        """
        Calculate the grouping factor and the centroid of all the 
        controlled ants.
        
        Grouping is defined as the standard deviation between the poses
        of all the ants.
        """
        arr = np.array(self.current_poses)
        m = np.mean(arr,0)
        self.centroid = (int(round(m[0])),
                         int(round(m[1]))
                        )
        self.log.info("New centroid: %s", self.centroid)
       
        self.grouping = np.max(np.std(arr,0))
        self.log.info("Grouping value of %f", self.grouping)

    def free_non_warriors(self):
        """
        Remove non warriors among the controlled ants.
        """
        for ant in self.controlled_ants.copy():
            if type(ant) is not warrior.Warrior:
                self.log.info("I don't need %s now", ant)
                self.remove_ant(ant)

    def newturn(self):
        """
        Calculates the centroid and grouping of all the ants. Add ants to
        this group.
        """
        self.previous_poses = self.current_poses
        self.current_poses = [ant.pos for ant in self.controlled_ants]
        
        self.calculate_grouping()

        self.attacking_step += 1
        bot = self.leader.bot
        enemies = self.current_ant.enemies_in_range(self.danger_radius)
        if len(enemies) == 0:
            self.free_non_warriors()
        
        if self.attack_pos in bot.enemy_hills:
            self.log.info("I am going for an hill, copting elements")
            antlist = bot.ants
        elif len(enemies):
            self.log.info("enemies aroung, copting elements")
            antlist = bot.ants
        else:
            antlist = bot.warrior_dispatcher.ants
        copted_ants = (a for a in antlist
                    if not hasattr(a,"aggregator") and 
                    (0 < 
                     len(castar.pathfind(self.leader.pos, a.pos)) 
                     < self.neighbour_dist/2.
                    )
                 )
        
        for ant in copted_ants:
            self.control(ant)

    def check_status(self):
        """
        If the number of visible enemy hills or the number of controlled ants
        is zero, the group disbands. The goal is calculated as the hill closest
        to the leader.
        """
        if len(self.controlled_ants) < self.min_group_size:
            self.log.info("No more enough controlled ants")
            return False
        
        enemy_hills = self.bot.enemy_hills
        if len(enemy_hills) == 0:
            self.log.info("No more enemy hills!")
            
            #going for unseen location
            unseen_locs = self.leader.unseen_locations()
            if (unseen_locs):
                self.attack_pos = unseen_locs[0][1]
                self.log.info("going for unseen loation")
                return True
            #going for enemy ants
            enemy_list = self.leader.enemies_in_range(1000)
            if len(enemy_list) == 0:
                self.log.warning("No enemies, how come?")
                return False
            else:
                self.log.info("Going for enemies")
                self.attack_pos = enemy_list[0][1]
                return True
        
        #here we have discovered enemy hills 
        if self.attack_pos in enemy_hills:
            self.log.info("I already know my target: %s", self.attack_pos)
            return True

        #calculating the distance between the enemy hills and the leader
        hills_dists = []
        for hill in enemy_hills:
            d = len(castar.pathfind(self.leader.pos, hill))
            if d != 0:
                heapq.heappush(hills_dists, (d, hill))
        self.attack_pos = hills_dists[0][1]

        return True

    def group(self):
        """
        Moves all the ants towards the current centroid. 
        If the ants are compact enough or if they are not moving anymore 
        it transits to attack.
        """
        self.attacking_step = 0
        
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
        Move the ants towards the enemy's hill.
        """
        self.grouping_step = 0
         
        
        enemies = self.current_ant.enemies_in_range(self.danger_radius)
        if len(enemies) > 0:
            if (self.grouping > self.clustering_std and 
                    self.attacking_step > self.min_attacking_steps):
                self.log.info("Grouping value %, time to regroup")
                return self.transition("group")
        
        self.log.info("ant %s attacks towards %s", self.current_ant,
                self.attack_pos)
        self.current_ant.move_to(self.attack_pos)

def create(calling_ant, neighbour_dist):
    """
    Create a new WarriorsFlock made by all the non aggregated warrior within
    neighbour_dist.
    """
    ant_list = set([calling_ant])
    bot = calling_ant.bot
    free_ants = (a for a in bot.warrior_dispatcher.ants
                    if not hasattr(a,"aggregator") and 
                    (0 < 
                     len(castar.pathfind(calling_ant.pos, a.pos)) 
                     < neighbour_dist
                    )
                 )
    for ant in free_ants:
        ant_list.add(ant)
    if len(ant_list) < WarriorsFlock.min_group_size:
        return False
    
    WarriorsFlock(calling_ant, ant_list, neighbour_dist)
    return True
