import types
import random

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
        global aggregator_id
        self.id = aggregator_id
        aggregator_id += 1
        
        self.controlled_ants = [] 
        self.leader = leader
        for ant in antlist:
            self.control(ant)

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
    
    def step(self):
        raise NotImplementedError(
            "The Aggregator step method must be subclassed")
