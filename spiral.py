def spiral(loc, n):
    """
    Spiral iterator of n steps around loc. loc is included.
    """
    x,y = (0,0)
    dx, dy = 0, -1
    for _ in xrange(n):
        if abs(x) == abs(y) and [dx,dy] != [1,0] or x>0 and y == 1-x:  
            dx, dy = -dy, dx            # corner, change direction

        yield loc[0] + x, loc[1] + y
        x, y = x+dx, y+dy
