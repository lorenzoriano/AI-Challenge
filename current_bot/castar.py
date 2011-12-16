import astar
import numpy as np
from MyBot import ants
from math import sqrt

astar_m = None
astar_mat = None
gworld = None

paths_cache = {}

def setup(mat, world):
    global astar_mat
    global astar_m
    global gworld

    gworld = world
    intmat = np.ones(mat.shape, dtype=np.float64)

    #Removing water from neighbours
    intmat[mat == ants.WATER] = -1
    #Increasing the cost of stepping over other ants
    intmat[mat == ants.ANTS] = 4 #the cost of going around is smaller
    
    #filename = "map_"+str(world.turn)+".txt"
    #np.savetxt(filename, intmat)

    if astar_mat is None:
        astar_mat = astar.MatrixHolder(intmat)
    astar_mat.setMat(intmat)
    if astar_m is None:
        astar_m = astar.AstarMatrix(astar_mat, 10000, 4)
    else:
        astar_m.reset()
    global paths_cache
    paths_cache = {}

def pathfind(start_pos, goal_pos, bot = None, world = None):
    """
    Plan a path from start_pos to goal_pos.

    Returns the path, which is empty if no path was found
    """
    global paths_cache
    if (start_pos, goal_pos) in paths_cache:
        return paths_cache[(start_pos, goal_pos)]

    path, cost = astar_m.solve(start_pos, goal_pos)
    if len(path) == 0:
        paths_cache[(start_pos, goal_pos)] = []
        return []
    else:
        paths_cache[(start_pos, goal_pos)] = path[1:]
        return path[1:]

def pathlen_range(start_pos, goal_pos, r):
    """
    Returns the length of the path between start_pos and goal_pos if it's less 
    than r, otherwise  r+1
    """
    if gworld.distance(start_pos, goal_pos) > r:
        return (r+1)
    path = pathfind(start_pos, goal_pos)
    if len(path) == 0 or len(path) > r:
        return (r+1)
    else:
        return len(path)

def pathlen(start_pos, goal_pos):
    """
    Return the length of the path between start_pos and goal_pos, or a very 
    large number if this path doesn't exist.
    """
    d = len(pathfind(start_pos, goal_pos))
    if d == 0:
        return 10e9
    else:
        return d

def pathdist(start_pos, goal_pos, d):
    """
    Return True if there is path between start_pos and goal_pos whose length is
    less than d, False otherwise
    """
    if gworld.distance(start_pos, goal_pos) > d:
        return False
    return 0 < len(pathfind(start_pos, goal_pos)) <= d

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
