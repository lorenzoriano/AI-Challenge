# cython: profile=False
from collections import defaultdict
import time

import numpy as np
cimport numpy as np
cimport cython

dirichlet = np.random.dirichlet
multinomial = np.random.multinomial

cdef dict AIM = {'-': (0, 0),
       'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1)}

cdef class Simulator

cdef class Score:
    cdef float call(self, Simulator simulator):
        raise NotImplementedError
        return 0.0


cdef class ConservativeScore(Score):
    cdef int side
    cdef int my_init_ants
    cdef int enemy_init_ants

    def __init__(self, Simulator simulator, int side):
        self.side = side
        self.my_init_ants = simulator.count_owner(self.side)
        self.enemy_init_ants = simulator.count_enemies(self.side)

    def py_call(self, Simulator simulator):
        return self.call(simulator)
    
    cdef float call(self, Simulator simulator):

        cdef int my_final_ants = simulator.count_owner(self.side)
        cdef int enemy_final_ants = simulator.count_enemies(self.side)

        cdef int delta_my = my_final_ants - self.my_init_ants 
        cdef int delta_enemy = enemy_final_ants - self.enemy_init_ants

        if delta_my == 0: #no friend ants died
            if delta_enemy < 0: #too good!
                return 2.0
            else:
                return 1.0
        elif delta_my >= delta_enemy: #still good
            return 1.0
        else:
            return 0.0

cdef class UltraConservativeScore(Score):
    cdef int side
    cdef int my_init_ants
    cdef int enemy_init_ants

    def __init__(self, Simulator simulator, int side):
        self.side = side
        self.my_init_ants = simulator.count_owner(self.side)
        self.enemy_init_ants = simulator.count_enemies(self.side)

    def py_call(self, Simulator simulator):
        return self.call(simulator)
    
    cdef float call(self, Simulator simulator):

        cdef int my_final_ants = simulator.count_owner(self.side)
        cdef int enemy_final_ants = simulator.count_enemies(self.side)

        cdef int delta_my = my_final_ants - self.my_init_ants 
        cdef int delta_enemy = enemy_final_ants - self.enemy_init_ants

        if delta_my == 0: #no friend ants died
            return 1.0 #really conservative
            if delta_enemy < 0: #too good!
                return 1.0
            else:
                return 1.0
        else: #I don't want to loose good guys
            return 0.0

cdef class AggressiveScore(Score):
    cdef int side
    cdef int my_init_ants
    cdef int enemy_init_ants
    def __init__(self, Simulator simulator, int side):
        self.side = side
        self.my_init_ants = simulator.count_owner(self.side)
        self.enemy_init_ants = simulator.count_enemies(self.side)

    def py_call(self, Simulator simulator):
        return self.call(simulator)
    
    cdef float call(self, Simulator simulator):
        cdef int my_final_ants = simulator.count_owner(self.side)
        cdef int enemy_final_ants = simulator.count_enemies(self.side)

        cdef int delta_my = my_final_ants - self.my_init_ants 
        cdef int delta_enemy = enemy_final_ants - self.enemy_init_ants

        if delta_my == 0: #no friend ants died
            if delta_enemy < 0: #too good!
                return 3.0
            else: #I want them burning!
                return 0.0
        elif delta_my >= delta_enemy: #still good
            return 1.0 #we killed more or equal
        else:
            return 0.0 #we killed less

cdef class _Ant:
    #TODO change pos in two integers
    cdef int i, j
    cdef int owner
    def __init__(self):
        raise TypeError("This class cannot be instantiated from Python")

    def __repr__(self):
        return str((self.i,self.j)) + ": " + str(self.owner) + " "

    cdef copy(self):
        return 

cpdef _Ant Ant(int i, int j, int owner):
    cdef _Ant instance = _Ant.__new__(_Ant)
    instance.i = i
    instance.j = j
    instance.owner = owner
    return instance

cdef inline int int_max(int a, int b): return a if a >= b else b
cdef inline int int_min(int a, int b): return a if a <= b else b
cdef inline int int_abs(int a): return a if a >= 0  else -a

cdef inline double double_max(double a, double b): return a if a >= b else b

cdef class Simulator:
    #TODO Change two lists of ANTS: enemies and friends

    cdef int rows, cols, attackradius
    cdef list ants 
    cdef dict movements, next_loc, policy, friends_mapping
    cdef tuple actions
    cdef object map

    def __init__(self, np.ndarray[np.int8_t, ndim=2, mode="c"] map not None):
        self.map = map
        self.rows = map.shape[0]
        self.cols = map.shape[1]
        self.ants = []
        self.attackradius = 5
        self.movements = {}
        self.next_loc = {}
        self.policy = {}
        self.actions = ('n','s','e','w','-')
        self.friends_mapping = {}

    def create_from_lists(self, object friends, object enemies):
        cdef _Ant newa
        cdef tuple e
        for a in friends:
            newa = Ant(a.pos[0], a.pos[1], 0)
            self.friends_mapping[newa] = a
            self.ants.append(newa)

        for e in enemies:
            self.ants.append(Ant(e[0], e[1], 1))

    cpdef get_friend_policy(self, dict policy):
        cdef dict ret = dict( [ (self.friends_mapping[a], policy[a])
                      for a in self.ant_owner(0)] )
        return ret

    cdef inline int distance2(self, int row1, int col1, int row2, int col2 ):
        "Calculate the closest squared distance between two locations"
        cdef int d_col = int_min(int_abs(col1 - col2), 
                                 self.cols - int_abs(col1 - col2))
        cdef int d_row = int_min(int_abs(row1 - row2), 
                                 self.rows - int_abs(row1 - row2))
        return d_row*d_row + d_col*d_col
    
    cdef list nearby_ants(self, _Ant ant, int max_dist, int exclude):
        cdef _Ant e
        return [ e for e in self.ants if (e.owner != exclude) and
                    self.distance2(ant.i, ant.j, e.i, e.j) <= max_dist
               ]
    
    cdef void allowed_policies(self):
        cdef _Ant ant
        cdef list p
        cdef int i
        cdef tuple mov
        cdef np.ndarray[np.int8_t, ndim=2, mode="c"] map = self.map
        cdef int r, c
        cdef int mov_r, mov_c

        for ant in self.ants:
            p = [0,0,0,0,0]
            for i,action in enumerate(self.actions):
                mov = AIM[action]
                mov_r, mov_c = mov        
                r = (ant.i + mov_r) % self.rows 
                c = (ant.j + mov_c) % self.cols
                if map[r,c] != -4:
                    p[i] = 1
            self.policy[ant] = p
    
    cdef int min_weakness(self, list this_nearby_enemies, dict nearby_enemies):
        cdef int m = 1000
        cdef int l

        for enemy in this_nearby_enemies:
            l = len(nearby_enemies[enemy])
            if l < m:
                m = l
        return m

    cdef list do_attack_focus(self):
        # maps ants to nearby enemies
        cdef dict nearby_enemies = {}
        cdef _Ant ant
        cdef list ants_to_kill
        cdef int weakness
        cdef _Ant enemy
        cdef int min_enemy_weakness 
    
        for ant in self.ants:
            nearby_enemies[ant] = self.nearby_ants(ant, 
                                                   self.attackradius, 
                                                   ant.owner)

        # determine which ants to kill
        ants_to_kill = []
        cdef list this_nearby_enemies
        for ant in self.ants:
            weakness = len(nearby_enemies[ant])
            # an ant with no enemies nearby can't be attacked
            if weakness == 0:
                continue
            this_nearby_enemies = nearby_enemies[ant]
            #min_enemy_weakness = min([len(nearby_enemies[enemy]) 
            #        for enemy in this_nearby_enemies])
            min_enemy_weakness = self.min_weakness(this_nearby_enemies,
                                                   nearby_enemies)

            # ant dies if it is weak as or weaker than an enemy weakness
            if min_enemy_weakness <= weakness:
                ants_to_kill.append(ant)
        
        for ant in ants_to_kill:
            self.kill(ant)

        return ants_to_kill

    cdef void kill(self, _Ant ant):
        self.ants.remove(ant)


    def __repr__(self):
        if len(self.ants) == 0:
            return "empty"
        s = ""
        for a in self.ants:
            s += str(a)
        return s

    cdef void add_ant(self, _Ant ant):
        self.ants.append(ant)
    
    def  py_add_ant(self, _Ant ant):
        self.ants.append(ant)

    def py_move_ant(self, _Ant ant, tuple newpos):
        return self.move_ant(ant, newpos)

    cdef int move_ant(self, _Ant ant, tuple newpos):
#        cdef np.ndarray[np.int_t, ndim=2, mode="c"] array = self.map
        cdef int mapvalue = self.map[newpos]
        if  mapvalue == -4:
            return 0
        self.movements[ant] = newpos
        if newpos in self.next_loc:
            self.next_loc[newpos].append(ant)
        else:
            self.next_loc[newpos] = [ant]
        return 1
 
    def py_move_direction(self, _Ant ant, str d):
        return self.move_direction(ant, d)

    cdef int move_direction(self, _Ant ant, str d):
        cdef tuple pos = AIM[d]
        cdef int i, j
        i, j = pos
        cdef tuple newpos = ( (ant.i + i) % self.rows, 
                   (ant.j + j) % self.cols
                 )
        return self.move_ant(ant, newpos)

    cdef inline void __really_move(self, _Ant ant, int i, int j):
        ant.i = i
        ant.j = j

    cdef list finalize_movements(self):
        cdef list killed_ants = []
        cdef list ants
        cdef tuple loc
        cdef _Ant a
        cdef int i,j
        
        for loc, ants in self.next_loc.items():
            if len(ants) == 1:
                a = ants[0]
                i, j = self.movements[a]
                self.__really_move(a, i, j)
            else:
                for ant in ants:
                    killed_ants.append(ant)
                    self.kill(ant)
        self.next_loc.clear()
        self.movements.clear()
        return killed_ants

    cdef list step_turn(self):
        cdef list k1 = self.finalize_movements()
        k1.extend(self.do_attack_focus())
        return k1

    def py_step_turn(self):
        return self.step_turn()

    cdef int count_owner(self, int owner):
        cdef _Ant a
        cdef int s = 0
        for a in self.ants:
            if a.owner == owner:
                s += 1
        return s

    cdef int count_enemies(self, int owner):
        cdef _Ant a
        cdef int s = 0
        for a in self.ants:
            if a.owner != owner:
                s += 1
        return s

    cdef list ant_owner(self, int owner):
        cdef _Ant a
        return [a for a in self.ants if a.owner == owner]
    
    def simulate_combat(self, double allowed_time,
                        Score score_0,
                        Score score_1,
                        log = None):
        cdef object time_fn = time.time
        cdef double start = time_fn()

        self.allowed_policies()

        cdef _Ant a
        cdef dict init_poses = dict( (a, (a.i, a.j)) for a in self.ants)
        
        cdef list killed = []
        cdef int steps = 0

        cdef dict action
        cdef _Ant k
        cdef tuple p
        cdef _Ant ant

        cdef object ps
        cdef list pol
        cdef double curr_time 

        
        cdef unsigned infor_index
        cdef double infor_score_val
        cdef double infor_pol_val
        while True:
            curr_time = time_fn()
            if (curr_time - start) >= allowed_time:
                break
            
            
            steps += 1
            action = {}
            #TODO this can be optimized
            for k in killed:
                self.add_ant(k)
            for a,p in init_poses.iteritems():
                a.i, a.j = p
            
            
            for ant in self.ants:
                ps = dirichlet(self.policy[ant])
                i = multinomial(1, ps).nonzero()[0][0]
                if not (self.move_direction(ant, self.actions[i])):
                    #this shouldn't happen, default to no move
                    action[ant] = 4
                else:
                    action[ant] = i
                
            killed = self.step_turn()
            for a, pol in self.policy.iteritems():
                
                #if a.owner == 0:
                #    infor_score_val = score_0.call(self)
                #else:
                #    infor_score_val = score_1.call(self)

                #infor_index = action[a]
                #infor_pol_val = pol[infor_index]
                #pol[infor_index] = double_max(infor_pol_val + infor_score_val,
                #                              1.0
                #                              )
                
                if a.owner == 0:
                    pol[action[a]] += score_0.call(self)
                else:
                    pol[action[a]] += score_1.call(self)

        for k in killed:
            self.add_ant(k)
        for a,p in init_poses.iteritems():
            a.i, a.j = p
        
        cdef dict retpolicy = {}
        cdef int m = 0
        cdef int index 
        cdef int val
        cdef int p_index = 0
        for a, pol in self.policy.iteritems():
            #ps = dirichlet(pol)
            #i = multinomial(1, ps).nonzero()[0][0]
           
            m = 0
            p_index = 0
            for index in range(5):
                val = pol[index]
                if val > m:
                    m = val
                    p_index = index

            retpolicy[a] = self.actions[p_index]
        if log is not None:
            log.info("Number of steps: %d", steps)
            #log.info("Raw policy: %s", self.policy)
        else:
            print "Number of steps: ", steps
            print "Raw policy: ", self.policy
        return retpolicy

def test1():
    print "test1"
    map = np.zeros((10,10), dtype=np.int8)
    print map.dtype
    sim = Simulator(map)
    sim.add_ant(Ant(1,1, 1))
    sim.add_ant(Ant(1,3, 0))
    sim.add_ant(Ant(2,4, 0))
    print "initial: ", sim

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def test2():
    print "test2"
    map = np.zeros((10,10), dtype = np.int8)
    sim = Simulator(map)
    a1 = Ant( 1,0 , 0)
    a2 = Ant( 0,3 , 1)
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
    map = np.zeros((10,10), dtype=np.int8)
    sim = Simulator(map)
    a1 = Ant(1,0, 0)
    a2 = Ant(0,1, 0)
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
    map = np.zeros((10,10), dtype=np.int8)
    sim = Simulator(map)
    sim.add_ant(Ant(1,2, 1))
    sim.add_ant(Ant(1,3, 0))
    sim.add_ant(Ant(1,4, 0))
    print "initial: ", sim

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def test5():
    print "test5"
    map = np.zeros((10,10), dtype=np.int8)
    sim = Simulator(map)
    a1 = Ant(1,1, 1)
    sim.add_ant(a1)
    a2 = Ant(2,3,0)
    sim.add_ant(a2)
    a3 = Ant(2,4,0)
    sim.add_ant(a3)
    print "initial: ", sim
    
    sim.move_direction(a1,'w')
    sim.move_direction(a2,'-')
    sim.move_direction(a3,'w')

    print "Killed: ", sim.step_turn() 
    print "after: ", sim

def test_ant_cant_move():
    print "test_ant_cant_move"
    map = np.zeros((10,10), dtype=np.int8)
    map[(1,0)] = -4
    map[(-1,0)] = -4
    sim = Simulator(map)
    a1 = Ant(0,0,0)
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
    map = np.zeros((10,10), dtype=np.int8)
    map[1,0] = -4
    map[0,1] = -4
    sim = Simulator(map)
    a = Ant(1,1, 1)
    sim.add_ant(a)
    a = Ant(2,0, 1)
    sim.add_ant(a)
    a = Ant(0,4, 0)
    sim.add_ant(a)
    a = Ant(1,4, 0)
    sim.add_ant(a)
    a = Ant(2,4, 0)
    sim.add_ant(a)
    a = Ant(3,4, 0)
    sim.add_ant(a)
    print "initial: ", sim
    
    score_0 = AggressiveScore(sim, 0)
    score_1 = ConservativeScore(sim, 1)
    
    policy = sim.simulate_combat(0.03, 
            score_0, 
            score_1)

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
    print "Score 0: ", score_0.call(sim)
    print "Score 1: ", score_1.call(sim)

def main():
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

if __name__ == "__main__":
    main()
