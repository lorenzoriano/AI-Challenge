import types
import random
import logging
import pezz_logging
import group_planner
import numpy as np
import MyBot
ants = MyBot.ants
import castar

logger = logging.getLogger("pezzant.aggregator")

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
        self.planner = group_planner.GroupPlanner(leader.world.map)
        self.bot = leader.bot
        self.world = leader.world
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant": self},
                self.bot
                )
        
        global aggregator_id
        self.id = aggregator_id
        aggregator_id += 1
        
        self.controlled_ants = set() 
        self.leader = leader
        for ant in antlist:
            self.control(ant)

        self.last_turn = -1
        self.destroyed = False
        self.centroid = None
        self.grouping = 0.0
        self.previous_poses = None
        self.current_poses = None
    
    def setup_planner(self, group_state):
        """
        Setup the planner with a new matrix.

        Parameters:
        group_state: if True, then the ants are not counted as obstacle. 
                    Useful when trying to keep the group tight
        """
        newmat = np.ones(self.world.map.shape, dtype=np.float64)
        newmat[self.world.map == ants.WATER] = -1
        if group_state:
            newmat[self.world.map == ants.ANTS] = 4
        self.planner.reset(newmat)

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
        if hasattr(ant, "aggregator"):
            self.log.info("stealing %s from %s", ant, ant.aggregator)
            ant.aggregator.remove_ant(ant)
        
        ant.step = types.MethodType(aggr_step, ant, ant.__class__)
        ant.check_status = types.MethodType(aggr_check_status, ant,
                ant.__class__)
        ant.aggregator = self
        ant.planner = self.planner
        self.controlled_ants.add(ant)

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
        ant.planner = castar
        self.controlled_ants.remove(ant)

        #select a new leader
        if len(self.controlled_ants) == 0:
            if not self.destroyed:
                self.log.info("No more controlled ants, destroying")
                self.destroy()
        elif ant == self.leader:
            self.leader = random.choice(list(self.controlled_ants))
            self.log.info("Selecting the new leader %s", self.leader)

    def calculate_grouping(self):
        """
        Calculate the grouping factor and the centroid of all the 
        controlled ants.
        
        Grouping is defined as the standard deviation between the poses
        of all the ants.
        """
        arr = np.array(self.current_poses)
        m = np.mean(arr,0)
        self.centroid = (int(round(m[0])),
                         int(round(m[1]))
                        )
        self.log.info("New centroid: %s", self.centroid)
        self.log.info("My ants poses are: %s", 
                [a.pos for a in self.controlled_ants]) 
        self.grouping = np.max(np.std(arr,0))
        self.log.info("Grouping value of %f", self.grouping)
    
    def destroy(self):
        """
        Destroy the aggragator. This has to be called before
        delete.

        All the ants will get their set method restored.
        """
        self.destroyed = True
        self.log.info("getting destroyed")
        self.log.info("my controlled ants are: %s", self.controlled_ants)
        for ant in self.controlled_ants.copy():
            self.remove_ant(ant)
        self.controlled_ants.clear()

    def newturn(self):
        """
        This method gets executed every time a new turn is ongoing.
        Subclasses should ovverride.
        """
        self.previous_poses = self.current_poses
        self.current_poses = [ant.pos for ant in self.controlled_ants]

    def check_status(self):
        """
        This function has to return True if the aggregator is 
        still alive, False otherwise
        """
        raise NotImplementedError 

    def step(self, ant):
        """
        Every time an ant belonging to this aggregator gets its step
        method called, this method is called instead. This method calls
        newturn only once every turn.
        A subclass should override but still call this method.
        """
        #removing ants that do not belong to me
        if hasattr(ant, "aggregator"):
            if ant.aggregator != self:
                self.log.info("Ant %s does not belong to me anymore", ant)
                self.controlled_ants.discard(ant)
        if self.bot.turn != self.last_turn:
            #check status is done only once
            if not self.check_status():
                self.destroy()
                #but first execute the restored ant step method
                ant.step()
                return
            self.newturn()
        self.last_turn = self.bot.turn

