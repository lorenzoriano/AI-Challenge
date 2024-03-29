#!/usr/bin/env python
import ants_numpy as ants
#import ants_orig as ants
Ants = ants.Ants

import castar
#from ants import Ants
import pezz_logging
import logging
import explorer_dispatcher
import warrior_dispatcher
import defender_dispatcher
import mover
from timetracker import TimeTracker

import numpy as np
import time
import sys
import random
import cProfile

logger = logging.getLogger("pezzant")
loglevel = logging.INFO
logger.setLevel(loglevel)
#fh = logging.StreamHandler(sys.stderr)
fh = logging.FileHandler("bot.txt", mode="w")
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
#logger.addHandler(fh)
logger.addHandler(logging.NullHandler())

#profiler = cProfile.Profile()
profiler = None

class PezzBot:
    def __init__(self):
        self.ants = []
        self.world = None
        self.turn = 0
        
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"Bot"},
                self
                )
        self.enemy_hills = set()
        self.aggregators = set()
        self.executed_aggregators = 0
        self.postloop_time = 10.
        self.average_ant_time = 0.5
        self.executed_ants = 0
        self.aggregators_times = []

        self.explored_map = None
        self.prev_visible = -1
        
    # do_setup is run once at the start of the game
    # after the bot has received the game settings
    # the ants class is created and setup by the Ants.run method
    def do_setup(self, world):
        self.log.info("Setup")
        self.world = world
        self.explorer_dispatcher = explorer_dispatcher.ExplorerDispatcher(
                world, self)
        self.warrior_dispatcher = warrior_dispatcher.WarriorDispatcher(
                world, self)
        self.defender_dispatcher = defender_dispatcher.DefenderDispatcher(
                world, self)

        self.dispatchers = [self.explorer_dispatcher,
                            self.warrior_dispatcher,
                            self.defender_dispatcher]
        self.mover = mover.Mover(world, self)

        self.ants_tracker = TimeTracker(0)
        self.preloop_tracker = TimeTracker(0)
        self.postloop_tracker = TimeTracker(0)
        castar.setup(world.map, world)

        self.explored_map = np.zeros(world.map.shape, dtype = np.bool)

    def iterate_ants_loc(self):
        """
        An iterator that returns all the ants location    
        """
        for ant in self.ants:
            yield ant.pos

    def update_ants(self):
        """
        Create new ants if necessary. Every dispatcher is queried
        with a probability, and enough ants are sampled.
        """
        #TODO change so that it iterates only on the friend hills
        new_ant_loc = (ant_loc for ant_loc in self.world.my_ants()
                        if ant_loc not in self.iterate_ants_loc())
        

        for loc in new_ant_loc:
            probs = np.array([d.spawn_likelyhood() 
                                for d in self.dispatchers])
            probs /= np.sum(probs)
            self.log.info("The probs are: %s", probs)
            i = np.random.multinomial(1, probs).nonzero()[0][0]
            creator = self.dispatchers[i]
            
            newant = creator.create_ant(loc)
            if newant is not None:
                self.ants.append(newant)
            else:
                self.log.warning("How come nobody wants to create?")
                newant = self.explorer_dispatcher.create_ant(loc)
                self.ants.append(newant)

    def find_ant(self, loc):
        """
        Finds an Ant at a specific location.
        
        Parameters:
        loc: a (row,col) tuple
    
        Return:
        The Ant if it is found, None otherwise
    
        """
        if self.world.map_value(loc) != ants.MY_ANT:
            return None
        for ant in self.ants:
            if ant.pos == loc:
                return ant
        return None

    def add_aggregator(self, aggr):
        self.aggregators.add(aggr)

    def remove_aggregator(self, aggr):
        self.aggregators.discard(aggr)

    def unseen(self):
        unseen_arr = np.logical_not(self.explored_map)
        locs_arr = np.transpose(unseen_arr.nonzero())
        return locs_arr

    def mark_unreachable(self, pos):
        self.log.info("Marking pos %s as unreachable", pos)
        self.explored_map[pos] = True
        self.world.map[pos] = ants.WATER

    # do turn is run once per turn
    def do_turn(self, world):
        self.preloop_tracker.tick()
        self.log.info("----------")
        self.log.info("Start turn")
        
        self.explored_map = np.logical_or(self.explored_map,
                                           self.world.visible)
        visible =  self.explored_map.sum()
        if visible != self.prev_visible:
            self.log.info("The world has changed, let's update astar")
            castar.setup(world.map, world)
        
        self.prev_visible = visible
        self.turn += 1
        self.executed_aggregators = 0
        self.executed_ants = 0
        self.aggregators_times = []

        #adding enemy hills
        for hill_loc, hill_owner in world.enemy_hills():
            self.enemy_hills.add(hill_loc)
        #removing razed hills
        for hill in self.enemy_hills.copy():
            if world.visible[hill[0], hill[1]]:
                if hill not in world.hill_list:
                    self.log.info("Removing hill at %s", hill)
                    self.enemy_hills.remove(hill)

        #removing dead_ants
        for ant in self.ants[:]:
            if not ant.check_status():
                self.ants.remove(ant)
                for d in self.dispatchers:
                    d.remove_ant(ant)

        self.explorer_dispatcher.step()

        #adding newborn ants
        self.update_ants()

        #the defender wants to know who's alive
        self.defender_dispatcher.step()

        #now is time to update the mover
        self.mover.update(self.ants)

        iter_ants = self.ants[:]
        random.shuffle(iter_ants)
        preloop_time = self.preloop_tracker.tock()
        ants_time = 0.
        self.ants_tracker.tick()
        for ant in iter_ants:
            ant.step()
            
            self.executed_ants += 1
            
            if world.time_remaining() < 2*self.postloop_time:
                self.log.warning("Timeout incoming, bail out!")
                break

            self.log.info("Time remaining: %f", world.time_remaining())
        
        ants_time += self.ants_tracker.tock() - sum(self.aggregators_times)
        if ants_time <= 0:
            ants_time = 1.0
        self.postloop_tracker.tick()
        self.mover.finalize()
        if profiler is not None and self.turn == 300:
            profiler.dump_stats("profiler.prof")
            sys.exit()

        
        self.log.info("number of my hills: %d", len(self.world.my_hills()))
        self.log.info("number of enemy hills: %d", len(self.enemy_hills))
        self.log.info("number of enemy hills (world): %d", 
                len(world.enemy_hills()))
        self.log.info("number of explorer: %d", len(self.explorer_dispatcher.ants))
        self.log.info("number of warrior: %d", len(self.warrior_dispatcher.ants))
        
        postloop_time = self.postloop_tracker.tock()
        
        self.ants_tracker.reset()
        self.preloop_tracker.reset()
        self.postloop_tracker.reset()

        self.postloop_time = (0.5 * max(self.postloop_time, postloop_time)
                              + 0.5 * postloop_time)
        self.average_ant_time = ants_time / len(self.ants)
        if self.average_ant_time < 0:
            self.log.error("Time %f can't be < 0!", self.average_ant_time)
            self.average_ant_time = 0
        
        self.log.info("Preloop average time: %f", preloop_time)
        self.log.info("Ants single time: %f", self.average_ant_time)
        self.log.info("Avg postloop time: %f", self.postloop_time)
        self.log.info("Aggregators time: %s", self.aggregators_times)
        self.log.info("Time remaining: %f", world.time_remaining())


def main():
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        Ants.run(PezzBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')

if __name__ == '__main__':
    if profiler is not None:
        profiler.runctx("main()", globals(), locals())
    else:
        main()

