#!/usr/bin/env python
from ants import Ants
import pezz_logging
import logging
import explorer_dispatcher
import warrior_dispatcher
import sys
import random

logger = logging.getLogger("pezzant")
loglevel = logging.INFO
logger.setLevel(loglevel)
fh = logging.StreamHandler(sys.stderr)
#fh = logging.FileHandler("bot.txt", mode="w")
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
        for ant in iter_ants:
            #try:
                if not ant.check_status():
                    self.ants.remove(ant)
                    self.explorer_dispatcher.remove_ant(ant)
                    self.warrior_dispatcher.remove_ant(ant)
                else:
                    ant.step()
            #except Exception, e:
            #    self.log.error("Got an exception %s for ant %s", e, ant)

        self.log.info("Time remaining: %f", world.time_remaining())
if __name__ == '__main__':
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        Ants.run(PezzBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
