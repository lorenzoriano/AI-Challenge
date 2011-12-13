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
    danger_radius = 15

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
   
    def newturn(self):
        """
        Add ants to this group.
        This function changes the state of the whole flock
        """
        super(DefendersFlock, self).newturn()
        copted_ants = (a for a in self.bot.ants
                    if
                    type(getattr(a,'aggregator',None)) is not DefendersFlock
                    and 
                    castar.pathdist(self.myhill, a.pos, self.danger_radius)
                 )
        
        if len(self.controlled_ants) < len(self.close_enemies):
            #TODO this can be nicely done with an iterator
            for ant in copted_ants:
                if len(self.controlled_ants) >= len(self.close_enemies):
                    break
                self.control(ant)
       
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
            score_0 = c_simulator.UltraConservativeScore(sim,0)
            score_1 = c_simulator.AggressiveScore(sim,1)
            t = self.calculate_time_per_policy()
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
            self.setup_planner(True)
            self.policy = {}
        
        self.log.info("Moving all the ants with a policy")
        for ant, d in self.policy.iteritems():
            ant.move_heading(d)

        self.transition_delayed("follow_policy")

    def follow_policy(self):
        ant = self.current_ant
        if ant not in self.policy:
            e_dist = ((self.world.distance(ant.pos,e), e)
                      for e in self.close_enemies)
            e = min(e_dist)[1]
            self.log.info("Ant %s moves towards enemy %s", ant, e)
            ant.move_to(e)


def create(bot, hill, enemies, dispatcher):
    """
    Create a new DefendersFlock made by the len(enemies) ants 
    closer to the enemies.
    """
    def key_func(a):
        f = bot.world.distance
        return min(f(a.pos, e) for e in enemies)

    n = len(enemies)
    ant_list = heapq.nsmallest(n, bot.ants, key_func)
    if len(ant_list):
        return DefendersFlock(ant_list[0], ant_list, hill, dispatcher)
    else:
        return None
        
