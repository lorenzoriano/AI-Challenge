from math import sqrt
import itertools

def circular_poses(x0, y0, radius):
    """
    Returns a set of (i,j) poses that describe a circle centered around x0, y0
    and with specified radius. It uses the midpoing algorithm.
    """
    f = 1 - radius
    ddF_x = 1
    ddF_y = -2 * radius
    x = 0
    y = radius

    locations = set()
 
    locations.add( (x0, y0 + radius) )
    locations.add((x0, y0 - radius))
    locations.add((x0 + radius, y0))
    locations.add((x0 - radius, y0))
 
    while(x < y):
        if(f >= 0) :
            y -= 1;
            ddF_y += 2;
            f += ddF_y;
        x += 1
        ddF_x += 2
        f += ddF_x    
        locations.add((x0 + x, y0 + y))
        locations.add((x0 - x, y0 + y))
        locations.add((x0 + x, y0 - y))
        locations.add((x0 - x, y0 - y))
        locations.add((x0 + y, y0 + x))
        locations.add((x0 - y, y0 + x))
        locations.add((x0 + y, y0 - x))
        locations.add((x0 - y, y0 - x))

    return locations

def circular_poses_iter(x0, y0, radius):
    """
    Returns an iterator overl all the (i,j) poses that describe a circle 
    centered around x0, y0 and with specified radius. 
    It uses the midpoing algorithm.
    """
    f = 1 - radius
    ddF_x = 1
    ddF_y = -2 * radius
    x = 0
    y = radius

 
    yield (x0, y0 + radius) 
    yield (x0, y0 - radius)
    yield (x0 + radius, y0)
    yield (x0 - radius, y0)
 
    while(x < y):
        if(f >= 0) :
            y -= 1;
            ddF_y += 2;
            f += ddF_y;
        x += 1
        ddF_x += 2
        f += ddF_x    
        yield (x0 + x, y0 + y)
        yield (x0 - x, y0 + y)
        yield (x0 + x, y0 - y)
        yield (x0 - x, y0 - y)
        yield (x0 + y, y0 + x)
        yield (x0 - y, y0 + x)
        yield (x0 + y, y0 - x)
        yield (x0 - y, y0 - x)


def manhattan_fixed_dist(center, dist, offsets_cache={}):
    """ Return a list of squares exactly at a given distance of center = (r,c)

        The manhattan distance is used.
        offsets_cache uses a cache of previously calculated values, do not use
        it!
    """
    radius = int(dist) + 1
    if dist not in offsets_cache:
        offsets = []
        for d_row in xrange(-radius, radius+1):
            for d_col in xrange(-radius, radius+1):
                dm = abs(d_row) + abs(d_col)
                d = sqrt(d_row**2 + d_col**2)
                #print "r,c: ", (d_row,d_col), " d: ", d, " d2: ", d_row**2+d_col**2
                if dm == int(dist):
                    offsets.append((
                        d_row,
                        d_col
                    ))
        offsets_cache[dist] = offsets
    return set( (center[0] + r, center[1] + c) 
            for r,c in offsets_cache[dist])

def attack_positions(center, attackradius2, manh_range=(3,5)):
    radius = int(sqrt(attackradius2)) + 20
    offsets = []
    
    variations = ((0, 0),
                  (0, -1),
                  (-1, 0),
                  (-1, -1),
                  (0, 1),
                  (1, 0),
                  (1, 1)
                 )

    for d_row in xrange(-radius , radius+1):
        for d_col in xrange(-radius , radius+1):
            dm = abs(d_row) + abs(d_col)
            d2 = ( (d_row+r)**2 + (d_col+c)**2
                    for r,c in variations
                 )
            if ((manh_range[0] <= dm <= manh_range[1]) and 
                all(d > attackradius2 for d in d2)):
                offsets.append( (d_row, d_col) )
    
    return set( (center[0] + r, center[1] + c) 
            for r,c in offsets)

def __attack_positions(center, attackradius2):
    radius = int(sqrt(attackradius2)) + 2
    offsets = []
    
    for d_row in xrange(-radius , radius+1):
        for d_col in xrange(-radius , radius+1):
            dm = abs(d_row) + abs(d_col)
            d2 = (d_row)**2 + (d_col)**2
                 
            if (4 == dm) and d2 > attackradius2:
                offsets.append( (d_row, d_col) )
    
    return set( (center[0] + r, center[1] + c) 
            for r,c in offsets)

def gen_variations(center, d_row, d_col):
    moves = ( (0,0),
              (-1,0),
              (1,0),
              (0,-1),
              (0,1)
            )

    d2 = ( ( (d_row+r1)-(center[0]+r2) )**2 + 
           ( (d_col+c1)-(center[1]+c2) )**2
            for (r1,c1) in moves for (r2,c2) in moves
         )
    return d2

def danger_positions(center, attackradius2,):
    radius = int(sqrt(attackradius2)) + 2
  
    moves = ( (0,0),
              (-1,0),
              (1,0),
              (0,-1),
              (0,1)
            )
    
    for d_row in xrange(-radius + center[0] , radius+center[0]+1):
        for d_col in xrange(-radius +center[1], radius+center[1]+1):
            d2 = ( ( (d_row+r1)-(center[0]+r2) )**2 + 
                   ( (d_col+c1)-(center[1]+c2) )**2
                    for (r1,c1) in moves for (r2,c2) in moves
                 )
            if any(d <= attackradius2 for d in d2):
                yield d_row, d_col

def can_attack(center, attackradius2):
    radius = int(sqrt(attackradius2)) + 2
  
    moves = ( (0,0),
              (-1,0),
              (1,0),
              (0,-1),
              (0,1)
            )
    
    for d_row in xrange(-radius + center[0] , radius+center[0]+1):
        for d_col in xrange(-radius +center[1], radius+center[1]+1):
            d2 = ( ( (d_row)-(center[0]+r2) )**2 + 
                   ( (d_col)-(center[1]+c2) )**2
                    for (r2,c2) in moves
                 )
            if any(d <= attackradius2 for d in d2):
                yield d_row, d_col

