import c_simulator
import numpy as np
from collections import defaultdict

MAP_OBJECT = '?%*.!'
FOOD = -3
WATER = -4
LAND = -2

def parse_map(map_file):
    """ Parse the map_text into a more friendly data structure """
    with open(map_file, "r") as f:
        map_text = f.read()
    ant_list = None
    hill_list = []
    hill_count = defaultdict(int)
    width = height = None
    water = []
    food = []
    ants = defaultdict(list)
    hills = defaultdict(list)
    row = 0
    score = None
    hive = None
    num_players = None

    for line in map_text.split('\n'):
        line = line.strip()

        # ignore blank lines and comments
        if not line or line[0] == '#':
            continue

        key, value = line.split(' ', 1)
        key = key.lower()
        if key == 'cols':
            width = int(value)
        elif key == 'rows':
            height = int(value)
        elif key == 'players':
            num_players = int(value)
            if num_players < 2 or num_players > 10:
                raise Exception("map",
                                "player count must be between 2 and 10")
        elif key == 'score':
            score = list(map(int, value.split()))
        elif key == 'hive':
            hive = list(map(int, value.split()))
        elif key == 'm':
            if ant_list is None:
                if num_players is None:
                    raise Exception("map",
                                    "players count expected before map lines")
                ant_list = [chr(97 + i) for i in range(num_players)]
                hill_list = list(map(str, range(num_players)))
                hill_ant = [chr(65 + i) for i in range(num_players)]
            if len(value) != width:
                raise Exception("map",
                                "Incorrect number of cols in row %s. "
                                "Got %s, expected %s."
                                %(row, len(value), width))
            for col, c in enumerate(value):
                if c in ant_list:
                    ants[ant_list.index(c)].append((row,col))
                elif c in hill_list:
                    hills[hill_list.index(c)].append((row,col))
                    hill_count[hill_list.index(c)] += 1
                elif c in hill_ant:
                    ants[hill_ant.index(c)].append((row,col))
                    hills[hill_ant.index(c)].append((row,col))
                    hill_count[hill_ant.index(c)] += 1
                elif c == MAP_OBJECT[FOOD]:
                    food.append((row,col))
                elif c == MAP_OBJECT[WATER]:
                    water.append((row,col))
                elif c != MAP_OBJECT[LAND]:
                    raise Exception("map",
                                    "Invalid character in map: %s" % c)
            row += 1

    if score and len(score) != num_players:
        raise Exception("map",
                        "Incorrect score count.  Expected %s, got %s"
                        % (num_players, len(score)))
    if hive and len(hive) != num_players:
        raise Exception("map",
                        "Incorrect score count.  Expected %s, got %s"
                        % (num_players, len(score)))

    if height != row:
        raise Exception("map",
                        "Incorrect number of rows.  Expected %s, got %s"
                        % (height, row))

    return {
        'size':        (height, width),
        'num_players': num_players,
        'hills':       hills,
        'ants':        ants,
        'food':        food,
        'water':       water
    }

    
def main():
    res = parse_map("/home/pezzotto/AI-Challenge/tools/maps/random_walk/random_walk_03p_02.map")

    map = np.zeros(res["size"], dtype=np.int8)
    for pos in res["water"]:
        map[pos] = -4
    
    sim = c_simulator.Simulator(map)

    a = c_simulator.Ant(58,24,1)
    sim.py_add_ant(a)
    a = c_simulator.Ant(73,17,1)
    sim.py_add_ant(a)

    a = c_simulator.Ant(61,24,0)
    sim.py_add_ant(a)
    a = c_simulator.Ant(72,21,0)
    sim.py_add_ant(a)
    a = c_simulator.Ant(60,26,0)
    sim.py_add_ant(a)

    print "initial: ", sim
        
    score_0 = c_simulator.ConservativeScore(sim, 0)
    score_1 = c_simulator.ConservativeScore(sim, 1)

    #policy = sim.simulate_combat(10.0, 
    policy = sim.simulate_combat(0.170383, 
            score_0, 
            score_1)

    print "policy: ", policy

    for a,d in policy.iteritems():
        sim.py_move_direction(a,d)

    print "killed: ", sim.py_step_turn()
    print "after: ", sim
    print "Score 0: ", score_0.py_call(sim)
    print "Score 1: ", score_1.py_call(sim)

if __name__ == "__main__":
    main()
