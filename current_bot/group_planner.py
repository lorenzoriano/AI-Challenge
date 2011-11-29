import astar
class GroupPlanner(object):
    """
    This planner will not penalize movement over other ants, therefore
    allowing for a more compact group motion.
    It mimics the interface of the castar module.
    """
    def __init__(self, mat):
        self.astar_mat = astar.MatrixHolder(mat)
        self.astar_m = astar.AstarMatrix(self.astar_mat,10000,4)
    
    def reset(self, mat):
        """
        Reset the astar structures.
        """
        self.astar_mat.setMat(mat)
        self.astar_m.reset()
    
    def pathfind(self, start_pos, goal_pos, bot = None, world = None):
        """
        Plan a path from start_pos to goal_pos.

        Returns the path, which is empty if no path was found
        """
        path, _ = self.astar_m.solve(start_pos, goal_pos)
        if len(path) == 0:
            return []
        else:
            return path[1:]

    def find_near(self, start_pos, max_cost):
        """
        Find all the cells within max_cost distance.
        Returns a list of the cells, empty if no cell
        was found. The starting cell will not be included.
        """
        cells = self.astar_m.solve_for_near_states(start_pos, max_cost)
        if len(cells) == 0:
            return cells
        else:
            return cells[1:]

