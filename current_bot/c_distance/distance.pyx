cdef inline int int_min(int a, int b): return a if a <= b else b
cdef inline int int_abs(int a): return a if a >= 0  else -a

def distance(int row1, int col1, int row2, int col2, int rows, int cols):
        "Calculate the closest distance between two locations"
        cdef int d_col = int_min(int_abs(col1 - col2), cols - int_abs(col1 - col2))
        cdef int d_row = int_min(int_abs(row1 - row2), rows - int_abs(row1 - row2))
        return d_row + d_col

