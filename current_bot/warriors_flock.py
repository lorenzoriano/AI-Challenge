import aggregator
import fsm
import numpy as np
import heapq
import castar
import random
import warrior
import defender
from MyBot import ants

import astar
class GroupPlanner(object):
    """
    This planner will not penalize movement over other ants, therefore
    allowing for a more compact group motion.
    It mimics the interface of the castar module.
    """
    def __init__(self, mat):
        self.astar_mat = astar.MatrixHolder(mat)
        self.astar_m = astar.AstarMatrix(self.astar_mat,10000,4)
    
    def reset(self, mat):
        """
        Reset the astar structures.
        """
        self.astar_mat.setMat(mat)
        self.astar_m.reset()
    
    def pathfind(self, start_pos, goal_pos, bot = None, world = None):
        """
        Plan a path from start_pos to goal_pos.

        Returns the path, which is empty if no path was found
        """
        path, cost = self.astar_m.solve(start_pos, goal_pos)
        if len(path) == 0:
            return []
        else:
            return path[1:]

    def find_near(self, start_pos, max_cost):
        """
        Find all the cells within max_cost distance.
        Returns a list of the cells, empty if no cell
        was found. The starting cell will not be included.
        """
        cells = self.astar_m.solve_for_near_states(start_pos, max_cost)
        if len(cells) == 0:
            return cells
        else:
            return cells[1:]

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
    min_attacking_steps = 0
    min_group_size = 3
    max_ants = 6

    def __init__(self, leader, antlist, neighbour_dist):
        """
        Parameters:
    
        leader: the ants on which many computations might be based.
        antlist: a list of ants to add to this aggregator
        neighbout_dist: the max dist to gather new elements
        """
        self.planner = GroupPlanner(leader.world.map)
        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "group")
        self.current_ant = leader
        self.centroid = None
        self.attack_pos = None
        self.grouping = 0
        self.previous_poses = None
        self.current_poses = None
        self.neighbour_dist = neighbour_dist
        self.danger_radius = 1.5 * leader.world.attackradius2
        self.world = leader.world

    def setup_planner(self, group_state):
        newmat = np.ones(self.world.map.shape, dtype=np.float64)
        newmat[self.world.map == ants.WATER] = -1
        if group_state:
            newmat[self.world.map == ants.ANTS] = 4
        self.planner.reset(newmat)

    def step(self, ant):
        """
        Simply invokes the FSM step method. 
        """
        aggregator.Aggregator.step(self, ant)
        if self.destroyed:
            return
        self.current_ant = ant
        fsm.FSM.step(self)

    def control(self, ant):
        """
        Replaces the ant astar
        """
        self.log.info("Replacing the astar of %s", ant)
        super(WarriorsFlock, self).control(ant)
        ant.planner = self.planner

    def remove_ant(self,ant):
        """
        Restore the ant's castar
        """
        self.log.info("Restoring the astar of %s", ant)
        super(WarriorsFlock, self).remove_ant(ant)
        ant.planner = castar

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
        
        bot = self.leader.bot
        close_enemy = any(a.enemy_in_range(self.danger_radius)
                for a in self.controlled_ants)
        if (not close_enemy) and (self.attack_pos not in bot.enemy_hills):
            self.free_non_warriors()
        
        if self.attack_pos in bot.enemy_hills:
            self.log.info("I am going for an hill, copting elements")
            antlist = bot.ants
        elif close_enemy:
            self.log.info("enemies around, copting elements")
            antlist = bot.ants
        else:
            antlist = bot.warrior_dispatcher.ants


        copted_ants = (a for a in antlist
                    if self.check_if_grab(a) and 
                    (0 < 
                     len(castar.pathfind(self.leader.pos, a.pos)) 
                     < self.neighbour_dist
                    )
                 )
        
        for ant in copted_ants:
            if len(self.controlled_ants) >= self.max_ants:
                self.log.info("max number of ants reached")
                break
            self.control(ant)

        self.calculate_grouping()
        #transitions
        if self.previous_poses == self.current_poses:
            self.log.info("Ants didn't move, stepping out of grouping")
            self.setup_planner(False)
            return self.transition_delayed("attack")
        elif close_enemy and (self.grouping > self.clustering_std):
            self.log.info("Enemies nearby, regrouping")
            self.log.info("Grouping value is: ", self.grouping)
            self.log.info("Ants pos are: ", self.current_poses)
            self.setup_planner(True)
            return self.transition_delayed("group")
        else:
            self.log.info("I can move freely towards the target %s", 
                    self.attack_pos)
            self.setup_planner(False)
            return self.transition_delayed("attack")


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
            else:
                return False
        
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
        """

        self.log.info("moving ant %s towards the centre", self.current_ant)
        self.current_ant.move_to(self.centroid)

    def attack(self):
        """
        Move the ants towards the goal.
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
        elif type(ant) is defender.Defender:
            return False
        else:
            return True


def create(calling_ant, neighbour_dist):
    """
    Create a new WarriorsFlock made by all the non aggregated warrior within
    neighbour_dist.
    """
    ant_list = set([calling_ant])
    bot = calling_ant.bot
    free_ants = (a for a in bot.warrior_dispatcher.ants
                    if WarriorsFlock.check_if_grab(a) and 
                    (0 < 
                     len(castar.pathfind(calling_ant.pos, a.pos)) 
                     < neighbour_dist
                    )
                 )
    for ant in free_ants:
        if len(ant_list) >= WarriorsFlock.max_ants:
            break
        ant_list.add(ant)
    if len(ant_list) < WarriorsFlock.min_group_size:
        return False
    
    WarriorsFlock(calling_ant, ant_list, neighbour_dist)
    return True
