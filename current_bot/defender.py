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
    
    def orbit(self):
        """
        Moves randomly, but if the the distance from the assigned hill is
        less than 5 then moves back towards the hill. Creates a flock if danger
        is close.
        """
        
        r = defenders_flock.DefendersFlock.danger_radius
        enemies = self.enemies_in_range(r)
        if len(enemies):
            defenders_flock.create(self,r, len(enemies))
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

