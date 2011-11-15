import astar
import numpy as np
from MyBot import ants

astar_m = None
astar_mat = None

def setup(mat):
    global astar_mat
    global astar_m

    intmat = np.ones(mat.shape, dtype=np.float64)

    #Removing water from neighbours
    intmat[mat == ants.WATER] = -1
    #Increasing the cost of stepping over other ants
    #intmat[mat > 0] = 10

    #np.savetxt("map.txt", intmat)

    if astar_mat is None:
        astar_mat = astar.MatrixHolder(intmat)
    astar_mat.setMat(intmat)
    if astar_m is None:
        astar_m = astar.AstarMatrix(astar_mat, 10000, 4)
    else:
        astar_m.reset()

def pathfind(start_pos, goal_pos, bot, world):
    """
    Plan a path from start_pos to goal_pos.

    Returns the path, which is empty if no path was found
    """
    path, cost = astar_m.solve(start_pos, goal_pos)
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
    cells = astar_m.solve_for_near_states(start_pos, max_cost)
    if len(cells) == 0:
        return cells
    else:
        return cells[1:]
