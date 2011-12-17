cdef extern from "math.h":
    double sqrt(double)

def danger_positions(tuple center, int attackradius2,):
    """
    Returns a list of all the squares that center would attack if it
    moves and a nearby ant moves too.
    """
    cdef int radius = <int>(sqrt(attackradius2)) + 2
  
    cdef int* moves_r = [0, -1, 1, 0, 0]
    cdef int* moves_c = [0, 0, 0, -1, 1]

    cdef list res = [] 
    cdef int d_row
    cdef int d_col
    cdef int r1, c1
    cdef int r2, c2
    cdef int d2

    cdef int center0 = center[0]
    cdef int center1 = center[1]

    cdef unsigned int i, j
    
    cdef int will_break = 0
    
    for d_row in range(-radius + center0 , radius+center0+1):
        for d_col in range(-radius +center1, radius+center1+1):
            will_break = 0
            for i in range(5):
                if will_break:
                    break
                
                r1 = moves_r[i]
                c1 = moves_c[i]
                for j in range(5):
                    r2 = moves_r[j]
                    c2 = moves_c[j]
                    d2 = ( ( (d_row+r1)-(center0+r2) )**2 + 
                           ( (d_col+c1)-(center1+c2) )**2
                         )
                    if d2 <= attackradius2:
                        res.append((d_row, d_col))
                        will_break = 1
                        break
    return res

def can_attack(tuple center, int attackradius2):
    """returns an interator over all the poses that center can attack if it
    moves"""
    cdef int radius = <int>(sqrt(attackradius2)) + 2
  
    cdef int* moves_r = [0, -1, 1, 0, 0]
    cdef int* moves_c = [0, 0, 0, -1, 1]
  
    cdef list res = [] 
    cdef int d_row
    cdef int d_col
    cdef int r2, c2
    cdef int d2

    cdef int center0 = center[0]
    cdef int center1 = center[1]

    cdef unsigned int i, j

     
    for d_row in range(-radius + center0 , radius+center0+1):
        for d_col in range(-radius +center1, radius+center1+1):
            for j in range(5):
                r2 = moves_r[j]
                c2 = moves_c[j]
                d2 = ( ( (d_row)-(center0+r2) )**2 + 
                       ( (d_col)-(center1+c2) )**2
                     )
                if d2 <= attackradius2:
                    res.append((d_row, d_col))
                    break
    return res
