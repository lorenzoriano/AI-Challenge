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

def find_near(start_pos, max_cost):
    """
    Find all the cells within max_cost distance.
    Returns a list of the cells, empty if no cell
    was found. The starting cell will not be included.
    """
    cells = astar_o.solve_for_near_states(start_pos, max_cost)
    if len(cells) == 0:
        return cells
    else:
        return cells[1:]

cumtime = 0.0
nsteps = 1000
rows = 300
cols = 300
for i in xrange(nsteps):
    fmat = np.random.random( (rows,cols))
    fmat[fmat>0.2] = 1
    fmat[fmat<=0.2] = -4

    mat = fmat.astype(np.int8)
    rs = randrange(0,rows)
    re = randrange(0,rows)
    cs = randrange(0,cols)
    ce = randrange(0,cols)
    
    now = time.time()
    setup(mat)
    pathfind( (rs,cs), (re,ce) , None, None)
    
    cumtime += (time.time() - now)

print "Find path: average time per step: %f" % (cumtime/nsteps)
cumtime = 0.0
nsteps = 1000
radius = 150.0
lengths = 0.0
for i in xrange(nsteps):
    fmat = np.random.random( (rows,cols))
    fmat[fmat>0.2] = 1
    fmat[fmat<=0.2] = -4

    mat = fmat.astype(np.int8)
    row = randrange(0,rows)
    col = randrange(0,cols)
    
    now = time.time()
    setup(mat)
    l = find_near((row,col), radius)
    
    cumtime += (time.time() - now)
    lengths += len(l)


print "Find near: average time per step: %f" % (cumtime/nsteps)
print "Average cells length: %f" % (lengths / nsteps)
