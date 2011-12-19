import numpy as np
cimport numpy as np
cimport cython

cdef extern from "math.h":
    double sqrt(double)

cdef inline int int_min(int a, int b): return a if a <= b else b
cdef inline int int_abs(int a): return a if a >= 0  else -a

cdef inline int distance(int row1, int col1, int row2, int col2, int rows, int cols):
        "Calculate the closest distance between two locations"
        cdef int d_col = int_min(int_abs(col1 - col2), cols - int_abs(col1 - col2))
        cdef int d_row = int_min(int_abs(row1 - row2), rows - int_abs(row1 - row2))
        return d_row + d_col

@cython.boundscheck(False)
def closest_pos(np.ndarray[np.int8_t, ndim=2, mode="c"] availability not None,
                np.ndarray[np.int8_t, ndim=2, mode="c"] world_map not None,
                int row, int col,
                ):
    
    cdef int WATER=-4
    cdef unsigned int i, j
    cdef int d
    cdef int min_d = 10000
    cdef int best_i =-1, best_j = -1

    cdef int rows = availability.shape[0]
    cdef int cols = availability.shape[1]

    for i in range(rows):
        for j in range(cols):
            
            if not availability[i,j]:
                continue
            if world_map[i,j] == WATER:
                continue
            
            d = distance(row, col, i, j, rows, cols)
            if d < min_d:
                min_d = d
                best_i = i
                best_j = j
    
    return (best_i, best_j)

@cython.boundscheck(False)
def create_availability_map(
                   np.ndarray[np.int8_t, ndim=2, mode="c"] availability not None,
                   np.ndarray[np.int_t, ndim=2, mode="c"] enemy_poses not None,
                   int visibility_range
                   ):

    cdef int radius = <int>sqrt(visibility_range) + 1

    cdef int nenemies = enemy_poses.shape[0]
    cdef int rows = availability.shape[0]
    cdef int cols = availability.shape[1]
    
    cdef unsigned int r,c
    cdef int d
    cdef unsigned int i
    cdef int r_enemy, c_enemy
    cdef int d_row, d_col

    for i in range(nenemies):
        r_enemy = enemy_poses[i,0]
        c_enemy = enemy_poses[i,1]
        for d_row in range(-radius + r_enemy , radius+ r_enemy+1):
            for d_col in range(-radius +c_enemy, radius+c_enemy+1):
                
                r = d_row % rows
                c = d_col % cols

                if not availability[r,c]:
                    continue

                d = (d_row - r_enemy)**2 + (d_col - c_enemy)**2
                if d <= visibility_range:
                    availability[r,c] = 0

@cython.boundscheck(False)
def add_to_mask(np.ndarray[np.int8_t, ndim=2, mode="c"] mask not None,
                int row, int col,
                int visibility_range
                ):
    
    cdef int radius = <int>sqrt(visibility_range) + 1
    cdef int d_row, d_col
    cdef unsigned int r,c
    cdef int d
    cdef int rows = mask.shape[0]
    cdef int cols = mask.shape[1]

    for d_row in range(-radius + row , radius+ row+1):
        for d_col in range(-radius +col, radius+col+1):
            r = d_row % rows
            c = d_col % cols
            d = (d_row - row)**2 + (d_col - col)**2
            if d <= visibility_range:
                mask[r,c] = 1

@cython.boundscheck(False)
def remove_from_mask(np.ndarray[np.int8_t, ndim=2, mode="c"] mask not None,
                int row, int col,
                int visibility_range
                ):
    
    cdef int radius = <int>sqrt(visibility_range) + 1
    cdef int d_row, d_col
    cdef unsigned int r,c
    cdef int d
    cdef int rows = mask.shape[0]
    cdef int cols = mask.shape[1]

    for d_row in range(-radius + row , radius+ row+1):
        for d_col in range(-radius +col, radius+col+1):
            r = d_row % rows
            c = d_col % cols
            d = (d_row - row)**2 + (d_col - col)**2
            if d <= visibility_range:
                mask[r,c] = 0

