import aggregator
import fsm
import castar
from c_simulator import c_simulator

class ExplorerFlock(aggregator.Aggregator, fsm.FSM):
    """
    An Aggregator that tries first to cluster the belonging
    ants, then move them towards the closest enemy.
    """

    clustering_std = 1.0
    min_group_size = 2
    min_grouping = 5.0

    def __init__(self, leader, antlist):
        """
        Parameters:
    
        leader: the ants on which many computations might be based.
        antlist: a list of ants to add to this aggregator
    
        """
        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "group")
        self.current_ant = leader
        self.all_enemies = set()
        self.positions_assigned = set()
        self.policy = {}
        self.current_ant = None

    def step(self, ant):
        """
        Simply invokes the FSM step method. 
        """
        aggregator.Aggregator.step(self, ant)
        if self.destroyed:
            return
        self.current_ant = ant
        fsm.FSM.step(self)

    def gather_new_ants(self):
        """Gathers new ants around this flock"""

        if len(self.controlled_ants) > len(self.all_enemies) + 1:
            self.log.info("I have already enough ants, no gathering")
            return

        def aggr_check(ant):
            aggr = getattr(ant,'aggregator',None)
            if aggr is None:
                return True
            elif aggr == self:
                return False
            elif type(aggr) is ExplorerFlock:
                return True
            else:
                return False

        coptable_ants = (a for a in self.bot.ants
                         if
                         aggr_check(a)
                         and
                         any(self.world.distance(a.pos, myant.pos) < 4 
                             for myant in self.controlled_ants)
                        )
        
        for ant in coptable_ants:
            self.log.info("Adding ant %s to my flock", ant)
            self.control(ant)

    def create_policy(self):    
        sim = c_simulator.Simulator(self.world.map)
        policy_ants = set(a for a in self.controlled_ants 
                if any(self.can_attack(a.pos,e) for e in self.all_enemies) )
        policy_enemies = set(e for e in self.all_enemies 
                if any(self.can_attack(a.pos,e) for a in policy_ants) )
        
        len_friends = len(policy_ants)
        len_enemies = len(policy_enemies)
        if ((len_friends>0) and (len_enemies)>0):
            self.log.info("Policy ants: %s", policy_ants)
            self.log.info("Policy enemies: %s", policy_enemies)
            sim.create_from_lists(policy_ants, policy_enemies)
            
            if len_friends > len_enemies:
                score_0 = c_simulator.ConservativeScore(sim,0)
                score_1 = c_simulator.ConservativeScore(sim,1)
            elif len_friends == len_enemies:
                score_0 = c_simulator.ConservativeScore(sim,0)
                score_1 = c_simulator.ConservativeScore(sim,1)
            else:
                score_0 = c_simulator.UltraConservativeScore(sim,0)
                score_1 = c_simulator.AggressiveScore(sim,1)
            
            t = self.calculate_time_per_policy()
            if t <= 0:
                self.log.warning("No time for a policy!")
                self.policy = dict( (a, '-') for a in policy_ants)
            else:
                res = sim.simulate_combat(t,
                        score_0,
                        score_1,
                        self.log)
                self.policy = sim.get_friend_policy(res) 
                self.log.info("Policy: %s", self.policy)
            self.setup_planner(True)
        else :
            self.log.info("No policy will be calculated!")
            self.log.info("Policy ants: %s", policy_ants)
            self.log.info("Policy enemies: %s", policy_enemies)
            self.setup_planner(True)
            self.policy = {}
       
    def newturn(self):
        super(ExplorerFlock, self).newturn()
       
        self.gather_new_ants()
        self.create_policy()
        self.log.info("Moving all the ants with a policy")
        for ant, d in self.policy.iteritems():
            ant.move_heading(d)

        self.transition_delayed("follow_policy")

    def follow_policy(self):
        ant = self.current_ant
        if ant not in self.policy:
            e_dist = ((self.world.distance(ant.pos,e), e)
                      for e in self.all_enemies)
            e = min(e_dist)[1]
            self.log.info("Ant %s moves towards enemy %s", ant, e)
            ant.move_to(e)

    def __newturn(self):
        """
        Calculates the centroid and grouping of all the ants. This function
        also controls the transitions of the FSM
        """
        # super(ExplorerFlock, self).newturn()
        self.calculate_grouping()
        self.positions_assigned = set()
       	
        in_formation = all(a.pos in self.attack_positions(self.all_enemies) 
                for a in self.controlled_ants)
        if in_formation:
            self.log.info("Ants are in formation, attacking")
            self.setup_planner(False)
            return self.transition_delayed("attack")

        if self.previous_poses == self.current_poses:
            self.log.info("Ants didn't move, stepping out of grouping")
            self.setup_planner(False)
            return self.transition_delayed("attack")
        
        else:
            self.log.info("Moving the ants in formation")
            self.setup_planner(True)
            return self.transition_delayed("formation")
        
        if len(self.all_enemies) > len(self.controlled_ants):
            self.log.info("Too many enemeies, keep formation!")
            self.setup_planner(True)
            return self.transition_delayed("formation")

        #if (self.grouping > self.clustering_std): 
        #    self.log.info("Grouping value %f, time to regroup", self.grouping)
        #    self.setup_planner(True)
        #    return self.transition_delayed("group")

    def check_status(self):
        """
        If the number of controlled ants is less than min_group_size, or the 
        number of enemies in range is 0, then the Aggregator
        dismantles.
        """
        if len(self.controlled_ants) < self.min_group_size:
            self.log.info("No more enough controlled ants")
            return False
        super(ExplorerFlock, self).check_status()
                
        #calculating the distance between the enemies and all the ants
        try:
            r = self.leader.danger_radius + 1
        except AttributeError:
            self.log.error("WTF??")
            return False
        self.all_enemies = set(self.ants_enemies_in_range(r))
        self.log.info("Enemies around: %s", self.all_enemies)
        if len(self.all_enemies) == 0:
            self.log.info("No more enemies in range")
            return False

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
        attack_pos = min( (self.world.distance(self.current_ant.pos, e), e)
                for e in self.all_enemies)[1]

        self.log.info("ant %s attacks towards %s", self.current_ant,
                    attack_pos)
        self.current_ant.move_to(attack_pos)
   
    def formation(self):
        """
        Moves current_ant towards the closest location right outside the enemies
        attack range.
        """
        circle = set(self.attack_positions(self.all_enemies))
        if self.current_ant.pos in circle:
            self.positions_assigned.add(self.current_ant.pos)
            self.log.info("Ant %s is already in formation", self.current_ant)
            return
        
        candidates = sorted((self.world.distance(self.current_ant.pos, p), p)
                for p in circle)
       
        for _, pos in candidates:
            if ((pos not in self.positions_assigned) and 
                    (not pos in (a.pos for a in self.controlled_ants))
                ):
                if self.current_ant.move_to(pos):
                    self.log.info("ant %s in formation to %s", self.current_ant,
                        pos)
                    self.positions_assigned.add(pos)
                    return 
        self.log.error("No free slots for ant %s", self.current_ant)
    
    @staticmethod
    def check_if_grab(ant):
        """
        Return true if it can grab an ant
        """
        if hasattr(ant, "aggregator"):
            return False
        else:
            return True

