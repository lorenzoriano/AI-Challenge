import time
import numpy
from MyBot import ants
timingf = ants.timingf

class TimeTracker(object):
    def __init__(self, nturns):
        self.recorded_times = []
        self.nturns = nturns
        self.nticks = 0.0
        self.moving_average = 0.0
        self.tick_time = None


    def tick(self):
        self.tick_time = timingf()

    def tock(self):
        elapsed = timingf()*1000. - self.tick_time*1000.
        return elapsed
        self.recorded_times.append(elapsed)
        return int(numpy.mean(self.recorded_times) * 1000)

#        elapsed = random.random()
        if self.nticks == 0.:
            self.nticks += 1.
            return elapsed

        N = self.nticks
        old_average = self.moving_average
        self.moving_average = N/(N+1) * old_average +  elapsed /(N+1)
        self.nticks = N+1

        return int(self.moving_average * 1000)

    def reset(self):
        self.recorded_times = []
        self.nticks = 0.0
        self.moving_average = 0.0
        self.tick_time = None
