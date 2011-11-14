#! /usr/bin/python

import astar
import numpy as np
import time
from random import randrange

astar_o = None
astar_mat = None

def setup(mat):
    global astar_mat
    global astar_o
    if astar_mat is None:
        astar_mat = astar.MatrixHolder(mat)
    astar_mat.setMat(mat)
    if astar_o is None:
        astar_o = astar.AstarMatrix(astar_mat, 10000, 4)
    else:
        astar_o.reset()
        pass

def pathfind(start_pos, goal_pos, bot, world):
    """
    Plan a path from start_pos to goal_pos.

    Returns the path, which is empty if no path was found
    """
    path, cost = astar_o.solve(start_pos, goal_pos)
    if len(path) == 0:
        return []
    else:
        return path[1:]


cumtime = 0.0
nsteps = 1000
rows = 300
cols = 300
for i in xrange(nsteps):
    fmat = np.random.random( (rows,cols))
    fmat[fmat>0.8] = 1
    fmat[fmat<=0.8] = -4

    mat = fmat.astype(np.int8)
    rs = randrange(0,rows)
    re = randrange(0,rows)
    cs = randrange(0,cols)
    ce = randrange(0,cols)
    
    now = time.time()
    setup(mat)
    pathfind( (rs,cs), (re,ce) , None, None)
    
    cumtime += (time.time() - now)

print "Average time: %f" % (cumtime/nsteps)
