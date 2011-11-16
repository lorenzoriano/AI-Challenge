import castar
import aggregator
import pezz_logging
from MyBot import ants
import castar
import logging
import heapq

logger = logging.getLogger("pezzant.aggressive_aggregator")
loglevel = logging.INFO
logger.setLevel(loglevel)
fh = logging.FileHandler("aggressive_aggregator.txt", mode="w")
#fh = logging.StreamHandler(sys.stderr)
fh.setLevel(loglevel)
formatter = logging.Formatter(
                "%(levelname)s "
                "Turn: %(turn)d "
                "%(ant)s - "
                "%(funcName)s:"
                "%(lineno)s >> "
                "%(message)s"
                )
fh.setFormatter(formatter)
logger.addHandler(fh)


class AggressiveAggregator(aggregator.Aggregator):
    """
    Aggrgates ants and move them towards enemies. It dibands
    if no enemies are in sight.
    """
    
    def __init__(self, leader, antlist):
        #logging structure

        self.log = pezz_logging.TurnAdapter(
            logger,
            {"ant":self},
            leader.bot
            )
        super(AggressiveAggregator, self).__init__(leader, antlist)
        self.allocated_slots = set()
        self.leader_moving = False

    def number_friendly_ants(self, ant):
        """
        Returns the number of friendly ants around ant (8-neighbour).
        """
        pos_r = self.leader.pos[0]
        pos_c = self.leader.pos[1]
        world = ant.world
        rows, cols = world.rows, world.cols
        counter = 0
        for dpos in (        (-2,0)
                     (-1,-1),(-1,0),(-1,1), 
               (0,-2)(0,-1),        (0,1), (0,2),
                     (1,-1),(1,0),(1,-1),
                            (2,0)
                     ):

            newloc_r = pos_r + dpos[0]
            newloc_c =  pos_c + dpos[1]
            
            if world.map_value((newloc_r, newloc_c)) == ants.MY_ANT:
                counter += 1
        return counter

    def step(self, ant):
        """
        The leader moves towards an enemy, the other ants try to
        move close to the leader
        """
        
        if ant == self.leader:
            self.log.info("Step for leader %s", ant)
            #only the leader checks for destroy
            r = 1.5 * ant.world.attackradius2
            enemies_list = ant.enemies_in_range(r)
            if self.check_if_destroy(enemies_list):
                self.destroy()
                return
            if self.number_friendly_ants(ant) < 3:
                self.log.info("Too few ants around the leader, waiting")
                self.leader_moving = False
                return
            loc = enemies_list[0][1]
            self.log.info("Moving leader towards enemy at %s", loc)
            ant.move_to(loc)
            self.leader_moving = True
            self.allocated_slots.clear()

        else:
            self.log.info("Step for slave %s", ant)
            d = ant.world.distance(ant.pos, self.leader.pos)
            if d <= 2:
                self.log.info(
                        "Slave %s will move in the same direction as the leader",
                        ant)
                if self.leader_moving:
                    ant.move_heading(self.leader.current_heading)
                else:
                    self.log.info("Unfortunately for slave %s the leader is not moving", 
                                  ant)
                return
            
            #finding an empty slot around the leader
            slots = ([l for l in ((0,0),(0,1),(0,-1), 
                         (1,0),(1,1),(1,-1),
                         (-1,0),(-1,-1),(-1,-1))
                       if l not in self.allocated_slots])
            if len(slots) == 0:
                self.log.info("no slots for slave %s, moving towards the leader", ant)
                ant.move_to(self.leader.pos)
                return
            candidates = []
            for dpos in slots:
                newloc = (self.leader.pos[0]+ dpos[0],
                         self.leader.pos[0] + dpos[1])
                heapq.heappush(candidates, (len(castar.pathfind(ant.pos, newloc)),
                                           newloc, dpos)
                              )
            self.log.info("Candidates for slave %s are %s", ant, candidates)
            for loc in candidates:
                target = loc[1]
                dpos = loc[2]
                if ant.move_to(target):
                    self.log.info("Moving ant %s to %s", ant, target)
                    self.allocated_slots.add(dpos)
                    break
            
    def check_if_destroy(self, enemies_list):
        """
        If the number of enemies close to the leader is zero, or the number 
        of contolled ants is less than 3, the aggregator is destroyed

        Parameters:
        enemies_list: the list of close enemies

        Return:
        True if has to be destroyed, False otherwise
        """
        if len(enemies_list) == 0:
            self.log.info("no more enemies!")
            return True
        elif len(self.controlled_ants) < 3:
            self.log.info("number of controlled ants is less than 3")
            return True
        else:
            return False

def createAggressiveAggregator(calling_ant, neighbour_size, neighbour_dist):
    """
    Create a new AggressiveAggregator if the number of friendly ants
    whose distance (calculated using the A*) is closer than neighbour_dist.

    Parameters:
    calling_ant: The ant that has requested to form the aggregator.
    neighbour_dist: The max distance from the other ants to add to the
    aggregator.
    neighbour_size: The minimum number of ants to aggregate.

    Return:
    True if the Aggregator could be formed, False if less than neighbout_size
    ants are closer than neighbour_dist.
    """
    close_locations = castar.find_near(calling_ant.pos, neighbour_dist)
    ant_list = [calling_ant]
    bot = calling_ant.bot
    
    for loc in close_locations:
        ant = bot.find_ant(loc)
        if ant is None:
            continue
        #don't steal other ants
        if not hasattr(ant, 'aggregator'):
            ant_list.append(ant)
    
    if len(ant_list) >= neighbour_size:
        #create the Aggregator, which will store an instance of itself in each
        #controlled ant
        AggressiveAggregator(calling_ant, ant_list)
        return True
    else:
        return False

