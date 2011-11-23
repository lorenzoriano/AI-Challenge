import singleant
import random
import defenders_flock

class Defender(singleant.SingleAnt):
    """
    The Defender class.

    The Defender will orbit a nest, ready to create a defender flock if
    enemies approach.
    """
    def __init__(self, loc, bot, world, dispatcher):
        super(Defender,self).__init__(loc, bot, world, "orbit")
       
        #if there are no hills left I'd better generate a crash here
        self.myhill = min((world.distance(loc,h), h) 
                for h in world.my_hills())[1]
        self.dispatcher = dispatcher
    
    def enemy_in_range(self, r):
        """
        Returns True if an enemy is less than r distant from the home hill.
        """

        world = self.world
        for e in world.enemy_ants():
            d = world.distance(self.myhill, e[0])
            if d <= r:
                return True
        return False

    def orbit(self):
        """
        Moves randomly, but if the the distance from the assigned hill is
        less than 5 then moves back towards the hill. Creates a flock if danger
        is close.
        """
        
        if self.enemy_in_range(defenders_flock.DefendersFlock.danger_radius):
            defenders_flock.create(self,
                    defenders_flock.DefendersFlock.danger_radius)
            return

        if self.world.distance(self.pos, self.myhill) > 5:
            self.log.info("moving towards the hill")
            for d in self.world.direction(self.pos, self.myhill):
                if self.move_heading(d):
                    break
            return
        else:
            self.log.info("moving random")
            directions = ['n','s','w','e']
            random.shuffle(directions)

            for d in directions:
                if self.move_heading(d):
                    break
            return

