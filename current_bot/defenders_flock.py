import aggregator
import fsm
import numpy as np
import castar
import defender
import heapq

class DefendersFlock(aggregator.Aggregator, fsm.FSM):
    """
    A DefendersFlock will be created whenever an hill is threatened by enemies.
    It will grab ants from the surrounding to defend the hill.
    """
    clustering_std = 1.0
    danger_radius = 10
    very_danger_radius = 5

    def __init__(self, leader, antlist, neighbour_dist):

        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "group")
        self.centroid = None
        self.attack_pos = None
        self.previous_poses = None
        self.current_poses = None
        self.neighbour_dist = neighbour_dist
        self.world = leader.world
        self.myhill = leader.myhill
        self.bot = leader.bot
        self.close_enemy = None
        self.current_ant = leader
        self.grouping = 0

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
    
    def check_status(self):
        """
        If there are no enemies within self.danger_radius, then the flock can
        safely disband
        """
#        self.close_enemy = self.enemy_in_range(self.danger_radius)
        self.close_enemies = self.enemies_in_range(self.danger_radius)
        if len(self.close_enemies):
            self.close_enemy = self.close_enemies[0][1]
            return True
        else:
            return False

    def enemy_in_range(self, r):
        """
        Returns the enemy location if it is less than r distant from the
        home hill, None otherwise
        """

        world = self.world
        for e in world.enemy_ants():
            d = world.distance(self.myhill, e[0])
            if d <= r:
                self.log.info("Close enemy at %s", e)
                return e[0]
        self.log.info("No enemy within %f", r)
        return None

    def enemies_in_range(self, r):
        """
        Returns an ordered list of (dist, location) of all the enemy 
        locations whose distance from the hill is <= r
        """

        world = self.world

        enemies = []
        for e in world.enemy_ants():
            d = world.distance(self.myhill, e[0])
            if d <= r:
                heapq.heappush(enemies,(d,e[0]) )

        return enemies
    
    def newturn(self):
        """
        Calculates the centroid and grouping of all the ants. Add ants to
        this group.
        This function changes the state of the whole flock
        """
        copted_ants = (a for a in self.bot.ants
                    if
                    type(getattr(a,'aggregator',None)) is not DefendersFlock
                    and 
                    (0 < 
                     len(castar.pathfind(self.myhill, a.pos)) 
                     < self.neighbour_dist
                    )
                 )
        for ant in copted_ants:
            self.control(ant)

        #checking for clear danger
        if self.close_enemy <= self.very_danger_radius:
            self.log.warning("enemies at the door!!")
            self.transition_delayed("very_danger")
            return
        
        #doing this before would be useless
        self.previous_poses = self.current_poses
        self.current_poses = [ant.pos for ant in self.controlled_ants]
        self.calculate_grouping()

        if self.world.distance(self.leader.pos, self.myhill) > self.danger_radius/2.:
            #we don't want to get to far from home
            return self.transition_delayed("homing")
        elif (self.grouping > self.clustering_std and 
                self.previous_poses != self.current_poses):
            return self.transition_delayed("group")
        else:
            return self.transition_delayed("attacking")

    def homing(self):
        """
        Moves the ant towards the hill
        """
        self.current_ant.move_to(self.myhill)

    def group(self):
        """
        Groups the ants
        """
        self.current_ant.move_to(self.centroid)

    def attacking(self):
        """
        Attacks the closest enemy
        """
        target = self.close_enemy
        self.current_ant.move_to(target)

    def very_danger(self):
        """
        Move the ant towards the hill
        """
        #TODO use a spiral distribution
        self.current_ant.move_to(self.myhill)

def create(calling_ant, neighbour_dist):
    """
    Create a new DefendersFlock made by all the ants within
    neighbour_dist of the hill.
    """
    myhill = calling_ant.myhill
    ant_list = set([calling_ant])
    bot = calling_ant.bot
    free_ants = (a for a in bot.ants
                    if
                    type(getattr(a,'aggregator',None)) is not DefendersFlock
                    and 
                    (0 < 
                     len(castar.pathfind(a.pos, myhill)) 
                     < neighbour_dist
                    )
                 )
    for ant in free_ants:
        ant_list.add(ant)
    
    DefendersFlock(calling_ant, ant_list, neighbour_dist)
    return True
