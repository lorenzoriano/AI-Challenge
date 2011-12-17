import random
import distance
import orig_distance

for sgh in xrange(1000):
    rows = random.randint(20,200)
    cols = random.randint(20,200)

    row1 = random.randint(0,rows-1)
    row2 = random.randint(0,rows-1)
    col1 = random.randint(0,cols-1)
    col2 = random.randint(0,cols-1)

    loc1 = (row1, col1)
    loc2 = (row2, col2)
    
    val1 = distance.distance(loc1[0], loc1[1], loc2[0], loc2[1], rows, cols)
    val2 = orig_distance.distance(loc1, loc2, rows, cols)

    assert val1 == val2

print "All fine"
