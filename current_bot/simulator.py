from collections import defaultdict
from numpy.random import dirichlet, multinomial
import time
from copy import deepcopy

AIM = {'-': (0, 0),
       'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1)}

class ConservativeScore(object):
    def __init__(self, simulator, side):
        self.init_sim = deepcopy(simulator)
        self.side = side
        self.my_init_ants = self.init_sim.count_owner(self.side)
        self.enemy_init_ants = self.init_sim.count_enemies(self.side)

    def __call__(self, simulator):
        my_final_ants = simulator.count_owner(self.side)
        enemy_final_ants = simulator.count_enemies(self.side)

        delta_my = my_final_ants - self.my_init_ants 
        delta_enemy = enemy_final_ants - self.enemy_init_ants

        if delta_my == 0: #no friend ants died
            if delta_enemy < 0: #too good!
                return 2.0
            else:
                return 1.0
        elif delta_my > delta_enemy: #still good
            return 1.0
        else:
            return 0.0


class Ant(object):
    def __init__(self, pos, owner):
        self.pos = pos
        self.owner = owner

    def __repr__(self):
        return str(self.pos) + ": " + str(self.owner) + " "

class Simulator(object):
    def __init__(self):
        self.ants = []
        self.attackradius = 5
        self.movements = {}
        self.next_loc = defaultdict(list)

    def nearby_ants(self, ant, max_dist, exclude=None):
        enemies = []
        for e in self.ants:
            if e.owner == exclude:
                continue
            if (ant.pos[0]- e.pos[0])**2 + (ant.pos[1] - e.pos[1])**2 <= max_dist:
                enemies.append(e)
        return enemies

    def do_attack_focus(self):
        """ Kill ants which are the most surrounded by enemies

            For a given ant define: Focus = 1/NumOpponents
            An ant's Opponents are enemy ants which are within the attackradius.
            Ant alive if its Focus is greater than Focus of any of his Opponents.
            If an ant dies 1 point is shared equally between its Opponents.
        """
        # maps ants to nearby enemies
        nearby_enemies = {}
        for ant in self.ants:
            nearby_enemies[ant] = self.nearby_ants(ant, 
                                                   self.attackradius, 
                                                   ant.owner)

        # determine which ants to kill
        ants_to_kill = []
        for ant in self.ants:
            # determine this ants weakness (1/focus)
            weakness = len(nearby_enemies[ant])
            # an ant with no enemies nearby can't be attacked
            if weakness == 0:
                continue
            # determine the most focused nearby enemy
            min_enemy_weakness = min(len(nearby_enemies[enemy]) 
                    for enemy in nearby_enemies[ant])
            # ant dies if it is weak as or weaker than an enemy weakness
            if min_enemy_weakness <= weakness:
                ants_to_kill.append(ant)
        
        for ant in ants_to_kill:
            self.kill(ant)

        return ants_to_kill

    def kill(self, ant):
        self.ants.remove(ant)


    def __repr__(self):
        if len(self.ants) == 0:
            return "empty"
        s = ""
        for a in self.ants:
            s += str(a)
        return s

    def add_ant(self, ant):
        self.ants.append(ant)

    def move_ant(self, ant, newpos):
        self.movements[ant] = newpos
        self.next_loc[newpos].append(ant)
  
    def move_direction(self, ant, d):
        pos = AIM[d]
        newpos = ant.pos[0] + pos[0], ant.pos[1] + pos[1]
        self.move_ant(ant, newpos)

    def __really_move(self, ant, newpos):
        ant.pos = newpos

    def finalize_movements(self):
        killed_ants = []
        for loc, ants in self.next_loc.items():
            if len(ants) == 1:
                a = ants[0]
                self.__really_move(a, self.movements[a])
            else:
                for ant in ants:
                    killed_ants.append(ant)
                    self.kill(ant)
        self.next_loc.clear()
        self.movements.clear()
        return killed_ants

    def step_turn(self):
        k1 = self.finalize_movements()
        return k1 + self.do_attack_focus()

    def count_owner(self, owner):
        return sum(1 for a in self.ants if a.owner == owner)
    
    def count_enemies(self, owner):
        return sum(1 for a in self.ants if a.owner != owner)

    def ant_owner(self, owner):
        return (a for a in self.ants if a.owner == owner)

    def simulate_combat(self, allowed_time):
        start = time.time()
        actions = ('n','s','e','w','-')
        print "Actions: ", actions
        policy = {}
        score_0 = ConservativeScore(self, 0)
        score_1 = ConservativeScore(self, 1)
        
        for ant in self.ants:
            policy[ant] = [1.]*len(actions)

        init_poses = dict( (a, a.pos) for a in self.ants)
        
        killed = []
        steps = 0
        while (time.time() - start) < allowed_time:
            steps += 1
            action = {}
            for k in killed:
                self.add_ant(k)
            for a,p in init_poses.iteritems():
                a.pos = p
            
            for ant in self.ants:
                ps = dirichlet(policy[ant])
                i = multinomial(1, ps).nonzero()[0][0]
                self.move_direction(ant, actions[i])
                action[ant] = i
                
            killed = self.step_turn()
            for a, p in policy.iteritems():
                if a.owner == 0:
                    p[action[a]] += score_0(self)
                else:
                    p[action[ant]] += score_1(self)

        print "Steps: ", steps
        for k in killed:
            self.add_ant(k)
        for a,p in init_poses.iteritems():
            a.pos = p
        
        retpolicy = {}
        print "Raw: ", policy
        for a,p in policy.iteritems():
            ps = dirichlet(p)
            i = multinomial(1, ps).nonzero()[0][0]
            retpolicy[a] = actions[i]
        return retpolicy

def test1():
    print "test1"
    sim = Simulator()
    sim.add_ant(Ant((1,1), 1))
    sim.add_ant(Ant((1,3), 0))
    sim.add_ant(Ant((2,4), 0))
    print "initial: ", sim

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def test2():
    print "test2"
    sim = Simulator()
    a1 = Ant((1,0), 0)
    a2 = Ant((0,3), 1)
    sim.add_ant(a1)
    sim.add_ant(a2)
    print "initial: ", sim

    sim.move_ant(a1, (0,0))
    sim.move_ant(a2, (0,3))
    sim.finalize_movements()
    killed = sim.do_attack_focus()
    print "Killed: ", killed
    print "after: ", sim

def test3():
    print "test3"
    sim = Simulator()
    a1 = Ant((1,0), 0)
    a2 = Ant((0,1), 0)
    sim.add_ant(a1)
    sim.add_ant(a2)
    print "initial: ", sim

    sim.move_direction(a1, 'n' )
    sim.move_direction(a2, 'w')
    sim.finalize_movements()
    killed = sim.do_attack_focus()
    print "Killed: ", killed
    print "after: ", sim

def test4():
    print "test4"
    sim = Simulator()
    sim.add_ant(Ant((1,2), 1))
    sim.add_ant(Ant((1,3), 0))
    sim.add_ant(Ant((1,4), 0))
    print "initial: ", sim

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def test5():
    print "test5"
    sim = Simulator()
    a1 = Ant((1,1), 1)
    sim.add_ant(a1)
    a2 = Ant((2,3),0)
    sim.add_ant(a2)
    a3 = Ant((2,4),0)
    sim.add_ant(a3)
    print "initial: ", sim
    
    sim.move_direction(a1,'w')
    sim.move_direction(a2,'-')
    sim.move_direction(a3,'w')

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def calculate_policy():
    print "policy"
    sim = Simulator()
    a1 = Ant((1,1), 1)
    a2 = Ant((2,3), 0)
    a3 = Ant((2,4), 0)
    sim.add_ant(a1)
    sim.add_ant(a2)
    sim.add_ant(a3)
    print "initial: ", sim
    
    score_0 = ConservativeScore(sim,0)
    score_1 = ConservativeScore(sim,1)
    
    policy = sim.simulate_combat(0.1)
    print "initial2: ", sim
    print "policy: ", policy
    
    for a,d in policy.iteritems():
        sim.move_direction(a,d)
    
    print "killed: ", sim.step_turn()
    print "after: ", sim
    print "Score 0: ", score_0(sim)
    print "Score 1: ", score_1(sim)

if __name__ == "__main__":
    test1()
    test2()
    test3()
    test4()
    test5()
    print
    print
    start = time.time()
    calculate_policy()
    print "Time: ", time.time() - start
