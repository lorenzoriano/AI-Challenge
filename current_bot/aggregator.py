import types
import random
import logging

logger = logging.getLogger("pezzant.aggregator")
loglevel = logging.INFO
logger.setLevel(loglevel)
#fh = logging.StreamHandler(sys.stderr)
fh = logging.FileHandler("bot.txt", mode="a")
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
def aggr_check_status(self):
    res = self.__class__.check_status(self)
    if not res:
        self.aggregator.remove_ant(self)
    return res

def aggr_step(self):
    self.aggregator.step(self)

aggregator_id = 0

class Aggregator(object):
    """
    The general class for an aggregator.
    """
    def __init__(self, leader, antlist):
        """
        leader: the ants on which many computations might be based.
        antlist: a list of ants to add to this aggregator
        """
        global aggregator_id
        self.id = aggregator_id
        aggregator_id += 1
        
        self.controlled_ants = [] 
        self.leader = leader
        for ant in antlist:
            self.control(ant)

        self.bot = leader.bot
        self.last_turn = -1

    def __repr__(self):
        return (self.__class__.__name__ +
                "(" +
                str(self.id) + 
                ")"
                )
    
    def control(self, ant):
        """
        Takes control of an ant by injecting a new step function. 
        
        Parameters:
        step_fun: the new step function
        """
        self.log.info("Taking control of %s", ant)
        ant.step = types.MethodType(aggr_step, ant, ant.__class__)
        ant.check_status = types.MethodType(aggr_check_status, ant,
                ant.__class__)
        ant.aggregator = self
        self.controlled_ants.append(ant)

    def remove_ant(self, ant):
        """
        Remove ant from the controlled ants, restoring its methods.
        
        Parameters:
        ant: an Ant
        """
        self.log.info("Removing ant %s", ant)
        del ant.aggregator
        ant.step = types.MethodType(ant.__class__.step, ant, ant.__class__)
        ant.check_status = types.MethodType(ant.__class__.check_status, ant,
                ant.__class__)
        self.controlled_ants.remove(ant)

        #select a new leader
        if len(self.controlled_ants) == 0:
            return
        if ant == self.leader:
            self.leader = random.choice(self.controlled_ants)
            self.log.info("Selecting the new leader %s", self.leader)

    def destroy(self):
        """
        Destroy the aggragator. This has to be called before
        delete.

        All the ants will get their set method restored.
        """
        self.log.info("getting destroyed")
        for ant in self.controlled_ants[:]:
            self.remove_ant(ant)
        self.controlled_ants = []
    
    def newturn(self):
        """
        This method gets executed every time a new turn is ongoing.
        Subclasses should ovverride.
        """
        pass

    def step(self, ant):
        """
        Every time an ant belonging to this aggregator gets its step
        method called, this method is called instead. This method calls
        newturn only once every turn.
        A subclass should override but still call this method.
        """
        if self.bot.turn != self.last_turn:
            self.new_turn()
        self.last_turn = self.bot.turn

