#!/usr/bin/env python
from ants import Ants
import logging
import explorer_dispatcher

def initLogging():
  #logLevel = logging.DEBUG
  logLevel = logging.INFO
  #logLevel = logging.WARNING
  logger = getLogger()
  logger.setLevel(logLevel)

  ch = logging.FileHandler("bot.txt", mode="w")
  ch.setLevel(logLevel)

  formatter = logging.Formatter("%(asctime)s - %(funcName)s: %(message)s")
  ch.setFormatter(formatter)
  getLogger().addHandler(ch)

def getLogger():
  return logging.getLogger("AntsLog")

class TurnLogger(logging.LoggerAdapter):
    def process(self, ):
        """
    
        """
        pass

class PezzBot:
    def __init__(self):
        self.log = getLogger()
        self.ants = []
        self.world = None
        self.orders = {}
        self.turn = 0
    
    # do_setup is run once at the start of the game
    # after the bot has received the game settings
    # the ants class is created and setup by the Ants.run method
    def do_setup(self, world):
        self.log.info("Setup")
        self.world = world
        self.explorer_dispatcher = explorer_dispatcher.ExplorerDispatcher(
                world, self)
    
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
                self.log.info("Creating an ant at %s", str(ant_loc))
                newant = self.explorer_dispatcher.create_ant(ant_loc)
                if newant is not None:
                    self.ants.append(newant)

    # do turn is run once per turn
    def do_turn(self, world):
        self.log.info("----------")
        self.log.info("Start turn")
        self.turn += 1

        #clear orders
        self.orders = {}

        self.update_ants()
        for ant in self.ants[:]:
            if not ant.check_status():
                self.ants.remove(ant)
                self.explorer_dispatcher.remove_ant(ant)
            else:
                ant.step()
        
if __name__ == '__main__':
    initLogging()
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        Ants.run(PezzBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
