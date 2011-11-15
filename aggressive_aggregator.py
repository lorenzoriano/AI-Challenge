import castar
import aggregator
import pezz_logging
from MyBot import ants

import logging
logger = logging.getLogger("pezzant.aggressive_aggregator")
loglevel = logging.INFO
logger.setLevel(loglevel)
fh = logging.FileHandler("bot.txt", mode="w")
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

    def number_friendly_ants(self, ant):
        """
        Returns the number of friendly ants around ant.
        """
        pos_r = self.leader.pos[0]
        pos_c = self.leader.pos[1]
        map = ant.world.map
        rows, cols = map.shape
        counter = 0
        for dpos in ((0,0),(0,1),(0,-1), 
                     (1,0),(1,1),(1,-1),
                     (-1,0),(-1,-1),(-1,-1)):

            newloc_r = pos_r + dpos[0]
            if newloc_r >= rows:
                newloc_r = newloc_r - rows
            if newloc_r < 0:
                newloc_r = newloc_r + rows
            newloc_c =  pos_c + dpos[1]
            if newloc_c >= cols:
                newloc_c = newloc_c - cols
            if newloc_c < 0:
                newloc_c = newloc_c + cols
            
            if map[newloc_r, newloc_c] == ants.MY_ANT:
                counter += 1
        return counter

    def step(self, ant):
        """
        The leader moves towards an enemy, the other ants try to
        move close to the leader
        """
        self.log.info("Step for ant %s", ant)
        if ant == self.leader:
            #only the leader checks for destroy
            r = 1.5 * ant.world.attackradius2
            enemies_list = ant.enemies_in_range(r)
            if self.check_if_destroy(enemies_list):
                self.destroy()
                return
            if self.number_friendly_ants(ant) < 2:
                self.log.info("Too few ants around the leader, waiting")
                return
            loc = enemies_list[0][1]
            self.log.info("Moving leader towards enemy at %s", loc)
            ant.move_to(loc)
        else:
            target_r = self.leader.pos[0]
            target_c = self.leader.pos[1]
            d = ant.world.distance(ant.pos, self.leader.pos)
            if d == 1:
                self.log.info(
                        "Ant %s will move in the same direction as the leader",
                        ant)
                ant.move_heading(self.leader.current_heading)
                return
            
            for dpos in ((0,0),(0,1),(0,-1), 
                         (1,0),(1,1),(1,-1),
                         (-1,0),(-1,-1),(-1,-1)):
               newloc = (target_r + dpos[0],
                         target_c + dpos[1])
               if ant.move_to(newloc):
                   break
            self.log.info("Moving ant %s to %s", ant, newloc)
            
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

