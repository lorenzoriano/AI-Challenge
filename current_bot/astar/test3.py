#! /usr/bin/python
import numpy as np
import astar
l = ((-1,1,1,1,1.),
     (-1,1,4,4,4),
     (-1,1,1,-1,-1),
     (-1,-1,-1,-1, -1))
mat = np.array(l)

mh = astar.MatrixHolder(mat)
astar = astar.AstarMatrix(mh)

mh.setMat(mat)
astar.reset()

start = (2,2)
goal = (0,4)

path= astar.solve(start,goal)
print "path: ", path


