cimport numpy as np

cdef inline int int_min(int a, int b): return a if a <= b else b
cdef inline int int_abs(int a): return a if a >= 0  else -a

cpdef int distance(int row1, int col1, int row2, int col2, int rows, int cols):
        "Calculate the closest distance between two locations"
        cdef int d_col = int_min(int_abs(col1 - col2), cols - int_abs(col1 - col2))
        cdef int d_row = int_min(int_abs(row1 - row2), rows - int_abs(row1 - row2))
        return d_row + d_col

def closest_pos(int row, int col, 
                np.ndarray[np.int_t, ndim=2, mode="c"] positions, 
                int rows, int cols):

    cdef int r, c
    cdef int d
    cdef int min_d = 10000
    cdef int min_index = 0
    cdef unsigned int i

    cdef int l = positions.shape[0]
    for i in range(l):
        r = positions[i, 0]
        c = positions[i, 1]
        d = distance(row, col, r, c, rows, cols)
        if d < min_d:
            min_d = d
            min_index = i

    return min_index
