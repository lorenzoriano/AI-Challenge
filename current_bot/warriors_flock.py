"""
This is a docstring to make pylint happy
"""
import aggregator
import fsm
import castar
import warrior
import defenders_flock
from c_simulator import c_simulator
from math import sqrt

class WarriorsFlock(aggregator.Aggregator, fsm.FSM):
    """
    An Aggregator that tries first to cluster the belonging
    ants, then move them towards the closest enemy hill.

    Only non-aggreagated Warriors will be added to this group. 
    If there are no visible enemy hills the group dibands.
    """

    clustering_std = 1.1
    min_group_size = 0
    max_ants = 10
    min_dist_to_copt = 20

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
        self.attack_pos = None
        self.neighbour_dist = neighbour_dist
        self.world = leader.world
        self.danger_radius = 3 + int(sqrt(self.world.attackradius2))
        self.policy = {}
        self.all_enemies = set()

    def step(self, ant):
        """
        Simply invokes the FSM step method. 
        """
        aggregator.Aggregator.step(self, ant)
        if self.destroyed:
            return
        self.current_ant = ant
        fsm.FSM.step(self)

    def free_non_warriors(self):
        """
        Remove non warriors among the controlled ants.
        """
        for ant in self.controlled_ants.copy():
            if type(ant) is not warrior.Warrior:
                self.log.info("I don't need %s now", ant)
                self.remove_ant(ant)

    def calculate_policy(self):
        """Calculate the policy for all the ants with a close enemy using the
        simulator
        """
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
                score_0 = c_simulator.AggressiveScore(sim,0)
                score_1 = c_simulator.ConservativeScore(sim,1)
            elif len_friends == len_enemies:
                score_0 = c_simulator.AggressiveScore(sim,0)
                score_1 = c_simulator.ConservativeScore(sim,1)
            else:
                score_0 = c_simulator.ConservativeScore(sim,0)
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
        else :
            self.log.info("No policy will be calculated!")
            self.log.info("Policy ants: %s", policy_ants)
            self.log.info("Policy enemies: %s", policy_enemies)
            self.policy = {}


    def newturn(self):
        """
        Add ants to this group. Calculate the policy.
        """
        super(WarriorsFlock, self).newturn()
        bot = self.leader.bot
        self.all_enemies = set(self.ants_enemies_in_range(self.danger_radius))
        self.log.info("Enemies around: %s", self.all_enemies)
        close_enemy = len(self.all_enemies) > 0

        ehill_d = self.world.distance(self.leader.pos, self.attack_pos)

        mhill_l = self.leader.my_hills()
        if len(mhill_l) == 0: #strange things happen with ants_numpy
            mhill_d = 0
        else:
            mhill_d = min(mhill_l)[0]

        #the enemy hill is closer than the home hill
        if (ehill_d < 2*mhill_d):
            self.log.info("The enemy hill is close, copting")
            antlist = bot.ants
        else:
            self.log.info("The enemy hills is not close, not copting")
            antlist = []
        
        copted_ants = (a for a in antlist
                       if self.check_if_grab(a) and 
                       castar.pathdist(self.leader.pos, a.pos, 
                                       self.min_dist_to_copt)
                      )
        
        for ant in copted_ants:
            if len(self.controlled_ants) >= self.max_ants:
                self.log.info("max number of ants reached")
                break
            self.control(ant)

        self.calculate_grouping()
        
        #transitions
        if close_enemy:
            self.calculate_policy()
            self.log.info("Moving all the ants with a policy")
            for ant, d in self.policy.iteritems():
                ant.move_heading(d)
            self.transition_delayed("follow_policy")
            self.setup_planner(True)
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
            self.log.info("No more enemy hills, disbanding!")
            return False            
       
        #here we have discovered enemy hills 
        if self.attack_pos in enemy_hills:
            self.log.info("I already know my target: %s", self.attack_pos)
            return True

        #calculating the distance between the enemy hills and the leader
        hills_dists = [(self.world.distance(self.leader.pos, h), h) 
                for h in enemy_hills]
        self.attack_pos = min(hills_dists)[1]

        return True
    
    def follow_policy(self):
        ant = self.current_ant
        if ant not in self.policy:
            e_dist = ((self.world.distance(ant.pos,e), e)
                      for e in self.all_enemies)
            e = min(e_dist)[1]
            self.log.info("Ant %s moves towards enemy %s", ant, e)
            ant.move_to(e)

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
        if type(getattr(ant, "aggregator", None)) is defenders_flock.DefendersFlock:
            return False
        if type(getattr(ant, "aggregator", None)) is WarriorsFlock:
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
    free_ants = (a for a in bot.ants
                    if WarriorsFlock.check_if_grab(a) and
                    type(a) is warrior.Warrior and
                    castar.pathdist(calling_ant.pos, a.pos, neighbour_dist)
                 )
    for ant in free_ants:
        if len(ant_list) >= WarriorsFlock.max_ants:
            break
        ant_list.add(ant)
    if len(ant_list) < WarriorsFlock.min_group_size:
        return False
    
    WarriorsFlock(calling_ant, ant_list, neighbour_dist)
    return True
