import aggregator
import fsm
import castar
import defender
import heapq
import random
import MyBot
ants = MyBot.ants


class DefendersFlock(aggregator.Aggregator, fsm.FSM):
    """
    A DefendersFlock will be created whenever an hill is threatened by enemies.
    It will grab ants from the surrounding to defend the hill.
    """
    clustering_std = 1.0
    danger_radius = 15
    very_danger_radius = 10
    flocks_location = set()

    def __init__(self, leader, antlist, neighbour_dist):
        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "group")
        self.centroid = None
        self.attack_pos = None
        self.neighbour_dist = neighbour_dist
        self.world = leader.world
        self.myhill = leader.myhill
        self.bot = leader.bot
        self.close_enemy = None
        self.current_ant = leader
        self.close_enemies = []
  
        DefendersFlock.flocks_location.add(self.myhill)
        self.log.info("Flocks locations: %s", self.flocks_location)

        r,c = self.myhill
        world = self.bot.world
        self.ants_associations = {}
       
        #I know this is ugly
        gr, gc = r + 1, c
        if world.map[gr,gc] != ants.WATER:
            self.grouping_goal = gr, gc
            self.log.info("grouping goal is %s", self.grouping_goal)
            return
        gr, gc = r - 1, c
        if world.map[gr,gc] != ants.WATER:
            self.grouping_goal = gr, gc
            self.log.info("grouping goal is %s", self.grouping_goal)
            return
        gr, gc = r, c + 1
        if world.map[gr,gc] != ants.WATER:
            self.grouping_goal = gr, gc
            self.log.info("grouping goal is %s", self.grouping_goal)
            return
        gr, gc = r, c - 1
        if world.map[gr,gc] != ants.WATER:
            self.grouping_goal = gr, gc
            self.log.info("grouping goal is %s", self.grouping_goal)
            return

    def destroy(self):
        DefendersFlock.flocks_location.remove(self.myhill)
        super(DefendersFlock,self).destroy()

    def step(self, ant):
        """
        Simply invokes the FSM step method. 
        """
        aggregator.Aggregator.step(self, ant)
        if self.destroyed:
            return
        self.current_ant = ant
        fsm.FSM.step(self)
    
    def check_status(self):
        """
        If there are no enemies within self.danger_radius, then the flock can
        safely disband
        """
        if len(self.controlled_ants) == 0:
            return False
        self.close_enemies = self.enemies_in_range(self.danger_radius)
        if len(self.close_enemies):
            self.close_enemy = self.close_enemies[0][1]
            return True
        else:
            return False

    def enemies_in_range(self, r):
        """
        Returns an ordered list of (dist, location) of all the enemy 
        locations whose distance from the leader is <= r
        """

        world = self.world

        enemies = []
        for e in world.enemy_ants():
            d = world.distance(self.leader.pos, e[0])
            if d <= r:
                heapq.heappush(enemies,(d,e[0]) )

        return enemies
   
    def associate_ants(self):
        """
        For each ant in the group, associate the closest (without replacement)
        enemy ant.
        """
        self.ants_associations.clear()
        enemy_list = set(e[1] for e in self.close_enemies)
        world = self.world
        for ant in self.controlled_ants:
            if len(enemy_list) == 0:
                self.log.error("we have more ants than enemies")
                break
            close_enemy = min((world.distance(ant.pos, e),e)
                    for e in enemy_list)[1]
            self.log.info("Associating ant %s with enemy %s", ant, close_enemy)
            self.ants_associations[ant] = close_enemy
            enemy_list.remove(close_enemy)

        if len(self.ants_associations) < len(self.controlled_ants):
            self.log.error("There are more enemies than ants!")


    def newturn(self):
        """
        Add ants to this group.
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

        while len(self.controlled_ants) > len(self.close_enemies):
            ant_to_remove = random.choice(list(self.controlled_ants))
            self.log.info("The enemies are fewer, freeing ant %s",
                    ant_to_remove)
            self.remove_ant(ant_to_remove)

        for ant in copted_ants:
            if len(self.controlled_ants) >= len(self.close_enemies):
                break
            self.control(ant)

        #doing this before would be useless
        super(DefendersFlock, self).newturn()
        self.calculate_grouping()
       
        self.setup_planner(True)
        self.associate_ants()
        self.transition_delayed("kamikaze")
        return
        
        #checking for clear danger
        if self.close_enemy <= self.very_danger_radius:
            self.log.warning("enemies at the door!!")
            self.transition_delayed("very_danger")
            return

        if self.world.distance(self.centroid, self.myhill) > self.danger_radius/2.:
            #we don't want to get to far from home
            self.setup_planner(True)
            return self.transition_delayed("homing")
        elif (self.grouping > self.clustering_std and 
                self.previous_poses != self.current_poses):
            self.setup_planner(True)
            return self.transition_delayed("group")
        else:
            self.setup_planner(False)
            return self.transition_delayed("attacking")

    def kamikaze(self):
        """
        Move each ant towards the associated enemy
        """
        try:
            enemy = self.ants_associations[self.current_ant]
        except KeyError:
            self.log.info("Ant %s has no associated enemy!", self.current_ant)
            return

        self.current_ant.move_to(enemy)

    def homing(self):
        """
        Moves the ant towards the hill
        """
        self.current_ant.move_to(self.myhill)

    def group(self):
        """
        Groups the ants
        """
        self.current_ant.move_to(self.grouping_goal)

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

def create(calling_ant, neighbour_dist, nenemies):
    """
    Create a new DefendersFlock made by at most nememies ants within
    neighbour_dist of the hill.
    """
    myhill = calling_ant.myhill
    global flocks_location
    if myhill in DefendersFlock.flocks_location:
        calling_ant.log.info("Flocks location: %s", 
                DefendersFlock.flocks_location)
        return False
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
        if len(ant_list) >= nenemies:
            break
    
    DefendersFlock(calling_ant, ant_list, neighbour_dist)
    return True
