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
import mover
from timetracker import TimeTracker

import numpy as np
import time
import sys
import random
import cProfile
import signal

logger = logging.getLogger("pezzant.MyBot")
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
logger.addHandler(fh)

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
        self.unseen = set()
        
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

        self.dispatchers = [self.explorer_dispatcher,
                            self.warrior_dispatcher]
        self.mover = mover.Mover(world, self)

        self.unseen = set( (r,c) for r in xrange(world.rows)
                                 for c in xrange(world.cols)
                         )
        self.time_tracker = TimeTracker(0)
        castar.setup(world.map)

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
        if self.world.map[loc[0], loc[1]] != ants.MY_ANT:
            return None
        for ant in self.ants:
            if ant.pos == loc:
                return ant
        return None

    # do turn is run once per turn
    def do_turn(self, world):
        
        self.log.info("----------")
        self.log.info("Start turn")
        castar.setup(world.map)
        self.turn += 1

        #adding enemy hills
        for hill_loc, hill_owner in world.enemy_hills():
            self.enemy_hills.add(hill_loc)
        #removing razed hills
        for hill in self.enemy_hills.copy():
            if world.visible[hill[0], hill[1]]:
                if hill not in world.hill_list:
                    self.log.info("Removing hill at %s", hill)
                    self.enemy_hills.remove(hill)


        #enemy hills are removed by the warriors
        
        #removing visible locations
        for loc in self.unseen.copy():
            if world.visible[loc[0], loc[1]]:
                self.unseen.discard(loc)

        self.update_ants()

        #now is time to update the mover
        self.mover.update(self.ants)

        iter_ants = self.ants[:]
        random.shuffle(iter_ants)
        for ant_number, ant in enumerate(iter_ants):
            if not ant.check_status():
                self.ants.remove(ant)
                for d in self.dispatchers:
                    d.remove_ant(ant)
            else:
                ant.step()

            #avg_time = self.time_tracker.tock()
            if world.time_remaining() < 50:
                self.log.warning("Timeout incoming, bail out!")
                break
        
        self.mover.finalize()
        self.log.info("Time remaining: %f", world.time_remaining())
        if profiler is not None and self.turn == 200:
            profiler.dump_stats("profiler.prof")
            sys.exit()

        for h in self.enemy_hills:
            self.log.info("Enemy hill at %s, map shows %d", h, 
                    world.map[h[0],h[1]])

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

