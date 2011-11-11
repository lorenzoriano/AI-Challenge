import libastar
import numpy as np

a = np.ones((20,20), dtype=np.float64)
m = libastar.Matrix_new(a)

libastar.Matrix_setMat(m,a)
print "creating astar"
astar_m = libastar.AstarMatrix_new(m, 1000, 4)


start = (0,0)
end = (5,5)

path = libastar.AstarMatrix_solve(astar_m, start, end)
print "Path is: ", path


print "resetting"
libastar.AstarMatrix_reset(astar_m)
print "deleting astar"
libastar.AstarMatrix_delete(astar_m)
print "creating astar"
astar_m = libastar.AstarMatrix_new(m, 1000, 4)

path = libastar.AstarMatrix_solve(astar_m, start, end)
print "Path is: ", path

print "deleting astar"
libastar.AstarMatrix_delete(astar_m)
print "deleting m"
libastar.Matrix_delete(m)

print "Todo OK"
