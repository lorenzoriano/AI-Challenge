from MyBot import ants
import logging
import pezz_logging

logger = logging.getLogger("pezzant.Mover")

class Mover(object):
    def __init__(self, world, bot):
        self.world = world
        self.orders = {}
        self.notmoving = set()
        self.depends_on = {}
        self.moving = set()
        self.all_ants = set()
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"Mover"},
                bot
                )
        self.pos_mapping = {}
 

    def update(self, antlist):
        """
        Prepares for a new turn. This function has to be called before 
        all the ants issue any order but AFTER they are checked for being alive. 
        In other words, this list should contain a list of all the 
        active ants in a turn.
        
        Parameters:
        antlist: a list of all the active ants in the game.
    
        Return:
        None    
        """
        self.orders.clear()
        self.notmoving.clear()
        self.moving .clear()
        self.pos_mapping.clear()
        self.all_ants.clear()
        for a in antlist:
            self.notmoving.add(a.pos)
            self.pos_mapping[a.pos] = a
            self.all_ants.add(a.pos)

    def ask_to_move(self, ant, loc):
        """
        Check if an ant can move to a location. An ant could 
        move if loc is not water and if no other ant wants to
        move to the same location.
        
        Parameters:
        ant: a SingleAnt object
        loc: a (row,col) pair
    
        Return:
        True on success, False otherwise
        """
        if self.world.map_value(loc) != ants.WATER: 
            if not loc in self.orders.values():
                self.orders[ant] = loc
                self.notmoving.discard(ant.pos)
                self.moving.add(ant.pos)
                self.depends_on[ant.pos] = loc
                return True

        return False

    def solve_dependency(self, elem, poses):
        """
        Starting with an element, calculate the chain of dependencies and
        valuates if the ants can move or not. If one ant in the chain is 
        not moving or if the chain is circular, then the whold chain of ants
        cannot move.

        To call: solve_dependency( (row,col), [(row,col)])

        Parameters:
        elem: (row,col)
        pos_list: a set. This is a return parameter too

        Return:
        True if the ants can move, False otherwise. The set poses will also
        contain the result of the computation.
        """
        tail = self.depends_on[elem]
        if tail in poses:
            #the chain is circular
            return True
        #if tail is not an ant, then the chain is free
        if tail not in self.all_ants:
            return True
        poses.add(tail)
        if tail in self.notmoving:
            #the chain depends on a not moving ant, so it won't work
            return False
        return self.solve_dependency(tail, poses)

    def finalize(self):
        """
        Issue all the movements that do not conflict
        
        Parameters:
        None
    
        Return:
        None
        """
        moved_ants = set()
        while len(self.moving) > 0:
            elem = self.moving.pop()
            chain = set((elem,))
            ret = self.solve_dependency(elem, chain)
            if ret:
                for pos in chain:
                    ant = self.pos_mapping[pos]
                    if ant not in moved_ants:
                        ant.movement_success(self.orders[ant])
                        moved_ants.add(ant)
                self.moving.difference_update(chain)
                self.notmoving.difference_update(chain)
            else:
                #self.log.warning("The chain %s does not move!", chain)
                for pos in chain:
                    ant = self.pos_mapping[pos]
                    try:
                        ant.movement_failure(self.orders[ant])
                    except KeyError:
                        pass
                self.moving.difference_update(chain)
                self.notmoving.update(chain)
        
    def __finalize(self):
        """
        Issue all the movements that do not conflict
        
        Parameters:
        None
    
        Return:
        None
    
        """
        for loc, ant in self.orders.iteritems():
            if loc in self.notmoving:
                #the ant can't move, so it becomes a fixed
                ant.movement_failure(loc)
                self.notmoving.add(ant.pos) #this shouldn't be necessary
            else:
                ant.movement_success(loc)
