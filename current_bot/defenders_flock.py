import aggregator
import fsm
import castar
import heapq
import MyBot
ants = MyBot.ants
from c_simulator import c_simulator


class DefendersFlock(aggregator.Aggregator, fsm.FSM):
    """
    A DefendersFlock will be created whenever an hill is threatened by enemies.
    It will grab ants from the surrounding to defend the hill.
    """
    clustering_std = 1.0
    danger_radius = 10

    def __init__(self, leader, antlist, myhill, dispatcher):
        aggregator.Aggregator.__init__(self, leader, antlist)
        fsm.FSM.__init__(self, "follow_policy")
        self.myhill = myhill
        self.dispatcher = dispatcher
        self.close_enemies = []
        self.policy = {}
        self.current_ant = None
      
    def destroy(self):
        self.dispatcher.remove_hill(self.myhill)
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
        self.close_enemies = self.enemies_in_range()
        if len(self.close_enemies):
            return True
        else:
            return False

    def enemies_in_range(self):
        """
        Returns a list of all the enemies whose distance from the hill is
        less than self.danger_radius.
        """

        enemies = list( e[0] for e in self.world.enemy_ants()
                        if castar.pathdist(e[0], self.myhill, 
                            self.danger_radius))
        return enemies
 
    def free_ants(self):
        """
        Remove too far ants
        """
        far_aways = (a for a in self.controlled_ants.copy() 
            if castar.pathlen(a.pos, self.myhill) > self.danger_radius)
        for ant in far_aways:
            if len(self.controlled_ants) == 1:
                break
            self.remove_ant(ant)

    def gather_new_ants(self):
        """
        Gathers new ants around the hill
        """
        coptable_ants = (a for a in self.bot.ants
                        if
                        type(getattr(a,'aggregator',None)) is not DefendersFlock
                        )
        
        def key_func(a):
            return self.world.distance(a.pos, self.myhill)
        
        n = len(self.close_enemies) + 1 - len(self.controlled_ants)

        if n > 0:
            self.log.info("I need %d more ants", n)
            ant_list = heapq.nsmallest(n, coptable_ants, key_func)
            for ant in ant_list:
                self.control(ant)
        
        coptable_ants = (a for a in self.bot.ants
                        if
                        (type(getattr(a,'aggregator',None)) is not DefendersFlock)
                        and
                        (self.world.distance(a.pos,self.myhill) <= 4)
                        )
        for ant in coptable_ants:
            self.log.info("Taking close ant %s", ant)
            self.control(ant)

    def create_policy(self):
        """
        Calculate the policy for all the ants in danger
        """
        sim = c_simulator.Simulator(self.world.map)
        policy_ants = set(a for a in self.controlled_ants 
                if any(self.can_attack(a.pos,e) for e in self.close_enemies) )
        policy_enemies = set(e for e in self.close_enemies 
                if any(self.can_attack(a.pos,e) for a in policy_ants) )
        len_friends = len(policy_ants)
        len_enemies = len(policy_enemies)
        if ((len_friends>0) and (len_enemies)>0):
            self.log.info("Policy ants: %s", policy_ants)
            self.log.info("Policy enemies: %s", policy_enemies)
            sim.create_from_lists(policy_ants, policy_enemies)
            score_0 = c_simulator.AggressiveScore(sim,0)
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
            self.policy = {}
            self.setup_planner(True)


    def newturn(self):
        """
        Add ants to this group.
        This function changes the state of the whole flock
        """
        super(DefendersFlock, self).newturn()
        self.log.info("My ants are %s", self.controlled_ants) 
        self.free_ants()
        self.gather_new_ants()
        self.create_policy()
        self.log.info("After changes my ants are %s", self.controlled_ants) 
                
        self.log.info("Moving all the ants with a policy")
        for ant, d in self.policy.iteritems():
            ant.move_heading(d)

        self.transition_delayed("follow_policy")

    def follow_policy(self):
        ant = self.current_ant
        if ant not in self.policy:
            e_dist = ((castar.pathlen(e, self.myhill),e)
                      for e in self.close_enemies)
            e = min(e_dist)[1]
            self.log.info("Ant %s moves towards enemy %s", ant, e)
            ant.move_to(e)
        else:
            self.log.info("Ant %s already did a policy move", ant)


def create(bot, hill, enemies, dispatcher):
    """
    Create a new DefendersFlock made by the len(enemies) ants 
    closer to the enemies.
    """
    def key_func(a):
        f = bot.world.distance
        return min(f(a.pos, e) for e in enemies)

    n = len(enemies) + 1
    ant_list = heapq.nsmallest(n, bot.ants, key_func)
    if len(ant_list):
        return DefendersFlock(ant_list[0], ant_list, hill, dispatcher)
    else:
        return None
        
