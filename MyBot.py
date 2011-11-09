#!/usr/bin/env python
import ants_orig as ants
Ants = ants.Ants

#from ants import Ants
import pezz_logging
import logging
import explorer_dispatcher
import warrior_dispatcher
from timetracker import TimeTracker

import time
import sys
import random
import cProfile
import signal

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
logger.addHandler(fh)

#profiler = cProfile.Profile()
profiler = None

class TurnLogger(logging.LoggerAdapter):
    def process(self, ):
        """
    
        """
        pass

class PezzBot:
    def __init__(self):
        self.ants = []
        self.world = None
        self.orders = {}
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
        self.warrior_dispatcher = warrior_dispatcher.WarriorDispatcher(world,
                self)
        self.unseen = set( (r,c) for r in xrange(world.rows)
                                 for c in xrange(world.cols)
                         )
        self.time_tracker = TimeTracker(0)

    def iterate_ants_loc(self):
        """
        An iterator that returns all the ants location    
        """
        for ant in self.ants:
            yield ant.pos

    def update_ants(self):
        """
        Create new ants if necessary
        """
        for ant_loc in self.world.my_ants():
            if ant_loc not in self.iterate_ants_loc():
                newant = self.explorer_dispatcher.create_ant(ant_loc)
                if newant is not None:
                    self.ants.append(newant)
                else:
                    newant = self.warrior_dispatcher.create_ant(ant_loc)
                    if newant is not None:
                        self.ants.append(newant)

    # do turn is run once per turn
    def do_turn(self, world):
        
        self.log.info("----------")
        self.log.info("Start turn")
        self.turn += 1
        #self.time_tracker.reset()

        #clear orders
        self.orders = {}

        #adding enemy hills
        for hill_loc, hill_owner in world.enemy_hills():
            self.enemy_hills.add(hill_loc)

        #removing visible locations
        for loc in self.unseen.copy():
            if world.visible(loc):
                self.unseen.discard(loc)

        self.update_ants()
        iter_ants = self.ants[:]
        random.shuffle(iter_ants)
        for ant_number, ant in enumerate(iter_ants):
            self.time_tracker.tick()
            if not ant.check_status():
                self.ants.remove(ant)
                self.explorer_dispatcher.remove_ant(ant)
                self.warrior_dispatcher.remove_ant(ant)
            else:
                ant.step()

            avg_time = self.time_tracker.tock()
            if world.time_remaining() - 10*avg_time < 0:
                self.log.warning("Timeout incoming, bail out!")
                break

        self.log.info("Average time: %f", avg_time)
        self.log.info("Time remaining: %f", world.time_remaining())
        if profiler is not None and self.turn == 150:
            profiler.dump_stats("profiler.prof")


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