def create(calling_ant, neighbour_dist, enemies):
    """
    Create a new ExplorerFlock if the number of friendly ants
    whose distance (calculated using the A*) is closer than neighbour_dist.

    Parameters:
    calling_ant: The ant that has requested to form the aggregator.
    neighbour_dist: The max distance from the other ants to add to the
    aggregator.
    enemies: the nearby enemies

    Return:
    True if the Aggregator could be formed, False if no enough ants are nearby.
    """

    bot = calling_ant.bot
    world = calling_ant.world
    num_aggregated = sum(len(aggr.controlled_ants) for aggr in bot.aggregators)
    if num_aggregated > len(bot.ants) / 2:
        calling_ant.log.info("Too many aggregated: %d, number of ants: %d",
                            num_aggregated, len(bot.ants))
        return False

    def dist_criterion(ant):
        return castar.pathdist(ant.pos, calling_ant.pos, neighbour_dist)

    ant_list = set([calling_ant])
    free_ants = (a for a in bot.ants
                    if
                    ExplorerFlock.check_if_grab(a)
                    and
                    dist_criterion(a)
                 )

    def key_fun(ant):
        return world.distance(calling_ant.pos, ant.pos)

    for ant in sorted(free_ants, key = key_fun):
        ant_list.add(ant)
        if len(ant_list) > len(enemies) + 1:
            break
    
    if len(ant_list) <= len(enemies):
        return False
     
    if len(ant_list) >= ExplorerFlock.min_group_size:
        calling_ant.log.info("Creating an aggregator with %d elements", 
                len(ant_list))
        ExplorerFlock(calling_ant, ant_list)
        return True
    else:
        return False

