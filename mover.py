from MyBot import ants
import logging
import pezz_logging

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


class Mover(object):
    def __init__(self, world, bot):
        self.world = world
        self.orders = {}
        self.notmoving = set()
        #logging structure
        self.log = pezz_logging.TurnAdapter(
                logger,
                {"ant":"Mover"},
                bot
                )
 

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
        self.notmoving = set(a.pos for a in antlist)


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
        if self.world.map[loc[0], loc[1]] != ants.WATER: 
            if not self.orders.has_key(loc):
                self.orders[loc] = ant
                self.notmoving.remove(ant.pos)
                return True

        return False

    def finalize(self):
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
