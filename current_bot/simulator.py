from collections import defaultdict
from numpy.random import dirichlet, multinomial
import time
from copy import deepcopy
import numpy as np

AIM = {'-': (0, 0),
       'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1)}

class ConservativeScore(object):
    def __init__(self, simulator, side):
        self.side = side
        self.my_init_ants = simulator.count_owner(self.side)
        self.enemy_init_ants = simulator.count_enemies(self.side)

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

class AggresiveScore(object):
    def __init__(self, simulator, side):
        self.side = side
        self.my_init_ants = simulator.count_owner(self.side)
        self.enemy_init_ants = simulator.count_enemies(self.side)

    def __call__(self, simulator):
        my_final_ants = simulator.count_owner(self.side)
        enemy_final_ants = simulator.count_enemies(self.side)

        delta_my = my_final_ants - self.my_init_ants 
        delta_enemy = enemy_final_ants - self.enemy_init_ants

        if delta_my == 0: #no friend ants died
            if delta_enemy < 0: #too good!
                return 3.0
            else: #I want them burning!
                return 0.0
        elif delta_my > delta_enemy: #still good
            return 1.0 #we killed more
        else:
            return 0.0 #we killed less

class Ant(object):
    def __init__(self, pos, owner):
        self.pos = pos
        self.owner = owner

    def __repr__(self):
        return str(self.pos) + ": " + str(self.owner) + " "

class Simulator(object):
    def __init__(self, map):
        self.map = map
        self.rows = map.shape[0]
        self.cols = map.shape[1]
        self.ants = []
        self.attackradius = 5
        self.movements = {}
        self.next_loc = defaultdict(list)
        self.policy = {}
        self.actions = ('n','s','e','w','-')
        self.friends_mapping = {}

    def create_from_lists(self, friends, enemies):
        for a in friends:
            newa = Ant(a.pos, 0)
            self.friends_mapping[newa] = a
            self.ants.append(newa)

        for e in enemies:
            self.ants.append(Ant(e,1))

    def get_friend_policy(self, policy):
        ret = dict( [ (self.friends_mapping[a], policy[a])
                      for a in self.ant_owner(0) ] )
        return ret

    def distance2(self, loc1, loc2):
        "Calculate the closest squared distance between two locations"
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), self.cols - abs(col1 - col2))
        d_row = min(abs(row1 - row2), self.rows - abs(row1 - row2))
        return d_row**2 + d_col**2
    
    def nearby_ants(self, ant, max_dist, exclude=None):
        enemies = []
        for e in self.ants:
            if e.owner == exclude:
                continue
            #if (ant.pos[0]- e.pos[0])**2 + (ant.pos[1] - e.pos[1])**2 <= max_dist:
            if self.distance2(ant.pos, e.pos) <= max_dist:
                enemies.append(e)
        return enemies

    def allowed_policies(self):
        for ant in self.ants:
            p = [0] * len(self.actions)
            for i,action in enumerate(self.actions):
                mov = AIM[action]
                pos = ((ant.pos[0] + mov[0]) % self.rows, 
                       (ant.pos[1] + mov[1]) % self.cols)
                if self.map[pos] != -4:
                    p[i] = 1
            self.policy[ant] = p

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
        if self.map[newpos] == -4:
            return False
        self.movements[ant] = newpos
        self.next_loc[newpos].append(ant)
        return True
  
    def move_direction(self, ant, d):
        pos = AIM[d]
        newpos = ( (ant.pos[0] + pos[0]) % self.rows, 
                   (ant.pos[1] + pos[1]) % self.cols
                 )
        return self.move_ant(ant, newpos)

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
        return [a for a in self.ants if a.owner == owner]

    def simulate_combat(self, allowed_time,
                        ant_0_scoring = ConservativeScore,
                        ant_1_scoring = ConservativeScore,
                        log = None):
        start = time.time()
        score_0 = ant_0_scoring(self, 0)
        score_1 = ant_1_scoring(self, 1)
        
        self.allowed_policies()
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
                ps = dirichlet(self.policy[ant])
                i = multinomial(1, ps).nonzero()[0][0]
                if not (self.move_direction(ant, self.actions[i])):
                    print "CAZZZ"
                action[ant] = i
                
            killed = self.step_turn()
            for a, p in self.policy.iteritems():
                if a.owner == 0:
                    p[action[a]] += score_0(self)
                else:
                    p[action[a]] += score_1(self)

        for k in killed:
            self.add_ant(k)
        for a,p in init_poses.iteritems():
            a.pos = p
        
        retpolicy = {}
        for a,p in self.policy.iteritems():
            ps = dirichlet(p)
            i = multinomial(1, ps).nonzero()[0][0]
            retpolicy[a] = self.actions[i]
        if log is not None:
            log.info("Number of steps: %d", steps)
        else:
            print "Number of steps: ", steps
        return retpolicy

def test1():
    print "test1"
    map = np.zeros((10,10))
    sim = Simulator(map)
    sim.add_ant(Ant((1,1), 1))
    sim.add_ant(Ant((1,3), 0))
    sim.add_ant(Ant((2,4), 0))
    print "initial: ", sim

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def test2():
    print "test2"
    map = np.zeros((10,10))
    sim = Simulator(map)
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
    map = np.zeros((10,10))
    sim = Simulator(map)
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
    map = np.zeros((10,10))
    sim = Simulator(map)
    sim.add_ant(Ant((1,2), 1))
    sim.add_ant(Ant((1,3), 0))
    sim.add_ant(Ant((1,4), 0))
    print "initial: ", sim

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def test5():
    print "test5"
    map = np.zeros((10,10))
    sim = Simulator(map)
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

def test_ant_cant_move():
    print "test_ant_cant_move"
    map = np.zeros((10,10))
    map[(1,0)] = -4
    map[(-1,0)] = -4
    sim = Simulator(map)
    a1 = Ant((0,0),0)
    sim.add_ant(a1)
    print "initial: ", sim
    
    if sim.move_direction(a1, 's'):
        print "NO WAY!"
    else:
        print "Correct"
    
    if sim.move_direction(a1, 'n'):
        print "NO WAY!"
    else:
        print "Correct"
    
    print "after: ", sim

def calculate_policy():
    print "policy"
    map = np.zeros((10,10))
    map[1,0] = -4
    map[0,1] = -4
    sim = Simulator(map)
    a = Ant((1,1), 1)
    sim.add_ant(a)
    a = Ant((2,0), 1)
    sim.add_ant(a)
    a = Ant((0,4), 0)
    sim.add_ant(a)
    a = Ant((1,4), 0)
    sim.add_ant(a)
    a = Ant((2,4), 0)
    sim.add_ant(a)
    a = Ant((3,4), 0)
    sim.add_ant(a)
    print "initial: ", sim
    
    score_0 = ConservativeScore(sim, 0)
    score_1 = ConservativeScore(sim, 1)
    
    policy = sim.simulate_combat(0.5, 
            score_0.__class__, 
            score_1.__class__)

    #ants = sim.ants
    #policy =  {ants[0]:'-', 
    #           ants[1]:'e', 
    #           ants[2]:'w', 
    #           ants[3]:'w', 
    #           ants[4]:'w',
    #           ants[5]:'w',
    #           } 
    
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
    test_ant_cant_move()
    print
    print
    start = time.time()
    calculate_policy()
    print "Time: ", time.time() - start
