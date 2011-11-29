import astar
import numpy as np
from MyBot import ants
from math import sqrt

astar_m = None
astar_mat = None

def add_enemies_surround(mat, world ):
    """Add a penalty value around the enemies"""
    amat = np.zeros(mat.shape, dtype=bool)
    viewradius = int(sqrt(world.attackradius2))
    diameter = viewradius * 2 + 1

    for (a_row, a_col), _ in world.enemy_ants():
        top = (a_row - viewradius) % world.rows
        left = (a_col - viewradius) % world.cols
        # Height/width of the top and left parts of vision disc (which might actually
        # be draw at the bottom or right of the map) -- rest of vision disc wraps over.
        toph = min(diameter, world.rows - top)
        leftw = min(diameter, world.cols - left)
        if toph == diameter and leftw == diameter:
            amat[top:top+toph, left:left+leftw] |= world.attack_disc
        else:
            bottomh = diameter - toph
            rightw = diameter - leftw

            amat[top:top+toph, left:left+leftw] |= world.attack_disc[:toph, :leftw]
            amat[:bottomh, left:left+leftw] |= world.attack_disc[toph:, :leftw]
            amat[top:top+toph, :rightw] |= world.attack_disc[:toph, leftw:]
            amat[:bottomh, :rightw] |= world.attack_disc[toph:, leftw:]
    
    mat[mat != ants.WATER] += (amat[mat != ants.WATER] * 4)

def setup(mat, world):
    global astar_mat
    global astar_m

    intmat = np.ones(mat.shape, dtype=np.float64)

    #Removing water from neighbours
    intmat[mat == ants.WATER] = -1
    #Increasing the cost of stepping over other ants
    intmat[mat == ants.ANTS] = 4 #the cost of going around is smaller
    
    add_enemies_surround(intmat, world)
    
    #filename = "map_"+str(world.turn)+".txt"
    #np.savetxt(filename, intmat)

    if astar_mat is None:
        astar_mat = astar.MatrixHolder(intmat)
    astar_mat.setMat(intmat)
    if astar_m is None:
        astar_m = astar.AstarMatrix(astar_mat, 10000, 4)
    else:
        astar_m.reset()

def pathfind(start_pos, goal_pos, bot = None, world = None):
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
