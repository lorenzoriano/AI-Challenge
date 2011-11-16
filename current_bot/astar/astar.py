import libastar as _lib
#import ctypes
#_lib = ctypes.cdll.LoadLibrary('./libastar.so')

#_lib.Matrix_new.argtypes = [ctypes.py_object]
#_lib.Matrix_delete.argtypes = [ctypes.c_size_t, ctypes.py_object]
#_lib.Matrix_setMat.argtypes = [ctypes.c_size_t, ctypes.py_object]

#_lib.AstarMatrix_new.argtypes = [ctypes.py_object, ctypes.c_uint, ctypes.c_uint]
#_lib.AstarMatrix_solve.argtypes = [ctypes.c_size_t, ctypes.py_object]
#_lib.AstarMatrix_solve.restype = ctypes.py_object


class MatrixHolder(object):
    def __init__(self, mat):
        self.obj = _lib.Matrix_new(mat)

    def setMat(self, mat):
        _lib.Matrix_setMat(self.obj, mat)

    def __del__(self):
        _lib.Matrix_delete(self.obj)
    

class AstarMatrix(object):
    def __init__(self, matrix, alloc=10000, _ = None):
        self.matrix = matrix;
        self.obj = _lib.AstarMatrix_new(matrix.obj, alloc, 4)

    def solve(self, start, goal):
        return _lib.AstarMatrix_solve(self.obj, start, goal)
    
    def solve_for_near_states(self, start, cost):
        return _lib.AstarMatrix_solve_for_near_states(self.obj, start, cost)

    def reset(self,):
        return _lib.AstarMatrix_reset(self.obj)

    def __del__(self):
        _lib.AstarMatrix_delete(self.obj)
